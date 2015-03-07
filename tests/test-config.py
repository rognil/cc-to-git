__author__ = 'rognilse'

from configuration import ConfigParser

config = ConfigParser()
config.init()
if not config.cc_dir() == '/clearcase/proj':
    raise AssertionError("CC directory should have been /cearcase/proj")