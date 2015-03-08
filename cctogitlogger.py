""" Initialize logging"""

__author__ = 'rognilse'

import logging
import logging.config
from threading import Lock


class CcToGitLogger(object):
    __loggerLock = Lock()
    __initialized = False

    def __init__(self, log_conf_file='logging.conf'):
        CcToGitLogger.__loggerLock.acquire()
        if not CcToGitLogger.__initialized:
            logging.config.fileConfig(log_conf_file)
            print '\nInitialized logging'
            CcToGitLogger.__initialized = True
        CcToGitLogger.__loggerLock.release()
