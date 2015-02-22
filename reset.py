"""Reset hard to a specific change set"""

from git import Git


def main(git_cc_dir, commit):
    git = Git()
    git.branch(git.cc_tag(), commit)
    git.tag(git.ci_tag(), commit)
