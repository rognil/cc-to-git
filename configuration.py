__author__ = 'rognilse'

from distutils import __version__
import os
import sys
from os.path import join, basename
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

    __base_dir = os.getcwd()

    __git = Git('.', 'master')

    __git_dir = 'git'

    __git_repository_dir = join(__git_dir, constants.GitCcConstants.git_repository_name())

    __git_path = './git'

    __core_section = 'git_cc_core'

    # /ClearCase/project
    __cc_cfg = 'clearcase'

    # /home/login/git-cc/gitproject
    __git_cfg = 'git'

    # main|branch1|branch2|branch3
    __branches_cfg = 'branches'

    __extra_branches_cfg = '_branches'

    # %Y-%m-%d %H:%M:%S - 2014-03-23 04:03:01
    __since_cfg = 'since'

    __include_cfg = 'include'

    __exclude_cfg = 'exclude'

    __conf_file = 'conf/gitcc.conf'
    __debug = constants.GitCcConstants().debug()

    __lock = Lock()
    __initialized = False

    __cc_path = None
    __parser = None

    def __init__(self):
        self.section = self.__core_section

    def init(self, base_dir=os.getcwd(), mode=None, git_dir=None):
        ConfigParser.__lock.acquire()
        if not ConfigParser.__initialized:
            ConfigParser.__base_dir = base_dir
            ConfigParser.__parser = SafeConfigParser();
            ConfigParser.__conf_file = join(ConfigParser.__base_dir, constants.GitCcConstants.conf_dir(), constants.GitCcConstants.conf_file())
            self.read()
            ConfigParser.__git_path = self.path(self.core(ConfigParser.__git_cfg))
            if ConfigParser.__git_path is None or ConfigParser.__git_path== '':
                if git_dir is None:
                    ConfigParser.__git_path = join(base_dir, ConfigParser.git_cfg())
                else:
                    ConfigParser.__git_path = join(base_dir, git_dir)
            if git_dir is None:
                ConfigParser.__git_dir = basename(ConfigParser.__git_path)
            else:
                ConfigParser.__git_dir = git_dir
            ConfigParser.__git_repository_dir = join(ConfigParser.__git_path, constants.GitCcConstants.git_repository_name())
            if ConfigParser.__cc_path is None:
                ConfigParser.__cc_path = self.path(self.core(ConfigParser.__cc_cfg))
            if not ConfigParser.__debug:
                ConfigParser.__debug = ConfigParser.core('debug', False)
            if mode == 'init':
                ConfigParser.__parser.add_section(self.section)
            if not ConfigParser.__cc_path and (len(sys.argv) > 1 and not ("init" == sys.argv[1] or "configure" == sys.argv[1])):
                fail("fatal: Configuration is faulty using branch '%s'" % self.section)

            #if not exists(join(ConfigParser.__git_dir, constants.GitCcConstants.git_repository_name())):
            #    fail("fatal: Not a git repository (or any of the parent directories): .git")

            logger.info('\n')
            logger.info('GitCC Dir: %s' % ConfigParser.__base_dir)
            logger.info('GitCC Conf: %s' % ConfigParser.__conf_file)
            logger.info('Config Section: %s' % self.section)
            logger.info('CC Path: %s' % ConfigParser.__cc_path)
            logger.info('Git Dir: %s' % ConfigParser.__git_dir)
            logger.info('Branches: %s' % self.branches())
            logger.info('\n')
            logger.info('Environment: %s' % os.environ)

            ConfigParser.__initialized = True
        ConfigParser.__lock.release()

    def set_section(self, name, value):
        logger.debug('Section %s, name %s, value %s' % (self.section, name, value))
        ConfigParser.__parser.set(self.section, name, value)

    def section(self):
        return self.section

    def validate_cc(self):
        if not ConfigParser.__cc_path:
            fail("No 'clearcase' variable found for branch '%s'" % self.section)

    def read(self):
        ConfigParser.__parser.read(ConfigParser.__conf_file)

    def write(self):
        ConfigParser.__parser.write(open(ConfigParser.__conf_file, 'w'))

    def core(self, name, *args):
        return self._get(ConfigParser.__core_section, name, *args)

    def get(self, name, *args):
        return self._get(self.section, name, *args)

    def list(self, name, default=None):
        return self.get(name, default).split('|')

    def branches(self):
        return self.list(ConfigParser.__branches_cfg)

    def extra_branches(self):
        return self.list(ConfigParser.__extra_branches_cfg)

    def since(self):
        return self.core(ConfigParser.__since_cfg, '')

    def include(self):
        return self.core(ConfigParser.__include_cfg, '.').split('|')

    def exclude(self):
        return self.core(ConfigParser.__exclude_cfg, '.').split('|')

    @staticmethod
    def _get(section, name, default=None):
        if not ConfigParser.__parser.has_option(section, name):
            return default
        return ConfigParser.__parser.get(section, name)

    @staticmethod
    def cc_cfg():
        return ConfigParser.__cc_cfg

    @staticmethod
    def git_cfg():
        return ConfigParser.__git_cfg

    @staticmethod
    def branches_cfg():
        return ConfigParser.__branches_cfg

    @staticmethod
    def base_dir():
        return ConfigParser.__base_dir

    @staticmethod
    def cc_dir():
        return ConfigParser.__cc_path

    @staticmethod
    def git_dir():
        return ConfigParser.__git_dir

    @staticmethod
    def git_path():
        return ConfigParser.__git_path

    @staticmethod
    def git_repository_dir():
        return ConfigParser.__git_repository_dir

    @staticmethod
    def debug():
        return ConfigParser.__debug

    @staticmethod
    def path(path, args='-m'):
        if constants.GitCcConstants.cygwin():
            return os.popen('cygpath %s "%s"' % (args, path)).readlines()[0].strip()
        else:
            return path
