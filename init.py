"""Initialise gitcc with a clearcase directory"""

from git import Git
from configuration import ConfigParser
from common import fail


def main(cc_dir):
    try:
        config=ConfigParser('init')
    except:
        fail('\nGitCC already initialized')
    git = Git()

    git.config('core.autocrlf', 'false')
    config.set_section(ConfigParser.cc_cfg(), cc_dir)
    config.write()
    git.commit_empty('Empty commit')
    print '\nGit and ClearCase successfully initialized'