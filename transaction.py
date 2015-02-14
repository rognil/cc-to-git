from os.path import join
from configuration import ConfigParser
from encoding import Encoding

import logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error")


class Transaction(object):

    @staticmethod
    def commit_transaction(clear_case, git, ignore_conflicts, cc_label, actions, comment, cc_transaction):
        """Poor mans two-phase commit"""
        if cc_transaction:
            transaction = ClearCaseTransaction(clear_case, cc_label, comment)
        else:
            transaction = GitTransaction(git, ignore_conflicts, clear_case, cc_label, comment)

        for action in actions:
            try:
                action.stage(transaction)
            except:
                transaction.rollback()
                raise

        for action in actions:
            action.commit(transaction)

        transaction.commit(comment)


class ClearCaseTransaction(Transaction):

    def __init__(self, clear_case, cc_label, comment):
        self.CC_LABEL = cc_label
        self.clear_case = clear_case
        self.checked_out = []
        self.cc_label = cc_label
        clear_case.make_activity(comment)

    def remove(self, file_name):
        self.checked_out.remove(file_name)

    def add(self, file_name):
        self.checked_out.append(file_name)

    def co(self, file_name):
        self.clear_case.check_out(file_name)
        if self.cc_label:
            self.clear_case.make_label(self.cc_label, file_name, True)
        self.add(file_name)

    def stage_dir(self, file_name):
        file_name = file_name if file_name else '.'
        if file_name not in self.checked_out:
            self.co(file_name)

    def stage(self, file_name):
        self.co(file_name)

    def rollback(self):
        for file_name in self.checked_out:
            self.clear_case.undo_check_out(file_name)
        self.clear_case.remove_activity()

    def commit(self, comment):
        for file_name in self.checked_out:
            self.clear_case.check_in(comment.encode(Encoding.encoding()), file_name)


class GitTransaction(ClearCaseTransaction):

    def __init__(self, git, ignore_conflicts, clear_case, cc_label, comment):
        self.git = git
        self.ignore_conflicts = ignore_conflicts
        super(self).__init__(clear_case, cc_label, comment)
        self.base = self.git.merge_base(ConfigParser.ci_tag(), 'HEAD').strip()

    def stage(self, file_name):
        super(GitTransaction, self).stage(file_name)
        cc_id = self.git.hash_object(join(ConfigParser.cc_dir(), file_name))
        git_id = self.git.blob(self.base, file_name)
        if cc_id != git_id:
            if not self.ignore_conflicts:
                error_logger.warn('File has been modified: %s. Try rebasing.' % file_name)
                raise Exception('File has been modified: %s. Try rebasing.' % file_name)
            else:
                error_logger.warn('WARNING: Detected possible conflict with', file_name, '...ignoring...')
