from os.path import join, dirname, exists

from configuration import ConfigParser
from git import Git
from clearcase import ClearCase



class Activity:

    config = ConfigParser()
    git = Git()
    clear_case = ClearCase()

    def __init__(self, file_name=None):
        self.file_name = file_name
        self.directories = None

    def cat(self):
        blob = self.git.cat_blob_file(self.id, self.file_name)
        self.config.write(join(self.config.cc_dir(), self.file_name), blob)

    def stage_dirs(self, transaction):
        directory = dirname(self.file_name)
        directories = []
        while not exists(join(self.config.cc_dir(), directory)):
            directories.append(directory)
            directory = dirname(directory)
        self.directories = directories
        transaction.stage_dir(directory)

    def commit_directories(self, transactions):
        while len(self.directories) > 0:
            directory = self.directories.pop();
            if not exists(join(self.config.cc_dir(), directory)):
                self.clear_case.make_element(directory, True)
                if transactions.cc_label:
                    self.clear_case.make_label(transactions.cc_label, directory)
                transactions.add(directory)


class Modify(Activity):

    def __init__(self):
        Activity.__init__()

    def stage(self, transaction):
        transaction.stage(self.file_name)

    def commit(self, transaction):
        self.cat()


class Add(Activity):

    def __init__(self):
        Activity.__init__()

    def stage(self, transaction):
        self.stage_dirs(transaction)

    def commit(self, transaction):
        self.commit_directories(transaction)
        self.cat()
        self.clear_case.make_element(self.file_name)
        if transaction.cc_label:
            self.clear_case.make_label(transaction.cc_label, self.file_name)
        transaction.add(self.file_name)


class Delete(Activity):

    def __init__(self):
        Activity.__init__()

    def stage(self, transaction):
        transaction.stage_dir(dirname(self.file_name))

    def commit(self, transaction):
        # TODO Empty dirs?!?
        self.clear_case.remove(self.file_name)


class Rename(Activity):

    def __init__(self, files):
        Activity.__init__(files[1])
        self.old = files[0]
        self.new = files[1]

    def stage(self, transaction):
        transaction.stage_dir(dirname(self.old))
        transaction.stage(self.old)
        self.stage_dirs(transaction)

    def commit(self, transaction):
        self.commit_directories(transaction)
        self.clear_case.move(self.old, self.new)
        transaction.remove(self.old)
        transaction.add(self.new)
        self.cat()


class SymLink(Activity):
    def __init__(self, files):
        Activity.__init__(files[0])
        identity = files[1]
        self.target = self.git.cat_blob_file(identity, self.file_name)
        if exists(join(ConfigParser.cc_dir(), self.file_name)):
            self.remove_first = True
        else:
            self.remove_first = False

    def stage(self, transaction):
        self.stage_dirs(transaction)

    def commit(self, transaction):
        if self.remove_first:
            self.clear_case.remove(self.file_name)
        self.clear_case.link(self.target, self.file_name)
