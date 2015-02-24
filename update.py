"""Update the git repository with Clearcase manually, ignoring history"""

import sync, reset

from clearcase import ClearCase
from git import Git

ARGS = {
    'message': 'Commit message'
}


def main(git_cc_dir, message):
    git = Git()
    clear_case = ClearCase()

    clear_case.update('.')
    sync.main()
    git.add('.')
    git.commit(message)
    reset.main('HEAD')
