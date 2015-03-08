__author__ = 'rognilse'

import unittest
import os

from os.path import join
from gitcclogger import GitCcLogger
from configuration import ConfigParser

import unittest
from changeset import Change
from constants import GitCcConstants


class ConfigTest(unittest.TestCase):

    def test_config(self):

        path = os.getcwd().split(GitCcConstants.file_separator())
        GitCcLogger(join(GitCcConstants.file_separator().join(path),
                         GitCcConstants.conf_dir(), GitCcConstants.logger_conf_name()))

        config = ConfigParser()
        config.init()
        self.assertTrue(config.cc_dir(), '/clearcase/proj')

        print 'Config CC dir: %s' % config.cc_dir()


if __name__ == "__main__":
    unittest.main()
