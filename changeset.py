"""Change set from ClearCase"""

import os
import stat

from os.path import join, exists, isdir
from fnmatch import fnmatch
from re import search

from cache import CCFile
from configuration import ConfigParser
from constants import GitCcConstants
from fileio import IO
from users import users, mailSuffix

import logging


class ChangeSet(object):
    def __init__(self, cache, config, clear_case, git, split, comment):
        self.cache = cache
        self.config = config
        self.clear_case = clear_case
        self.git = git

        self.logger = logging.getLogger(__name__)
        self.error_logger = logging.getLogger("error")

        self.date = split[1]
        self.user = split[2]
        self.file = split[3]
        self.version = split[4]
        self.branch = None
        self.comment = comment
        self.subject = comment.split('\n')[0]

    def to_string(self):
        return "User=%s, Version=%s, File=%s, branch %s" % (self.user, self.version, self.file, self.branch)

    def add(self, files):
        self._add(self.file, self.version)

    def _add(self, file_path, version):
        """ Add file to Git """

        # Check if file is on this branch
        if not self.cache.check_and_update_path_in_current_branch(CCFile(file_path, version)):
            return
        if [e for e in self.config.exclude() if fnmatch(file_path, e)]:
            return
        to_file_path = self.config.path(join(ConfigParser.git_dir(), file_path))
        IO.make_directories(to_file_path)
        IO.remove_file(to_file_path)
        try:
            # Checkout ClearCase file
            self.clear_case.get_file(to_file_path, ChangeSet.prepare_cc_file(file_path, version))
        except:
            if len(file_path) < 200:
                self.error_logger.warn('Caught error adding %s' % file_path)
                raise
            self.logger.debug("Ignoring %s as it may be related to https://github.com/charleso/git-cc/issues/9" % file_path)
        if not exists(to_file_path):
            self.git.check_out_file(to_file_path)
        else:
            os.chmod(to_file_path, os.stat(to_file_path).st_mode | stat.S_IWRITE)
        self.logger.debug("Add file %s" % file_path)
        self.git.force_add(file_path)

    @staticmethod
    def prepare_cc_file(file_path, version):
        return '%s@@%s' % (file_path, version)

    def filter_branches(self, config, version, complete=False):
        version = version.split(GitCcConstants.file_separator())
        version.pop()
        version = version[-1]
        branches = config.branches()
        self.logger.debug('Branches: %s', branches)
        if complete:
            branches.extend(config.extra_branches())
        for branch in branches:
            if fnmatch(version, branch):
                self.logger.debug('Branch match: %s, %s', version, complete)
                if branch == 'main':
                    return 'master'
                return branch
        self.logger.debug('Branch skip: %s, %s', version, complete)
        return None


class Uncataloged(ChangeSet):

    def __init__(self, cache, config, clear_case, git, split, comment):
        ChangeSet.__init__(self, cache, config, clear_case, git, split, comment)

    def get_file(self, line):
        return join(self.file, line[2:max(line.find('  '), line.find(GitCcConstants.file_separator() + ' '))])

    def add(self, files):
        directory = self.config.path(ChangeSet.prepare_cc_file(self.file, self.version))
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
            return s[0] == kind and self.filter_branches(self.config, s[2], True) is not None

        return self.filter_versions(versions, f)

    @staticmethod
    def filter_versions(versions, handler):
        return list(filter(handler, versions))

    @staticmethod
    def parse_history(history_arr):
        return list(map(lambda x: x.split('|'), history_arr))


class Group:
    def __init__(self, cache, clear_case, git, cs):

        self.logger = logging.getLogger(__name__)
        self.error_logger = logging.getLogger("error")

        self.cache = cache
        self.clear_case = clear_case
        self.git = git
        self.user = cs.user
        self.comment = cs.comment
        self.subject = cs.subject
        self.date = cs.date
        self.cs_files = []
        self.cs_files.append(cs)
        self.branch = cs.branch

    def append(self, cs):
        self.date = cs.date
        self.cs_files.append(cs)

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
        for cs in self.cs_files:
            files.append(cs.file)
        # Add files to git
        for cs in self.cs_files:
            cs.add(files)
        self.cache.write()
        env = os.environ
        user = users.get(self.user, self.user)
        env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = str(commit_date(self.date))
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = user_name(user)
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = str(user_email(user))
        comment = self.comment if self.comment.strip() != "" else "<empty message>"

        # Commit files to Git
        try:
            self.git.commit(comment, env=env)

        except Exception as e:
            self.error_logger.error('Error: %s' % e)
            if search('nothing( added)? to commit', e.args[0]) is None:
                raise
