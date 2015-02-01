import logging
import sys
import os


def constants():
    return GitCcDefaultConstants()


class GitCcDefaultConstants:
    DEFAULT_LOGGER = "gitcc.log"
    DEFAULT_LOGGER_LEVEL = logging.DEBUG
    DEFAULT_ENCODING = "ISO8859-15"
    DEBUG = 1
    HISTORY_FILE = "lshistory.bak"
    SIMULATE_CC = 1
    SIMULATE_GIT = 0
    ENABLE_HISTORY = 1
    CYGWIN = sys.platform == 'cygwin'
    FS = os.sep
    if CYGWIN:
        FS = '\\'

    def __init__(self):
        pass

    def logger_name(self):
        return self.DEFAULT_LOGGER

    def logger_level(self):
        return self.DEFAULT_LOGGER_LEVEL

    def encoding(self):
        return self.DEFAULT_ENCODING

    def debug(self):
        return self.DEBUG

    def cygwin(self):
        return self.IS_CYGWIN

    def history_file(self):
        return self.HISTORY_FILE

    def simulate_cc(self):
        return self.SIMULATE_CC

    def simulate_git(self):
        return self.SIMULATE_GIT

    def enable_history(self):
        return self.ENABLE_HISTORY
