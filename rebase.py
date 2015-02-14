"""Rebase from Clearcase"""

from os.path import join, exists, isdir
import os
import stat
from users import users, mailSuffix
from fnmatch import fnmatch
from re import search

from clearcase import ClearCase
from cache import Cache, CCFile, NoCache
from git import Git
from fileio import IO
from configuration import ConfigParser
from constants import GitCcConstants
from encoding import Encoding

import logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error")

"""
Things remaining:
1. Renames with no content change. Tricky.
"""


DELIM = '|'

ARGS = {
    'stash': 'Wraps the rebase in a stash to avoid file changes being lost',
    'dry_run': 'Prints a list of changesets to be imported',
    'lshistory': 'Prints the raw output of lshistory to be cached for load',
    'load': 'Loads the contents of a previously saved lshistory file',
}


def main(stash=False, dry_run=False, lshistory=False, load=None):
    config = ConfigParser()
    git = Git()
    clear_case = ClearCase()
    io = IO()

    if config.core('cache', True) == 'False':
        cache = NoCache()
    else:
        cache = Cache(config.git_dir())

    config.validate_cc()
    if not (stash or dry_run or lshistory):
        git.check_pristine()

    clear_case.update()

    since = git.since_date(config.get('since'))
    cache.start()
    if load:
        history = open(load, 'r').read().decode(Encoding.encoding())
    else:
        clear_case.rebase()
        history = clear_case.fetch_history(since)
        io.write(join(config.git_dir(), '.git', 'lshistory.bak'), history.encode(Encoding.encoding()))
        history = open(join(config.git_dir(), '.git', 'lshistory.bak'), 'r').read().decode(Encoding.encoding())

    if lshistory:
        print(history)
    else:
        change_set = parse_history(cache, config, clear_case, git, history)
        change_set = reversed(change_set)
        change_set = merge_history(cache, clear_case, git, change_set)
        if dry_run:
            return print_groups(change_set)
        if not len(change_set):
            return
        git.stash(lambda: do_commit(change_set, git), stash)


def do_commit(cs, git):
    branch = git.current_branch()
    if branch:
        git.check_out(git.cc_tag)

    try:
        commit(cs)
    finally:
        logger.debug("On branch: %s" % branch)
        if branch:
            git.rebase(git.ci_tag(), git.cc_tag())
            git.rebase(git.cc_tag(), branch)
        else:
            logger.debug("On branch: %s" % branch)
            git.branch(git.cc_tag())
        git.tag(git.ci_tag(), git.cc_tag())


def filter_branches(config, version, complete=False):
    version = version.split(GitCcConstants.file_separator())
    version.pop()
    version = version[-1]
    branches = config.branches()
    logger.debug('Branches: %s', branches)
    if complete:
        branches.extend(config.extra_branches())
    for branch in branches:
        if fnmatch(version, branch):
            logger.debug('Branch match: %s, %s', version, complete)
            return True
    logger.debug('Branch skip: %s, %s', version, complete)
    return False


def parse_history(cache, config, clear_case, git, lines):

    types = {
        'checkinversion': ChangeSet,
        'checkindirectory version': Uncataloged,
    }

    change_sets = []

    def add(_cache, _config, _clear_case, _git, _split, _comment):
        if not _split:
            return
        cstype = _split[0]
        if cstype in types:
            cs = types[cstype](_cache, _config, _clear_case, _git, _split, _comment)
            try:
                logger.debug('Parse history %s', cs.version)
                if filter_branches(_config, cs.version):
                    change_sets.append(cs)
            except Exception as e:
                error_logger.warn('Bad line %s, %s' % (_split, _comment))
                raise

    last = None
    comment = None
    for line in lines.splitlines():
        split = line.split(DELIM)
        if len(split) < 6 and last:
            # Cope with comments with '|' character in them
            comment += "\n" + DELIM.join(split)
        else:
            add(cache, config, clear_case, git, last, comment)
            comment = DELIM.join(split[5:])
            last = split
    add(cache, config, clear_case, git, last, comment)
    return change_sets


def merge_history(cache, clear_case, git, change_sets):
    last = None
    groups = []

    def same(a, b):
        return a.subject == b.subject and a.user == b.user

    for change in change_sets:
        if last and same(last, change):
            last.append(change)
        else:
            last = Group(cache, clear_case, git, change)
            groups.append(last)
    for group in groups:
        group.fix_comment()
    return groups


def commit(change_set):
    for cs in change_set:
        cs.commit()


def print_groups(groups):
    for cs in groups:
        print('%s "%s"' % (cs.user, cs.subject))
        for file in cs.files:
            print("  %s" % file.file)


