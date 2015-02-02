"""Reset hard to a specific changeset"""

from git import Git


def main(commit):
    git = Git()
    git.branch(git.cc_tag(), commit)
    git.tag(git.ci_tag(), commit)
