"""Migrate from ClearCase"""

from os.path import join

from clearcase import ClearCase
from cache import Cache, NoCache
from git import Git
from fileio import IO
from configuration import ConfigParser
from encoding import Encoding
from changeset import ChangeSet, Uncataloged, Group
from constants import GitCcConstants
from common import fail

import logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error")


"""
Things remaining:
1. Renames with no content change. Tricky.
"""


DELIM = '|'

ARGS = {
    'stash': 'Wraps the migration in a stash to avoid file changes being lost',
    'dry_run': 'Prints a list of change sets to be imported',
    'lshistory': 'Prints the raw output of lshistory to be cached for load',
    'load': 'Loads the contents of a previously saved lshistory file',
}


def main(git_cc_dir='.', stash=False, dry_run=False, lshistory=False, load=None):

    base_dir = GitCcConstants.file_separator().join(git_cc_dir)
    config = ConfigParser()
    config.init(base_dir)
    git = Git(config.git_path())
    clear_case = ClearCase()
    io = IO()

    io.make_directory(config.git_path())
    io.cd(config.git_path())

    if not io.directory_exists(GitCcConstants.git_repository_name()):
        git.init()
        git.config('core.autocrlf', 'false')
        git.commit_empty('Empty commit')

    git.config('core.autocrlf', 'false')

    print '\nGit and ClearCase successfully initialized'

    if config.core('cache', True) == 'False':
        cache = NoCache()
    else:
        cache = Cache(config.git_dir())

    config.validate_cc()
    if not (stash or dry_run or lshistory):
        git.check_pristine()

    clear_case.update()

    since = git.since_date(config.get('since'))
    cache.start()
    if load:
        history = open(load, 'r').read().decode(Encoding.encoding())
    else:
        clear_case.rebase()
        history = clear_case.fetch_history(since)
        io.write(join(base_dir, GitCcConstants.conf_dir(), GitCcConstants.history_file()), history.encode(Encoding.encoding()))
        history = open(join(base_dir, GitCcConstants.conf_dir(), GitCcConstants.history_file()), 'r').read().decode(Encoding.encoding())

    if lshistory:
        print(history)
    else:
        change_set = parse_history(cache, config, clear_case, git, history)
        change_set = reversed(change_set)
        change_set = merge_history(cache, clear_case, git, change_set)
        if dry_run:
            print_groups(change_set)
            io.cd(base_dir)
            return
        if not len(change_set):
            print "Change set failed"
            io.cd(base_dir)
            return
        git.stash(lambda: do_commit(change_set, git), stash)
    io.cd(base_dir)


def do_commit(change_set, git):

    """Commit change set to Git"""
    for cs in change_set:
        branch = git.current_branch()
        logger.debug("Change set branch: %s" % branch)
        if branch != cs.branch:
            if not cs.branch is None:
                branch = cs.branch
                try:
                    git.check_out(branch)
                except Exception as e:
                    git.branch(branch)
                    git.check_out(branch)
        logger.debug("Commit change set on branch: %s" % branch)
        cs.commit()


def parse_history(cache, config, clear_case, git, lines):

    types = {
        'checkinversion': ChangeSet,
        'checkindirectory version': Uncataloged,
    }

    change_sets = []

    def add(_cache, _config, _clear_case, _git, _split, _comment):
        if not _split:
            return
        cstype = _split[0]
        if cstype in types:
            cs = types[cstype](_cache, _config, _clear_case, _git, _split, _comment)
            try:
                branch = cs.filter_branches(_config, cs.version)
                logger.debug('Parse history %s to branch %s', cs.to_string(), branch)
                if branch is not None:
                    cs.branch = branch
                    logger.info('Append change set: %s', cs.to_string())
                    change_sets.append(cs)
            except Exception as e:
                error_logger.warn('Bad line %s, %s' % (_split, _comment))
                raise

    last = None
    comment = None
    for line in lines.splitlines():
        split = line.split(DELIM)
        if len(split) < 6 and last:
            # Cope with comments with '|' character in them
            comment += "\n" + DELIM.join(split)
        else:
            add(cache, config, clear_case, git, last, comment)
            comment = DELIM.join(split[5:])
            last = split
    add(cache, config, clear_case, git, last, comment)
    return change_sets


def merge_history(cache, clear_case, git, change_sets):
    last = None
    groups = []

    def same(a, b):
        return a.subject == b.subject and a.user == b.user and a.branch == b.branch

    for change in change_sets:
        if last and same(last, change):
            last.append(change)
        else:
            last = Group(cache, clear_case, git, change)
            groups.append(last)
    for group in groups:
        group.fix_comment()
    return groups


def print_groups(groups):
    for cs in groups:
        print('%s "%s"' % (cs.user, cs.subject))
        for f in cs.files:
            print("  %s" % f.file)
