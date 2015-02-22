"""Tag a particular commit as gitcc start point"""

from configuration import ConfigParser
from git import Git


def main(git_cc_dir, commit):
    git = Git()
    git.tag(ConfigParser.ci_tag(), commit)
