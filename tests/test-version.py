__author__ = 'rognilse'

import unittest
import os

from os.path import join
from cctogitlogger import CcToGitLogger
from constants import GitCcConstants


class VersionTest(unittest.TestCase):

    def test_version(self):

        path = os.getcwd().split(GitCcConstants.file_separator())
        CcToGitLogger(join(GitCcConstants.file_separator().join(path),
                         GitCcConstants.conf_dir(), GitCcConstants.logger_conf_name()))

        _git = __import__('git')
        _clear_case = __import__('clearcase')

        _configuration = __import__('configuration')

        _cache = __import__('cache')

        _change_set = __import__('changeset')

        base_dir = GitCcConstants.file_separator().join('.')
        config = _configuration.ConfigParser()
        config.init(base_dir)
        git = _git.Git(config.git_path())
        clear_case = _clear_case.ClearCase(config.cc_dir(), config.include())
        cache = _cache.NoCache()

        change = 'checkindirectory version|19980709.133241|vobadm|/clearcase/tis/TIS/util|/main/1|Created by importer'
        split = change.split(GitCcConstants.attribute_delimiter())
        comment = GitCcConstants.attribute_delimiter().join(split[5:])

        uncatalogued_change = _change_set.Uncatalogued(cache, config, clear_case, git, split, comment)
        versions = [[u'**null operation kind**file element', u'19980709.133146', u''], [u'checkinversion', u'19951011.130004', u'/main/1'], [u'mkelemversion', u'19951011.130004', u'/main/0'], [u'mkelembranch', u'19951011.130004', u'/main'], [u'mkelemfile element', u'19951011.130004', u'']]

        uncatalogued_change.check_in_versions(versions)


if __name__ == "__main__":
    unittest.main()
