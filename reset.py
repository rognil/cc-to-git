"""Reset hard to a specific tag"""

from git import Git

ARGS = {
    'tag': 'The tag name'
}


def main(git_cc_dir, tag):
    git = Git()
    git.check_out(tag)
