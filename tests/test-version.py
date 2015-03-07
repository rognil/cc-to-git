__author__ = 'rognilse'

import unittest
from changeset import Change
from constants import GitCcConstants


class VersionTest(unittest.TestCase):

    def test_version(self):
        line = 'checkindirectory version|20110427.150714|user|/clearcase/proj/dir/util|/main/proj/subproj/2|Added element "mkdefs.sparcv9".'
        split = line.split(GitCcConstants.attribute_delimiter())
        cs = Change(None, None, None, None, split, '')
        print 'Branch %s' % cs.branch
        self.assertTrue(cs.branch == 'proj_subproj')


if __name__ == "__main__":
    unittest.main()
