"""Copy files from Clearcase to Git manually"""

import os
import shutil
import stat

from os.path import join, abspath, isdir
from fnmatch import fnmatch

from cache import Cache
from fileio import IO
from configuration import ConfigParser

import logging
logger = logging.getLogger(__name__)

ARGS = {
    'cache': 'Use the cache for faster syncing'
}


def main(cache=False):
    config = ConfigParser()
    config.validate_cc()
    if cache:
        return sync_cache()
    glob = '*'
    base = abspath(config.cc_dir())
    for i in config.include():
        for (dir_path, dir_names, file_names) in os.walk(join(ConfigParser.cc_dir(), i)):
            rel_dir = dir_path[len(base)+1:]
            if fnmatch(rel_dir, './lost+found'):
                continue
            for file_name in file_names:
                if fnmatch(file_name, glob):
                    copy(join(rel_dir, file_name))


def copy(file_name):
    new_file = join(ConfigParser.git_dir()(), file_name)
    logger.debug('Copying %s' % new_file)
    IO.make_directories(new_file)
    shutil.copy(join(ConfigParser.cc_dir(), file_name), new_file)
    os.chmod(new_file, stat.S_IREAD | stat.S_IWRITE)


def sync_cache():
    cache1 = Cache(ConfigParser.git_dir())
    cache1.start()
    
    cache2 = Cache(ConfigParser.git_dir())
    cache2.initial()
    
    for path in cache2.list():
        if not cache1.contains(path):
            cache1.check_and_update_path_in_current_branch(path)
            if not isdir(join(ConfigParser.cc_dir(), path.file)):
                copy(path.file)
    cache1.write()
