import sys
import shutil
import unittest
sys.path.append("..")

from os.path import join
from cache import Cache, CCFile

import cache
import tempfile

TEMP1 = """
file.py@@/main/a/b/1
"""

TEMP1_EXPECTED = """file.py@@/main/a/b/2
file2.py@@/main/c/2
"""


class CacheTest(unittest.TestCase):
    def testLoad(self):
        directory = tempfile.mkdtemp()
        f = open(join(directory, cache.FILE), 'w')
        f.write(TEMP1)
        f.close()

        _configuration = __import__('configuration')

        try:
            c = Cache(directory, _configuration.branches(), _configuration.core('type'), _configuration.cc_dir(), _configuration.include())

            self.assertFalse(c.isChild(CCFile('file.py', '/main/a/1')))
            self.assertFalse(c.isChild(CCFile('file.py', r'\main\a\1')))
            self.assertTrue(c.isChild(CCFile('file.py', '/main/a/b/c/1')))
            self.assertFalse(c.isChild(CCFile('file.py', '/main/a/c/1')))
            c.check_and_update_path_in_current_branch(CCFile('file.py', '/main/a/b/2'))
            c.check_and_update_path_in_current_branch(CCFile('file2.py', '/main/c/2'))
            c.write()
            f = open(join(directory, cache.FILE), 'r')
            try:
                self.assertEqual(TEMP1_EXPECTED, f.read())
            finally:
                f.close()
        finally:
            shutil.rmtree(directory)

if __name__ == "__main__":
    unittest.main()
