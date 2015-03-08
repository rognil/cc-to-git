__author__ = 'rognilse'

import unittest
import os

from os.path import join
from cctogitlogger import CcToGitLogger
from constants import GitCcConstants


class ReadChangesTest(unittest.TestCase):

    def test_version(self):
        path = os.getcwd().split(GitCcConstants.file_separator())
        CcToGitLogger(join(GitCcConstants.file_separator().join(path),
                         GitCcConstants.conf_dir(), GitCcConstants.logger_conf_name()))

        _git = __import__('git')
        _clear_case = __import__('clearcase')

        _configuration = __import__('configuration')

        _cache = __import__('cache')
        _encoding = __import__('encoding')
        _migrate = __import__('migrate')

        base_dir = GitCcConstants.file_separator().join('.')
        config = _configuration.ConfigParser()
        config.init(base_dir)
        git = _git.Git(config.git_path())
        clear_case = _clear_case.ClearCase(config.cc_dir(), config.include())
        cache = _cache.NoCache()
        history = open(join(base_dir, GitCcConstants.conf_dir(),
                            GitCcConstants.history_file()), 'r').read().decode(_encoding.Encoding.encoding())

        changes = _migrate.parse_history(cache, config, clear_case, git, history)
        changes = reversed(changes)
        change_sets = _migrate.group_history(cache, clear_case, git, changes)
        _migrate.print_change_sets(change_sets)


if __name__ == "__main__":
    unittest.main()
