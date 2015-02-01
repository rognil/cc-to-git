import logging
from threading import Lock
from constants import GitCcDefaultConstants


class GitCcLogger:
    initialized = False
    __loggerLock = Lock()

    def __init__(self, filename=GitCcDefaultConstants.DEFAULT_LOGGER, level=GitCcDefaultConstants.DEFAULT_LOGGER_LEVEL):
        self.init(filename, level)

    def init(self, filename, level):
        GitCcLogger.__loggerLock.acquire()
        if not self.initialized:
            logging.config.fileConfig(filename)
            logging.
            logging.basicConfig(filename, level)
            GitCcLogger.initialized = True
        GitCcLogger.__loggerLock.release()

    @staticmethod
    def info(msg, *args, **kwargs):
        logging.info(msg, args, kwargs)

    @staticmethod
    def debug(msg, *args, **kwargs):
        logging.debug(msg, args, kwargs)

    @staticmethod
    def log(level, msg, *args, **kwargs):
        logging.log(level, msg, args, kwargs)

logger = GitCcLogger()