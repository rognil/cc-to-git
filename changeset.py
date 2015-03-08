"""Change set from ClearCase"""

import os
import stat
from os.path import join, exists, isdir
from fnmatch import fnmatch
from re import search
import logging

from cache import CCFile
from configuration import ConfigParser
from constants import GitCcConstants
from fileio import IO
from conf.users import users, mailSuffix


class ChangeSet:
    """ Group files to change sets so that the commit gets atomic"""

    def __init__(self, cache, clear_case, git, change):

        self.logger = logging.getLogger(__name__)
        self.error_logger = logging.getLogger("error")

        self.cache = cache
        self.clear_case = clear_case
        self.git = git
        self.user = change.user
        self.comment = change.comment
        self.subject = change.subject
        self.version = change.version
        self.date = change.date
        self.change_sets = []
        self.change_sets.append(change)
        self.branch = change.branch

    def append(self, change):
        """
        :param change: A change in ClearCase
        :return:
        """
        self.date = change.date
        self.change_sets.append(change)

    def changes(self):
        return self.change_sets

    def fix_comment(self):
        self.comment = self.clear_case.comment(self.comment)
        self.subject = self.comment.split('\n')[0]

    def commit(self):
        def commit_date(date):
            d = date[:4] + '-' + date[4:6] + '-' + date[6:8] + ' ' + date[9:11] + ':' + date[11:13] + ':' + date[13:15]
            return d

        def user_name(username):
            return str(username).split(' <')[0]

        def user_email(username):
            email = search('<.*@.*>', str(username))
            if email is None:
                return '<%s@%s>' % (username.lower().replace(' ', '.').replace("'", ''), mailSuffix)
            else:
                return email.group(0)

        files = []
        for change in self.change_sets:
            files.append(change.file)
        # Add files to git
        files_added = False
        for change in self.change_sets:
            change.add(files)
            if (change.added_to_git()):
                files_added = True

        self.cache.write()

        if files_added:
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
        else:
            cs = ''
            for change in self.change_sets:
                cs = cs + '|' + change.to_string()

            self.logger.info('Nothing to commit of change set: %s', cs)
            self.error_logger.info('Nothing to commit of change set: %s', cs)

class Change(object):
    def __init__(self, cache, config, clear_case, git, split, comment):
        self.cache = cache
        self.config = config
        self.clear_case = clear_case
        self.git = git
        self.added = False

        self.logger = logging.getLogger(__name__)
        self.error_logger = logging.getLogger("error")

        # mkbranchversion|20110509.151228|proj|dir_a/src/dir_b/file_f|/main/branch_c/0|
        # mkbranchbranch|20110509.151228|proj|dir_a/src/dir_b/file_f|/main/branch_c|
        # mkbranchdirectory version|20110509.142023|proj|dir_a/src/dir_c/file_d|/main/branch_c/0|
        # mkbranchbranch|20110509.142023|proj|dir_a/src/dir_c/file_d|/main/branch_c|
        # checkindirectory version|20110509.112451|proj|dir_h|/main/branch_a/branch_c/1|Added directory "dir_h".
        # checkinversion|20110509.103538|proj|dir_a/src/dir_d/file_c|/main/branch_c/1|Added file "file_c".
        # mkbranchversion|20110509.103434|proj|dir_a/src/dir_d/file_c|/main/branch_c/0|
        # mkbranchbranch|20110509.103434|proj|dir_a/src/dir_d/file_c|/main/branch_c|
        # checkinversion|20110427.173416|proj|dir_e/file_b|/main/branch_b/branch_c/2|
        # checkinversion|20110427.170355|proj|dir_a/src/dir_d/file_a|/main/branch_c/1|
        # mkbranchversion|20110427.170117|proj|dir_a/src/dir_d/file_a|/main/branch_c/0|
        # mkbranchbranch|20110427.170117|proj|dir_a/src/dir_d/file_a|/main/branch_c|

        self.date = split[1]
        self.user = split[2]
        self.file = split[3]
        if self.file.startswith('/'):
            self.file = self.file[len(self.config.cc_dir())+1:]
        self.version = split[4]
        self.branch = Change.compile_branch(self.version)
        self.comment = comment
        self.subject = comment.split('\n')[0]

    @staticmethod
    def compile_branch(version):
        # first = version.rfind(GitCcConstants.version_delimiter())
        last = version.rfind(GitCcConstants.version_delimiter())
        b = version[1:last].replace(GitCcConstants.version_delimiter(), '_')
        return b if not b == 'main' else 'master'

    def added_to_git(self):
        return self.added

    def to_string(self):
        return "User=%s, Version=%s, File=%s, branch %s" % (self.user, self.version, self.file, self.branch)

    def add(self, files):
        self._add(self.file, self.version)

    def _add(self, file_path, version):
        """ Add file to Git """

        # Check if file is on this branch
        if not self.cache.check_and_update_path_in_current_branch(CCFile(file_path, version, self.config.cc_dir())):
            return

        if [e for e in self.config.exclude() if fnmatch(file_path, e)]:
            return

        to_file_path = self.config.path(join(ConfigParser.git_path(), file_path))
        IO.make_directories(to_file_path)
        IO.remove_file(to_file_path)
        try:
            # Checkout ClearCase file
            self.clear_case.get_file(to_file_path,
                                     Change.prepare_cc_file(join(ConfigParser.cc_dir(), file_path), version))
        except Exception:
            if len(file_path) < 200:
                self.error_logger.warn('Caught error adding %s' % file_path)
                raise
            self.logger.debug("Ignoring %s as it may be related to https://github.com/charleso/git-cc/issues/9" %
                              file_path)
        if not exists(to_file_path):
            self.git.check_out_file(to_file_path)
        else:
            os.chmod(to_file_path, os.stat(to_file_path).st_mode | stat.S_IWRITE)
        self.logger.debug("Add file %s" % file_path)
        self.git.force_add(file_path)
        self.added = True

    @staticmethod
    def prepare_cc_file(file_path, version):
        return '%s@@%s' % (file_path, version)

    def filter_branches(self, config, version, branch, complete=False):
        version = version.split(GitCcConstants.version_delimiter())
        self.logger.debug('Version: %s, %s', version, complete)
        version.pop()
        self.logger.debug('Version: %s', version)
        version = version[-1]
        branches = config.branches()
        if complete and branches is not None and config.extra_branches() is not None:
            branches.extend(config.extra_branches())
        for b in branches:
            if fnmatch(version, b):
                self.logger.debug('Branch match: %s, %s', version, complete)
                if b == 'main':
                    return 'master'
                return branch
        self.logger.debug('Branch skip: %s, %s', version, complete)
        return None


