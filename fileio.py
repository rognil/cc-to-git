from os.path import dirname, exists
import os

import logging
logger = logging.getLogger(__name__)

from encoding import Encoding
import constants
import configuration


class IO():
    def __init__(self):
        self.encoding = Encoding()
        self.config = configuration.ConfigParser()
        self.constants = constants.GitCcConstants()

    @staticmethod
    def write(file_path, blob):
        IO.__write(file_path, blob)

    @staticmethod
    def __write(file_path, blob):
        f = open(file_path, 'wb')
        f.write(blob)
        f.close()

    @staticmethod
    def make_directories(path):
        directory = dirname(path)
        if not exists(directory):
            os.makedirs(directory)

    @staticmethod
    def remove_file(name):
        if exists(name):
            os.remove(name)
