"""Migrate from ClearCase"""

from os.path import join

from clearcase import ClearCase
from cache import Cache, NoCache
from git import Git
from fileio import IO
from configuration import ConfigParser
from encoding import Encoding
from changeset import Change, Uncatalogued, Branch, Tag, ChangeSet
from constants import GitCcConstants

import logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error")


"""
Things remaining:
1. Renames with no content change. Tricky.
"""


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
    clear_case = ClearCase(config.cc_dir(), config.include())
    io = IO()

    io.make_directory(config.git_path())
    io.cd(config.git_path())

    if not io.directory_exists(GitCcConstants.git_repository_name()):
        git.init()
        git.config('core.autocrlf', 'false')
        git.commit_empty('Empty commit')

    git.config('core.autocrlf', 'false')

    print '\nGit and ClearCase successfully initialized'

    if config.core('cache', True) == 'True':
        cache = Cache(config.base_dir(), config.branches(), config.core('type'), config.cc_dir(), config.include())
    else:
        cache = NoCache()

    config.validate_cc()
    if not (stash or dry_run or lshistory):
        git.check_pristine()

    clear_case.update()

    since = git.since_date(config.since())
    cache.start()
    if load:
        if not load.startswith(GitCcConstants.file_separator()):
            load = join(base_dir, load)
        history = open(load, 'r').read().decode(Encoding.encoding())
    else:
        clear_case.rebase()
        history = clear_case.fetch_history(since)
        io.write(join(base_dir, GitCcConstants.conf_dir(), GitCcConstants.history_file()), history.encode(Encoding.encoding()))
        history = open(join(base_dir, GitCcConstants.conf_dir(), GitCcConstants.history_file()), 'r').read().decode(Encoding.encoding())

    if lshistory:
        print(history)
    else:
        changes = parse_history(cache, config, clear_case, git, history)
        changes = reversed(changes)
        change_sets = group_history(cache, clear_case, git, changes)
        if dry_run:
            print_change_sets(change_sets)
            io.cd(base_dir)
            return
        if not len(change_sets):
            logger.warning("No changes, change set failed")
            io.cd(base_dir)
            return
        git.stash(lambda: do_commit(change_sets, git), stash)
    io.cd(base_dir)


def do_commit(change_sets, git):

    """ Commit change sets to Git
    :param change_sets:
    :param git:
    :return:
    """

    branch = git.current_branch()
    for cs in change_sets:
        logger.debug("Change set branch: %s" % branch)
        if branch != cs.branch:
            if cs.branch is not None:
                branch = cs.branch
                try:
                    git.check_out(branch)
                    logger.info("Commit change set on branch: %s" % branch)
                except Exception as e:
                    git.branch(branch)
                    git.check_out(branch)
                    logger.info("Commit change set on branch: %s" % branch)
        cs.commit()


def parse_history(cache, config, clear_case, git, lines):
    """ Read changes from file

    :param cache:
    :param config:
    :param clear_case:
    :param git:
    :param lines:
    :return:
    """

    types = {
        'checkinversion': Change,
        'checkindirectory version': Uncatalogued,
        'mkbranchbranch': Branch,
        'mktypelabel type': Tag,
    }

    changes = []

    def add(_cache, _config, _clear_case, _git, _split, _comment):
        if not _split:
            return
        cs_type = _split[0]
        if cs_type in types:
            cs = types[cs_type](_cache, _config, _clear_case, _git, _split, _comment)
            try:
                if cs_type != 'mktypelabel type':
                    branch = cs.filter_branches(_config, cs.version, cs.branch)
                    logger.debug('Parse history %s to branch %s', cs.to_string(), branch)
                    if branch is not None:
                        logger.info('Append change set: %s', cs.to_string())
                        changes.append(cs)
                    else:
                        logger.warning('Skip line with no branch: %s', cs.to_string)
                else:
                    changes.append(cs)
            except Exception as e:
                error_logger.warn('Bad line %s, %s' % (_split, _comment))
                raise

    last = None
    comment = None
    for line in lines.splitlines():
        split = line.split(GitCcConstants.attribute_delimiter())
        if len(split) < 6 and last:
            # Cope with comments with '|' character in them
            comment += "\n" + GitCcConstants.attribute_delimiter().join(split)
        else:
            add(cache, config, clear_case, git, last, comment)
            comment = GitCcConstants.attribute_delimiter().join(split[5:])
            last = split
    add(cache, config, clear_case, git, last, comment)
    return changes


def group_history(cache, clear_case, git, changes):
    """ Group history into change sets
    :param cache:
    :param clear_case:
    :param git:
    :param changes:
    :return:
    """
    last = None
    change_sets = []

    def same_change_set(a, b):
        return a.subject == b.subject and a.user == b.user and a.version == b.version

    for change in changes:
        if last and same_change_set(last, change):
            last.append(change)
        else:
            last = ChangeSet(cache, clear_case, git, change)
            change_sets.append(last)
    for cs in change_sets:
        cs.fix_comment()
    return change_sets


def print_change_sets(change_sets):
    for cs in change_sets:
        logger.info('%s "%s" %s' % (cs.user, cs.subject, cs.branch))
        if cs.changes():
            for f in cs.changes():
                logger.info("  %s" % f.file)
