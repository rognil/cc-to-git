from os.path import join, exists

from constants import GitCcConstants

from clearcase import UCM, ClearCase
from git import Git

import logging


class Cache(object):

    def __init__(self, base_dir, branches, cc_type, cc_dir, include,):
        self.logger = logging.getLogger(__name__)
        self.error_logger = logging.getLogger("error")
        self.branches = branches
        self.map = {}
        self.cc_dir = cc_dir
        self.clear_case = (UCM if cc_type == 'UCM' else ClearCase)(cc_dir, include)
        self.constants = GitCcConstants()
        self.git = Git()
        self.dir = base_dir
        self.cache_file_name = join(base_dir, self.constants.conf_dir(), self.constants.cc_to_git_file())
        self.empty = CCBranch('/main/0')

    def start(self):
        f = join(self.dir, self.cache_file_name)
        if exists(f):
            self.load(f)
        else:
            self.initial()

    def load(self, file_path):
        f = open(file_path, 'r')
        try:
            self.read(f.read())
        finally:
            f.close()

    def initial(self):
        ls = self.clear_case.list()
        self.read(ls)

    def read(self, lines):
        for line in lines.splitlines():
            if line.find('@@') < 0:
                continue
            self.check_and_update_path_in_current_branch(CCFile2(line, self.cc_dir))

    def check_and_update_path_in_current_branch(self, path):
        is_child = self.map.get(path.file_name, self.empty).child(path.version)
        if is_child:
            self.map[path.file_name] = path.version
        return is_child or path.version.endswith(self.branches[0])

    def remove(self, filename):
        if filename in self.map:
            del self.map[filename]

    def write(self):
        lines = []
        keys = self.map.keys()
        keys = sorted(keys)
        for file_name in keys:
            lines.append(file_name + '@@' + self.map[file_name].full)
        f = open(join(self.dir, self.cache_file_name), 'w')
        try:
            f.write('\n'.join(lines))
            f.write('\n')
        except UnicodeEncodeError:
            self.error_logger.warn('Error on lines: %s' % '\n'.join(lines))
        finally:
            f.close()

    def list(self):
        values = []
        for file_name, version in self.map.items():
            values.append(CCFile(file_name, version.full, self.cc_dir))
        return values

    def contains(self, path):
        return self.map.get(path.file_name, self.empty).full == path.version.full


class NoCache(object):
    def start(self):
        pass

    def write(self):
        pass

    def check_and_update_path_in_current_branch(self, path):
        return True

    def remove(self, file_name):
        pass


class CCFile(object):
    def __init__(self, file_name, version, cc_dir):
        self.logger = logging.getLogger(__name__)
        if file_name.startswith('/'):
            file_name = file_name[len(cc_dir)+1:]
        elif file_name.startswith('./') or file_name.startswith('.\\'):
            file_name = file_name[2:]
        self.file_name = file_name
        self.version = CCBranch(version)
        self.logger.debug("File: %s, Version: %s", self.file_name, self.version.version)


class CCFile2(CCFile):
    def __init__(self, line, cc_dir):
        [file_name, version] = line.rsplit('@@', 1)
        super(CCFile2, self).__init__(file_name, version, cc_dir)


class CCBranch(object):
    """ The branch to which a change set belongs """

    def __init__(self, version):
        self.full = version.replace('\\', '/')
        self.version = '/'.join(self.full.split('/')[0:-1])

    def child(self, version):
        return version.version == self.version

    def endswith(self, version):
        return self.version.endswith('/' + version)
