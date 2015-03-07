from subprocess import Popen, PIPE
from fileio import IO
from encoding import Encoding
from constants import GitCcConstants

import logging


class ClearCaseCommon:

    def __init__(self, cc_dir, include):
        self.logger = logging.getLogger(__name__)
        self.error_logger = logging.getLogger("error")

        self.io = IO()
        self.cc_dir = cc_dir
        self.include = include
        self.encoding = Encoding()

    def describe_directory(self, directory):
        return self.__cc_exec(['describe', '-fmt', '%Nd', directory])

    def list(self):
        ls = ['ls', '-recurse', '-short']
        ls.extend(self.include)
        return self.__cc_exec(ls)

    def link(self, target_file, source_file):
        self.__cc_exec(['ln', '-s', target_file, source_file])

    def list_file_history(self, added):
        return self.__cc_exec(['lshistory', '-fmt', '%o%m|%Nd|%Vn\\n', added], errors=False)

    def fetch_history(self, since):
        """ Fetch history branches and labels (tags) included
        :param since:
        :return:
        """
        lsh = ['lsh', '-fmt', '%o%m|%Nd|%u|%En|%Vn|' + ClearCase.comment_format() + '\\n', '-all'][:]
        if since:
            lsh.extend(['-since', since])
        lsh.extend(self.include)
        return self.__cc_exec(lsh)

    def diff_directory(self, directory):
        return self.__cc_exec(['diff', '-diff_format', '-pred', directory], errors=False)

    def make_label(self, label, file_name, replace=False):
        if replace:
            self.__cc_exec(['mklabel', '-replace', '-nc', label, file_name])
        else:
            self.__cc_exec(['mklabel', '-nc', label, file_name])

    def make_element(self, file_name, directory=False):
        if directory:
            self.__cc_exec(['mkelem', '-nc', '-eltype', 'directory', file_name])
        else:
            self.__cc_exec(['mkelem', '-nc', file_name])

    def move(self, old_file_name, new_file_name):
        self.clear_case.__cc_exec(['mv', '-nc', old_file_name, new_file_name])

    def remove(self, file_name):
        self.clear_case.__cc_exec(['rm', file_name])

    def update(self, directory=None):
        if directory is not None:
            self.__cc_exec(['update', directory], errors=False)
        else:
            self.__cc_exec(['update'], errors=False)

    def check_in(self, message, file_name):
        self.__cc_exec(['ci', '-identical', '-c', message, file_name])

    def check_out(self, file_name):
        self.__cc_exec(['co', '-reserved', '-nc', file_name])

    def undo_check_out(self, file_name):
        self.__cc_exec(['unco', '-rm', file_name])

    def get_file(self, to_file_path, from_file_path):
        self.__cc_exec(['get', '-to', to_file_path, from_file_path],)

    @staticmethod
    def cc_file(file_path, version):
        return '%s@@%s' % (file_path, version)

    def __cc_exec(self, cmd, env=None, decode=True, errors=True, encode=None):
        exe = 'cleartool'
        cwd = self.cc_dir
        cmd.insert(0, exe)
        if self.logger.isEnabledFor(logging.DEBUG):
            f = lambda a: a if not a.count(' ') else '"%s"' % a
            # self.logger.debug('cmd: %s' % cmd)
            self.logger.debug('> ' + ' '.join(map(f, cmd)))
        if GitCcConstants.simulate_cc():
            self.logger.debug('Execute: %s, command %s ' % (exe, cmd))
            return ''
        else:
            pipe = Popen(cmd, cwd=cwd, stdout=PIPE, stderr=PIPE, env=env)
            (stdout, stderr) = pipe.communicate()
            if encode is None:
                encode = self.encoding.encoding()
            if errors and pipe.returncode > 0:
                self.error_logger.warn("Error exec cmd %s: %s" % (cmd, self.encoding.decode_string(encode, stderr + stdout)))
                raise Exception(self.encoding.decode_string(encode, stderr + stdout))
            return stdout if not decode else self.encoding.decode_string(encode, stdout)


class ClearCase(ClearCaseCommon):

    def __init__(self, cc_dir, include):
        ClearCaseCommon.__init__(self, cc_dir, include)

    def rebase(self):
        pass

    def make_activity(self, comment):
        pass

    def remove_activity(self):
        pass

    def commit(self):
        pass

    @staticmethod
    def comment_format():
        return '%Nc'

    def comment(self, comment):
        return comment


class UCM(ClearCaseCommon):

    def __init__(self, cc_dir, include):
        ClearCaseCommon.__init__(self, cc_dir, include)
        self.activities = {}
        self.activity = None

    def rebase(self):
        out = self.__cc_exec(['rebase', '-rec', '-f'])
        if not out.startswith('No rebase needed'):
            self.logger.debug(out)
            self.__cc_exec(['rebase', '-complete'])

    def make_activity(self, comment):
        self.activity = self._activities().get(comment)
        if self.activity:
            self.__cc_exec(['setact', self.activity])
            return
        _comment = self.__cc_exec(['mkact', '-f', '-headline', comment])
        _comment = _comment.split('\n')[0]
        self.activity = _comment[_comment.find('"') + 1:_comment.rfind('"')]
        self._activities()[comment] = self.activity

    def remove_activity(self):
        self.__cc_exec(['setact', '-none'])
        self.__cc_exec(['rmactivity', '-f', self.activity], errors=False)

    def commit(self):
        self.__cc_exec(['setact', '-none'])
        self.__cc_exec(['deliver', '-f'])
        self.__cc_exec(['deliver', '-com', '-f'])

    @staticmethod
    def comment_format():
        return '%[activity]p'

    def comment(self, activity):
        return self.__cc_exec(['lsactivity', '-fmt', '%[headline]p', activity]) if activity else activity

    def _activities(self):
        if not self.activities:
            sep = '@@@'
            for line in self.__cc_exec(['lsactivity', '-fmt', '%[headline]p|%n' + sep]).split(sep):
                if line:
                    line = line.strip().split('|')
                    self.activities[line[0]] = line[1]
        return self.activities
