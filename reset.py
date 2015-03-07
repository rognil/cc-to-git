"""Reset hard to a specific tag"""

from git import Git

ARGS = {
    'branch': 'The active branch'
}


def main(git_cc_dir, branch):
    git = Git()
    git.check_out(branch)