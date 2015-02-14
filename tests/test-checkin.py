from __init__ import *
import checkin
import unittest, os
from os.path import join
from git import Git


class CheckInTest(TestCaseEx):
    def setUp(self):
        TestCaseEx.setUp(self)
        self.expectedExec.append((['cleartool', 'update', '.'], ''))
        self.commits = []

    def check_in(self):
        self.expectedExec.insert(1,
                                 (['git', 'log', '--first-parent', '--reverse', '--pretty=format:%H%n%s%n%b',
                                   '%s..' % Git.ci_tag()], '\n'.join(self.commits)),
        )
        checkin.main()
        self.assert_(not len(self.expectedExec))

    def commit(self, commit, message, files):
        nameStatus = []
        for type, file in files:
            nameStatus.append('%s\0%s' % (type, file))
        self.expectedExec.extend([
            (['git', 'diff', '--name-status', '-M', '-z', '%s^..%s' % (commit, commit)], '\n'.join(nameStatus)),
        ])
        types = {'M': MockModfy, 'A': MockAdd, 'D': MockDelete, 'R': MockRename}
        self.expectedExec.extend([
            (['git', 'merge-base', Git.ci_tag(), 'HEAD'], 'abcdef'),
        ])
        for type, file in files:
            types[type](self.expectedExec, commit, message, file)
        self.expectedExec.extend([
            (['git', 'tag', '-f', Git.ci_tag(), commit], ''),
        ])
        self.commits.extend([commit, message, ''])

    def testEmpty(self):
        self.check_in()

    def testSimple(self):
        self.commit('sha1', 'commit1', [('M', 'a.py')])
        self.commit('sha2', 'commit2', [('M', 'b.py')])
        self.commit('sha3', 'commit3', [('A', 'c.py')])
        self.check_in();

    def testFolderAdd(self):
        self.commit('sha4', 'commit4', [('A', 'a/b/c/d.py')])
        self.check_in();

    def testDelete(self):
        os.mkdir(join(CC_DIR, 'd'))
        self.commit('sha4', 'commit4', [('D', 'd/e.py')])
        self.check_in();

    def testRename(self):
        os.mkdir(join(CC_DIR, 'a'))
        self.commit('sha1', 'commit1', [('R', 'a/b.py\0c/d.py')])
        self.check_in();


class MockStatus:
    def list_tree(self, id, file, hash):
        return (['git', 'ls-tree', '-z', id, file], '100644 blob %s %s' % (hash, file))

    def cat_file(self, file, hash):
        blob = "blob"
        return [
            (['git', 'cat-file', 'blob', hash], blob),
            (join(CC_DIR, file), blob),
        ]

    def hash(self, file):
        hash1 = 'hash1'
        return [
            (['git', 'hash-object', join(CC_DIR, file)], hash1 + '\n'),
            self.list_tree('abcdef', file, hash1),
        ]

    def check_out(self, file):
        return ['cleartool', 'co', '-reserved', '-nc', file], ''

    def check_in(self, message, file):
        return ['cleartool', 'ci', '-identical', '-c', message, file], ''

    def make_element(self, file):
        return ['cleartool', 'mkelem', '-nc', '-eltype', 'directory', file], ''

    def dir(self, file):
        return file[0:file.rfind('/')];


class MockModfy(MockStatus):
    def __init__(self, e, commit, message, file):
        hash2 = "hash2"
        e.append(self.check_out(file))
        e.extend(self.hash(file))
        e.append(self.list_tree(commit, file, hash2))
        e.extend(self.cat_file(file, hash2))
        e.append(self.check_in(message, file))


class MockAdd(MockStatus):
    def __init__(self, e, commit, message, file_name):
        hash = 'hash'
        files = []
        files.append(".")
        e.append(self.check_out("."))
        path = ""
        for f in file_name.split('/')[0:-1]:
            path = path + f + '/'
            f = path[0:-1]
            files.append(f)
            e.append(self.make_element(f))
        e.append(self.list_tree(commit, file_name, hash))
        e.extend(self.cat_file(file_name, hash))
        e.append((['cleartool', 'mkelem', '-nc', file_name], '.'))
        for f in files:
            e.append(self.check_in(message, f))
        e.append(self.check_in(message, file_name))


class MockDelete(MockStatus):
    def __init__(self, e, commit, message, file):
        dir = file[0:file.rfind('/')]
        e.extend([
            self.check_out(dir),
            (['cleartool', 'rm', file], ''),
            self.check_in(message, dir),
        ])


class MockRename(MockStatus):
    def __init__(self, e, commit, message, file):
        a, b = file.split('\0')
        hash = 'hash'
        e.extend([
            self.check_out(self.dir(a)),
            self.check_out(a),
        ])
        e.extend(self.hash(a))
        e.extend([
            self.check_out("."),
            self.make_element(self.dir(b)),
            (['cleartool', 'mv', '-nc', a, b], '.'),
            self.list_tree(commit, b, hash),
        ])
        e.extend(self.cat_file(b, hash))
        e.extend([
            self.check_in(message, self.dir(a)),
            self.check_in(message, "."),
            self.check_in(message, self.dir(b)),
            self.check_in(message, b),
        ])


if __name__ == "__main__":
    unittest.main()
