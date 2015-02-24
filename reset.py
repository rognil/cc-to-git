"""Reset hard to a specific change set"""

from git import Git

ARGS = {
    'tag': 'The tag name'
}


def main(git_cc_dir, tag):
    git = Git()
    git.branch(git.cc_tag(), tag)
    git.tag(git.ci_tag(), tag)
