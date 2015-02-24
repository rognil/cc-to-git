"""Configure gitcc by creating a config file
based on input, ClearCase directory and branch info
"""

from git import Git
from configuration import ConfigParser
from common import fail
from os.path import join, basename

ARGS = {
    'cc_dir': 'ClearCase directory',
    'git_dir': 'Git directory',
    'branches': 'A pipe separated list of branches branch1|branch2|branch3'
}


def main(git_cc_dir, cc_dir='clearcase', git_dir='git', branches='master'):

    Git('.', 'master')

    try:
        config = ConfigParser()
        config.init(git_cc_dir, 'init', git_dir)
    except:
        print('\nGitCC already configured\n')
        return

    config.set_section(ConfigParser.cc_cfg(), cc_dir)

    if basename(git_dir) == git_dir:
        config.set_section(ConfigParser.git_cfg(), join(git_cc_dir, git_dir))
    else:
        config.set_section(ConfigParser.git_cfg(), git_dir)

    config.set_section(ConfigParser.branches_cfg(), branches)
    config.write()
    print '\nConfiguration initialized'