class Uncatalogued(Change):

    def __init__(self, cache, config, clear_case, git, split, comment):
        Change.__init__(self, cache, config, clear_case, git, split, comment)

    def get_file(self, line):
        return join(self.file, line[2:max(line.find('  '), line.find(GitCcConstants.file_separator() + ' '))])

    def add(self, files):
        directory = self.config.path(Change.prepare_cc_file(self.file, self.version))
        diff = self.clear_case.diff_directory(directory)

        for line in diff.split('\n'):
            self.logger.info("UC-%s, Parsing line: '%s'" % (self.branch, line))
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
                self.logger.info("Actual version '%s'" % (str(actual_versions)))

                versions = self.check_in_versions(actual_versions)
                if not versions:
                    versions = self.empty_file_versions(actual_versions)
                    self.logger.info("No proper versions of '%s' file. Check if it is empty. V: %s, Actual V: %s" %
                                     (added, versions, actual_versions))
                if not versions:
                    self.logger.warn("It appears that you may be missing a branch "
                                     "in the includes section of your gitcc config for file '%s'. Actual V: %s"
                                     % (added, actual_versions))
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
            self.logger.debug("Kind '%s', versions '%s'" % (kind, s))

            return s[0] == kind and self.filter_branches(self.config, s[2], self.branch, True) is not None

        return self.filter_versions(versions, f)

    @staticmethod
    def filter_versions(versions, handler):
        return list(filter(handler, versions))

    @staticmethod
    def parse_history(history_arr):
        return list(map(lambda x: x.split('|'), history_arr))


class Branch(Change):
    def __init__(self, cache, config, clear_case, git, split, comment):
        Change.__init__(self, cache, config, clear_case, git, split, comment)

    def add(self, files):
        self.make_branch()

    def make_branch(self):
        for branch in self.git.branches():
            if branch.startswith('*'):
                branch = branch[2:]
            if branch == self.branch:
                return
        current = self.git.current_branch()
        self.git.check_out(self.git.default_branch())
        self.git.branch(self.branch)
        self.git.check_out(current)


class Tag(Change):

    def __init__(self, cache, config, clear_case, git, split, comment):
        Change.__init__(self, cache, config, clear_case, git, split, comment)

    def add(self, files):
        self.make_tag()

    def make_tag(self):
        for tag in self.git.tags():
            if tag.startswith('*'):
                tag = tag[2:]
            if tag == self.branch:
                return
        current = self.git.current_branch()
        self.git.check_out(self.git.default_branch())
        self.git.tag(self.file)
        self.git.check_out(current)