class Group:
    def __init__(self, cache, clear_case, git, cs):
        self.cache = cache
        self.clear_case = clear_case
        self.git = git
        self.user = cs.user
        self.comment = cs.comment
        self.subject = cs.subject
        self.files = []
        self.date = cs.date
        self.files.append(cs)

    def append(self, cs):
        self.date = cs.date
        self.files.append(cs)

    def fix_comment(self):
        self.comment = self.clear_case.comment(self.comment)
        self.subject = self.comment.split('\n')[0]

    def commit(self):
        def commit_date(date):
            return date[:4] + '-' + date[4:6] + '-' + date[6:8] + ' ' + date[9:11] + ':' + date[11:13] + ':' + date[13:15]

        def user_name(user):
            return str(user).split(' <')[0]

        def user_email(user):
            email = search('<.*@.*>', str(user))
            if email is None:
                return '<%s@%s>' % (user.lower().replace(' ', '.').replace("'", ''), mailSuffix)
            else:
                return email.group(0)

        files = []
        for file_name in self.files:
            files.append(file_name.file)
        for file_name in self.files:
            file_name.add(files)
        self.cache.write()
        env = os.environ
        user = users.get(self.user, self.user)
        env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = str(commit_date(self.date))
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = user_name(user)
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = str(user_email(user))
        comment = self.comment if self.comment.strip() != "" else "<empty message>"
        try:
            logger.debug('Comment: %s' % comment)
            self.git.commit(comment, env=env)

        except Exception as e:
            error_logger.error('Error: %s' % e)
            if search('nothing( added)? to commit', e.args[0]) is None:
                raise


def cc_file(file, version):
    return '%s@@%s' % (file, version)


class ChangeSet(object):
    def __init__(self, cache, config, clear_case, git, split, comment):
        self.cache = cache
        self.config = config
        self.clear_case = clear_case
        self.git = git

        self.date = split[1]
        self.user = split[2]
        self.file = split[3]
        self.version = split[4]
        self.comment = comment
        self.subject = comment.split('\n')[0]

    def add(self, files):
        self._add(self.file, self.version)

    def _add(self, file_path, version):
        if not self.cache.update(CCFile(file_path, version)):
            return
        if [e for e in self.config.exclude() if fnmatch(file_path, e)]:
            return
        to_file_path = self.config.path(join(ConfigParser.git_dir(), file_path))
        IO.make_directories(to_file_path)
        IO.remove_file(to_file_path)
        try:
            self.clear_case.get_file(to_file_path, cc_file(file_path, version))
        except:
            if len(file_path) < 200:
                error_logger.warn('Caught error adding %s' % file_path)
                raise
            logger.debug("Ignoring %s as it may be related to https://github.com/charleso/git-cc/issues/9" % file_path)
        if not exists(to_file_path):
            self.git.check_out_file(to_file_path)
        else:
            os.chmod(to_file_path, os.stat(to_file_path).st_mode | stat.S_IWRITE)
        self.git.force_add(file_path)


class Uncataloged(ChangeSet):

    def __init__(self, cache, config, clear_case, git, split, comment):
        ChangeSet.__init__(self, cache, config, clear_case, git, split, comment)

    def get_file(self, line):
        return join(self.file, line[2:max(line.find('  '), line.find(GitCcConstants.file_separator() + ' '))])

    def add(self, files):
        directory = self.config.path(cc_file(self.file, self.version))
        diff = self.clear_case.diff_directory(directory)

        for line in diff.split('\n'):
            sym = line.find(' -> ')
            if sym >= 0:
                continue
            if line.startswith('<'):
                self.git.remove(self.get_file(line))
                self.cache.remove(self.get_file(line))
            elif line.startswith('>'):
                added = self.get_file(line)
                cc_added = join(ConfigParser.cc_dir(), added)
                if not exists(cc_added) or isdir(cc_added) or added in files:
                    continue
                history = self.clear_case.list_file_history(added)
                if not history:
                    continue
                history = filter(None, history.split('\n'))
                all_versions = self.parse_history(history)

                date = self.clear_case.describe_directory(directory)
                actual_versions = self.filter_versions(all_versions, lambda x: x[1] < date)

                versions = self.check_in_versions(actual_versions)
                if not versions:
                    print("No proper versions of '%s' file. Check if it is empty." % added)
                    versions = self.empty_file_versions(actual_versions)
                if not versions:
                    print("It appears that you may be missing a branch "
                          "in the includes section of your gitcc config for file '%s'." % added)
                    continue
                self._add(added, versions[0][2].strip())

    def check_in_versions(self, versions):
        return self.filter_versions_by_type(versions, 'checkinversion')

    def empty_file_versions(self, versions):
        return self.versions_with_branch(versions) or self.versions_without_branch(versions)

    def versions_with_branch(self, versions):
        if len(versions) != 5:
            return False
        return self.filter_versions_by_type(versions, 'mkbranchversion')

    def versions_without_branch(self, versions):
        if len(versions) != 3:
            return False
        return self.filter_versions(versions, lambda x: x[0] == 'mkelemversion')

    def filter_versions_by_type(self, versions, kind):
        def f(s):
            return s[0] == kind and filter_branches(self.config, s[2], True)

        return self.filter_versions(versions, f)

    @staticmethod
    def filter_versions(versions, handler):
        return list(filter(handler, versions))

    @staticmethod
    def parse_history(history_arr):
        return list(map(lambda x: x.split('|'), history_arr))
