__author__ = 'rognilse'

import unittest
from configuration import ConfigParser

import unittest
from changeset import Change
from constants import GitCcConstants


class ConfigTest(unittest.TestCase):

    def test_config(self):
        config = ConfigParser()
        config.init()
        self.assertTrue(config.cc_dir(), '/clearcase/proj')


if __name__ == "__main__":
    unittest.main()
