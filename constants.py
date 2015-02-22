__author__ = 'rognilse'

import logging
import sys
import os


class GitCcConstants:

    __default_config_dir = "conf"
    __default_config_file = 'gitcc.conf'
    __default_logger_config = "logging.conf"
    __default_logger_level = logging.DEBUG
    __default_encoding = "ISO8859-15"
    __debug = 1
    __history_file = "lshistory.bak"
    __gitcc_file = '.gitcc'
    __simulate_cc = 0
    __simulate_git = 0
    __enable_history = 1
    __cygwin = sys.platform == 'cygwin'
    __fs = os.sep
    if __cygwin:
        __fs = '\\'

    def __init__(self):
        pass

    @staticmethod
    def conf_dir():
        return GitCcConstants.__default_config_dir

    @staticmethod
    def conf_file():
        return GitCcConstants.__default_config_file

    @staticmethod
    def logger_conf_name():
        return GitCcConstants.__default_logger_config

    @staticmethod
    def gitcc_file():
        return GitCcConstants.__gitcc_file

    @staticmethod
    def logger_level():
        return GitCcConstants.__default_logger_level

    @staticmethod
    def encoding():
        return GitCcConstants.__default_encoding

    @staticmethod
    def file_separator():
        return GitCcConstants.__fs

    @staticmethod
    def debug():
        return GitCcConstants.__debug

    @staticmethod
    def cygwin():
        return GitCcConstants.__cygwin

    @staticmethod
    def history_file():
        return GitCcConstants.__history_file

    @staticmethod
    def simulate_cc():
        return GitCcConstants.__simulate_cc

    @staticmethod
    def simulate_git():
        return GitCcConstants.__simulate_git

    @staticmethod
    def enable_history():
        return GitCcConstants.__enable_history
