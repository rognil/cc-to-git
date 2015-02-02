from os.path import join, exists


from clearcase import UCM, ClearCase
from git import Git

from constants import GitCcConstants
from configuration import ConfigParser

import logging
logger = logging.getLogger(__name__)


class Cache(object):
    config = ConfigParser()

    def __init__(self, dir):
        self.map = {}
        self.clear_case = (UCM if Cache.config.core('type') == 'UCM' else ClearCase)()
        self.constants = GitCcConstants()
        self.git = Git()
        self.file_name = self.constants.gitcc_file()
        self.dir = dir
        self.empty = Version('/main/0')

    def start(self):
        f = join(self.dir, self.file_name)
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
            self.update(CCFile2(line))

    def update(self, path):
        is_child = self.map.get(path.file_name, self.empty).child(path.version)
        if is_child:
            self.map[path.file_name] = path.version
        return is_child or path.version.endswith(Cache.config.branches()[0])

    def remove(self, filename):
        if filename in self.map:
            del self.map[filename]

    def write(self):
        lines = []
        keys = self.map.keys()
        keys = sorted(keys)
        for file_name in keys:
            lines.append(file_name + '@@' + self.map[file_name].full)
        f = open(join(self.dir, self.file_name), 'w')
        try:
            f.write('\n'.join(lines))
            f.write('\n')
        except UnicodeEncodeError:
            print 'Lines: ' + '\n'.join(lines)
        finally:
            f.close()
        self.git.add(self.file_name)

    def list(self):
        values = []
        for file_name, version in self.map.items():
            values.append(CCFile(file_name, version.full))
        return values

    def contains(self, path):
        return self.map.get(path.file_name, self.empty).full == path.version.full


class NoCache(object):
    def start(self):
        pass

    def write(self):
        pass

    def update(self, path):
        return True

    def remove(self, file_name):
        pass


class CCFile(object):
    def __init__(self, file_name, version):
        if file_name.startswith('./') or file_name.startswith('.\\'):
            file_name = file_name[2:]
        self.file_name = file_name
        self.version = Version(version)


class CCFile2(CCFile):
    def __init__(self, line):
        [file_name, version] = line.rsplit('@@', 1)
        super(CCFile2, self).__init__(file_name, version)


class Version(object):
    def __init__(self, version):
        self.full = version.replace('\\', '/')
        self.version = '/'.join(self.full.split('/')[0:-1])

    def child(self, version):
        return version.version.startswith(self.version)

    def endswith(self, version):
        return self.version.endswith('/' + version)
