"""Tag a particular commit as gitcc start point"""

from configuration import ConfigParser
from git import Git

ARGS = {
    'tag': 'The tag name'
}


def main(git_cc_dir, tag):
    config = ConfigParser()
    config.init(git_cc_dir)
    git = Git()
    git.tag(ConfigParser.ci_tag(), tag)
