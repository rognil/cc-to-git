from subprocess import Popen, PIPE
from os.path import join, exists, abspath, dirname
from datetime import datetime, timedelta

from common import fail
from encoding import Encoding
from constants import GitCcConstants
from threading import Lock

import logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error")


class Git:
    LOG_FORMAT = '%H%x01%B'

    __lock = Lock()
    __initialized = False

    __cc_tag = None
    __ci_tag = None
    __git_dir = None

    def __init__(self, dir='.'):
        Git.__lock.acquire()
        self.encoding = Encoding()
        if not Git.__initialized:
            Git.__git_dir = dir
            branch = self.current_branch() or 'master'
            if branch.endswith('_cc'):
                Git.__cc_tag = branch
                Git.__ci_tag = branch.replace('_cc', '_ci')
            elif branch.endswith('_ci'):
                Git.__cc_tag = branch.replace('_ci', '_cc')
                Git.__ci_tag = branch
            else:
                Git.__cc_tag = branch + '_cc'
                Git.__ci_tag = branch + '_ci'
            Git.__initialized = True
        Git.__lock.release()

    @staticmethod
    def ci_tag():
        return Git.__ci_tag

    @staticmethod
    def cc_tag():
        return Git.__cc_tag

    def add(self, file_path):
        self.__git_exec(['add', file_path])

    def force_add(self, directory):
        self.__git_exec(['add', '-f', directory], errors=False)

    def config(self, key, value):
        self.__git_exec(['config', key, value])

    def check_out_file(self, to_file):
            self.__git_exec(['checkout', 'HEAD', to_file])

    def commit(self, message, env=None):
        if env is not None:
            self.__git_exec(['commit', '-m', message.encode(Encoding.encoding())], env=env)
        else:
            self.__git_exec(['commit', '-m', message])

    def commit_empty(self, message):
        self.__git_exec(['commit', '--allow-empty', '-m', message])

    def tag(self, tag, identity="HEAD"):
        self.__git_exec(['tag', '-f', tag, identity])

    def check_out(self, tag):
        self.__git_exec(['checkout', tag])

    def rebase(self, tag_old, tag_new):
        self.__git_exec(['rebase', tag_old, tag_new])

    def branch(self, tag, commit=None):
        if commit is not None:
            self.__git_exec(['branch', '-f', tag, commit])
        else:
            self.__git_exec(['branch', '-f', tag])

    def merge_base(self, tag=None, branch='HEAD'):
        return self.git.__git_exec(['merge-base', tag, branch]).strip()

    def reset(self, tag=None):
        self.__git_exec(['reset', '--hard', tag or Git.__cc_tag])

    def remove(self, file_path):
        self.__git_exec(['rm', '-r', file_path], errors=False)

    def stash(self, f, stash):
        if stash:
            self.__git_exec(['stash'])
        f()
        if stash:
            self.__git_exec(['stash', 'pop'])

    def current_branch(self):
        for branch in self.__git_exec(['branch']).split('\n'):
            if branch.startswith('*'):
                branch = branch[2:]
                if branch == '(no branch)':
                    fail("Why aren't you on a branch?")
                if branch == 'master':
                    return ""
                logger.debug("Current branch: ", branch)
                return branch
        return ""

    def blob(self, sha, blob_file):
        return self.__git_exec(['ls-tree', '-z', sha, blob_file]).split(' ')[2].split('\t')[0]

    def hash_object(self, file_path):
        return self.__git_exec(['hash-object', file_path])[0:-1]

    def cat_blob_file(self, identity, file_name):
        return self.git.__git_exec(['cat-file', 'blob', self.blob(identity, file_name)], decode=False)

    def check_pristine(self):
        if len(self.__git_exec(['ls-files', '--modified']).splitlines()) > 0:
            fail('There are uncommitted files in your git directory')

    def since_date(self, default):
        try:
            date = self.__git_exec(['log', '-n', '1', '--pretty=format:%ai', '%s' % Git.cc_tag()])
            date = date[:19]
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            date = date + timedelta(seconds=1)
            return datetime.strftime(date, '%d-%b-%Y.%H:%M:%S')
        except Exception:
            return default

    def diff(self, identity, initial):
        cmd = ['diff', '--name-status', '-M', '-z', '--ignore-submodules', '%s^..%s' % (identity, identity)]
        if initial:
            cmd = cmd[:-1]
            cmd[0] = 'show'
            cmd.extend(['--pretty=format:', identity])
        return self.__git_exec(cmd)

    def list_tree(self, identity, activity):
        cmd = ['ls-tree', '-z', identity, '--', activity]
        return self.__git_exec(cmd)

    def log(self, complete=False, initial=False):
        # %H%x01%B      -       identity, delimiter, message
        # fb7276c7a745f3138b851c99a3f40a573212acad \xe2 Empty commit
        log = ['log', '-z', '--reverse', '--pretty=format:' + Git.LOG_FORMAT]
        if not complete:
            log.append('--first-parent')
        if not initial:
            log.append(Git.ci_tag() + '..')
        return self.__git_exec(log)

    @staticmethod
    def dir():
        def find_dir(dir):
            if not exists(dir) or dirname(dir) == dir:
                return '.'
            if exists(join(dir, '.git')):
                return dir
            return find_dir(dirname(dir))
        return find_dir(abspath('.'))

    def __git_exec(self, cmd, env=None, decode=True, errors=True):
        exe='git'
        cwd=self.__git_dir
        encode=Encoding.encoding()

        cmd.insert(0, exe)
        if logger.level == logging.DEBUG:
            f = lambda a: a if not a.count(' ') else '"%s"' % a
            logger.debug('Command: %s' % cmd)
            logger.debug('> ' + ' '.join(map(f, cmd)))
        if GitCcConstants.simulate_git():
            logger.debug('Execute: %s, command %s ' % (exe, cmd))
            return ''
        else:
            if GitCcConstants.debug():
                logger.debug('Git cmd: %s', cmd)
            pipe = Popen(cmd, cwd=cwd, stdout=PIPE, stderr=PIPE, env=env)
            (stdout, stderr) = pipe.communicate()
            if encode is None:
                encode = self.encoding.encoding()
            if errors and pipe.returncode > 0:
                error_logger.warn("Error executing cmd %s: %s" % (cmd, self.encoding.decode_string(encode, stderr + stdout)))
                raise Exception(self.encoding.decode_string(encode, stderr + stdout))
            return stdout if not decode else self.encoding.decode_string(encode, stdout)

