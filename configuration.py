__author__ = 'rognilse'

from distutils import __version__
import os
import sys
from os.path import join, exists
from threading import Lock

v30 = __version__.find("3.") == 0
if v30:
    from configparser import SafeConfigParser
else:
    from ConfigParser import SafeConfigParser

import constants
from git import Git

from common import fail

import logging
logger = logging.getLogger(__name__)

class ConfigParser():

    __git = Git()

    if constants.GitCcConstants.cygwin():
        __git_dir = os.popen('cygpath %s "%s"' % ('-m', __git.dir())).readlines()[0].strip()
    else:
        __git_dir = __git.dir()

    __core = 'core'
    __cc_cfg = 'clearcase'

    __debug = constants.GitCcConstants().debug()

    __lock = Lock()
    __initialized = False

    __cc_dir = None
    __parser = None

    def __init__(self, mode=None):
        ConfigParser.__lock.acquire()
        self.section = ConfigParser.__git.current_branch() or 'master'
        if ConfigParser.__git_dir is None:
            ConfigParser.__git_dir = ConfigParser.path(ConfigParser.__git.dir())
            if not exists(join(ConfigParser.__git_dir, '.git')):
                fail("fatal: Not a git repository (or any of the parent directories): .git")
        if not ConfigParser.__initialized:
            ConfigParser.__parser = SafeConfigParser();
        if ConfigParser.__cc_dir is None:
            ConfigParser.__cc_dir = self.path(self.get(ConfigParser.__cc_cfg))
        if not ConfigParser.__debug:
            ConfigParser.__debug = ConfigParser.core('debug', False)
        self.file = join(ConfigParser.__git_dir, '.git', 'gitcc')
        if not ConfigParser.__initialized:
            self.read()
            if ConfigParser.__cc_dir is None:
                ConfigParser.__cc_dir = self.path(self.get(ConfigParser.__cc_cfg))
            if mode == 'init':
                ConfigParser.__parser.add_section(self.section)
            if not ConfigParser.__cc_dir and (len(sys.argv) > 1 and not "init" == sys.argv[1]):
                fail("fatal: Configuration is faulty using branch '%s'" % self.section)

            print '\n'
            print 'GitCC: ', self.file
            print 'Git Dir: ', ConfigParser.__git_dir
            print 'CC Dir: ', ConfigParser.__cc_dir
            print 'Section: ', self.section
            print 'Branches: ', self.branches()
            ConfigParser.__initialized = True
        ConfigParser.__lock.release()

    def set_section(self, name, value):
        logger.debug('Section %s, name %s, value %s' % (self.section, name, value))
        ConfigParser.__parser.set(self.section, name, value)

    def section(self):
        return self.section

    def validate_cc(self):
        if not ConfigParser.__cc_dir:
            fail("No 'clearcase' variable found for branch '%s'" % self.section)

    def read(self):
        ConfigParser.__parser.read(self.file)

    def write(self):
        ConfigParser.__parser.write(open(self.file, 'w'))

    def core(self, name, *args):
        return self._get(ConfigParser.__core, name, *args)

    def get(self, name, *args):
        return self._get(self.section, name, *args)

    def list(self, name, default=None):
        return self.get(name, default).split('|')

    def branches(self):
        return self.list('branches', 'main')

    def extra_branches(self):
        return self.list('_branches', 'main')

    def include(self):
        return self.core('include', '.').split('|')

    def exclude(self):
        return self.core('exclude', '.').split('|')

    @staticmethod
    def _get(section, name, default=None):
        if not ConfigParser.__parser.has_option(section, name):
            return default
        return ConfigParser.__parser.get(section, name)

    @staticmethod
    def cc_cfg():
        return ConfigParser.__cc_cfg

    @staticmethod
    def cc_dir():
        return ConfigParser.__cc_dir

    @staticmethod
    def git_dir():
        return ConfigParser.__git_dir

    @staticmethod
    def debug():
        return ConfigParser.__debug

    @staticmethod
    def path(path, args='-m'):
        if constants.GitCcConstants.cygwin():
            return os.popen('cygpath %s "%s"' % (args, path)).readlines()[0].strip()
        else:
            return path
