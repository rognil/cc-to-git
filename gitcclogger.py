import logging
from threading import Lock
from constants import GitCcConstants


class GitCcLogger(object):
    __loggerLock = Lock()
    __initialized = False

    FORMAT = '%(asctime)-15s %(name)s %(thread)-8s %(message)s'

    def __init__(self, log_file_name, log_level=GitCcConstants.logger_level()):
        GitCcLogger.__loggerLock.acquire()
        if not GitCcLogger.__initialized:
            print '\nInitializing logger: ', log_file_name
            logging.basicConfig(filename=log_file_name, level=log_level, format=self.FORMAT)
            self.log = logging.getLogger(__name__)
            GitCcLogger.__initialized = True
        GitCcLogger.__loggerLock.release()

    @staticmethod
    def info(self, msg, *args, **kwargs):
        self.log.info(msg, args, kwargs)

    @staticmethod
    def debug(self, msg, *args, **kwargs):
        self.log.debug(msg, args, kwargs)

    @staticmethod
    def log(self, level, msg, *args, **kwargs):
        self.log.log(level, msg, args, kwargs)
