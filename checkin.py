"""Checkin new git changesets to Clearcase"""

from clearcase import ClearCase
from git import Git
from configuration import ConfigParser
from constants import GitCcConstants
from transaction import Transaction

# TODO !!!!!!!!!!!!!!
from activity import Modify, Add, Delete, Rename, SymLink

import logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error")


ARGS = {
    'force': 'ignore conflicts and check-in anyway',
    'no_deliver': 'do not deliver in UCM mode',
    'initial': 'checkin everything from the beginning',
    'all': 'checkin all parents, not just the first',
    'cclabel': 'optionally specify an existing Clearcase label type to apply to each element checked in',
}


def main(force=False, no_deliver=False, initial=False, complete=False, cc_label=''):
    config = ConfigParser()
    git = Git()
    clear_case = ClearCase()

    config.validate_cc()
    ignore_conflicts = False
    if force:
        ignore_conflicts = True
    clear_case.update('.')
    log = git.log(complete, initial)
    if not log:
        return
    clear_case.rebase()
    for line in log.split('\x00'):
        identity, comment = line.split('\x01')
        changes = state(git, identity, initial)
        Transaction.commit_transaction(clear_case, git, ignore_conflicts, cc_label, changes, comment.strip(), initial)
        git.tag(config.ci_tag(), identity)
    if not no_deliver:
        clear_case.commit()
    if initial:
        git.commit_empty('Empty commit')
        git.reset.main('HEAD')


def state(self, git, identity, initial):
    changes = self.diff_directory(identity, initial)
    changes = changes.strip()
    changes = changes.strip("\x00")
    split = changes.split('\x00')
    activities = {'M': Modify, 'R': Rename, 'D': Delete, 'A': Add, 'C': Add, 'S': SymLink}
    activity_log = []
    while len(split) > 1:
        char = split.pop(0)[0]  # first char
        args = [split.pop(0)]
        # check if file is really a symlink
        result = git.list_tree(identity, args[0])
        if result.split(' ')[0] == '120000':
            char = 'S'
            args.append(identity)
        if char == 'R':
            args.append(split.pop(0))
        elif char == 'C':
            args = [split.pop(0)]
        if args[0] == GitCcConstants.gitcc_file():
            continue
        activity = activities[char](args)
        activity.id = identity
        activity_log.append(activity)
    return activity_log
