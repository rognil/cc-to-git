""" Initialize logging"""

__author__ = 'rognilse'

import logging
import logging.config
from threading import Lock


class GitCcLogger(object):
    __loggerLock = Lock()
    __initialized = False

    def __init__(self, log_conf_file='logging.conf'):
        GitCcLogger.__loggerLock.acquire()
        if not GitCcLogger.__initialized:
            logging.config.fileConfig(log_conf_file)
            print '\nInitialized logging'
            GitCcLogger.__initialized = True
        GitCcLogger.__loggerLock.release()
