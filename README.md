## git-cc for migration

Hi, this branch of git-cc focus on migrating from ClearCase to Git. It is compiled to
support migration of one ClearCase view with multiple branches into a new Git repository.

The idea on this git-cc branch is to prepare the configuration once and then just run the command:

You should start in the folder above where you want your git tree.

### Configuration

Start with running configure to set up environment, this will create a configuration file
gitcc.conf in the subfolder conf.

gitcc configure --cc_dir='/clearcase/proj' --git_dir='gitname', --branches='master'


### Migration

After the configuration is in place run

gitcc migrate

This will create a subfolder for git, initialize git and mirror the ClearCase view into
the newly created Git folder.

Now you got your newly local Git project, you probably want to put it at your preferred host.

## First verify that you are in the master branch
git checkout master

# Then add the project to your favourite git host (favourite.gitsite.com) with a suitable
# project name (projname)
git remote add origin git@favourite.gitsite.com:projname/main.git
git remote show origin


## git-cc Charles O'Farrell

Simple bridge between base ClearCase or UCM and Git.

## Warning

I wrote this purely for fun and to see if I could stop use Clearcase at work
once and for all.

I will probably continue to hack away at it to suite my needs, but I would
love to see it get some real-world polish. (Actually what I would love to see
more is for Clearcase to die, but don't think that's going to happen any time
soon).

Suggestions on anything I've done are more than welcome.

Also, I have made a change recently to support adding binary files which uses
git-cat. Unfortunately git-cat doesn't handle end line conversions and so I
have made gitcc init set core.autocrlf to false. This is only relevant for
Windows users. Don't try changing this after your first commit either as it
will only make matters worse. My apologies to anyone that is stung by this.

## Workflow

Initialise:

    git init
    gitcc init d:/view/xyz
    gitcc rebase
    # Get coffee
    # Do some work
    git add .
    git commit -m "I don't actually drink coffee"
    gitcc rebase
    gitcc checkin

Initialise (fast):

Rebase can be quite slow initially, and if you just want to get a snapshot of
Clearcase, without the history, then this is for you:

    gitcc init d:/view/xyz
    gitcc update "Initial commit"

Other:

These are two useful flags for rebase which is use quite frequently.

    gitcc rebase --stash

Runs stash before the rebase, and pops it back on afterwards.

    gitcc rebase --dry-run

Prints out the list of commits and modified files that are pending in clearcase.

To synchronise just a portion of your git history (instead of from the
very first commit to HEAD), mark the start point with the command:

    gitcc tag <commit>

To specify an existing Clearcase label while checking in, in order to let your
dynamic view show the version of the element(s) just checked in if your
confspec is configured accordingly, use the command:

    gitcc checkin --cclabel=YOUR_EXISTING_CC_LABEL

Note that the CC label will be moved to the new version of the element, if it is already used.

## Configuration

You need to add a mapping for each user in your clearcase history to users.py.
You can also limit which branches and folders you import from.
eg. .git/gitcc

    [core]
    include = FolderA|FolderB
    exclude = FolderA/sub/folder|FolderB/other/file
    debug = False
    type = UCM
    [master]
    clearcase = D:\views\co4222_flex\rd_poc
    branches = main|ji_dev|ji_*_dev|iteration_*_dev
    [sup]
    clearcase = D:\views\co4222_sup\rd_poc
    branches = main|sup

In this case there are two separate git branches, master and sup, which
correspond to different folders/branches in clearcase.

## Notes

Can either work with static or dynamic views. I use dynamic at work because
it's much faster not having to update. I've done an update in rebase anyway,
just-in-case someone wants to use it that way.

Can also work with UCM, which requires the 'type' config to be set to 'UCM'.
This is still a work in progress as I only recently switched to this at work.
Note the history is still retrieved via lshistory and not specifically from
any activity information. This is largely for convenience for me so I don't have
to rewrite everything. Therefore things like 'recommended' baselines are ignored.
I don't know if this will cause any major dramas or not.

## Troubleshooting

1. WindowsError: [Error 2] The system cannot find the file specified

You're most likely running gitcc under Windows Cmd. At moment this isn't
supported. Instead use Git Bash, which is a better console anyway. :-)

If you have both msysgit and Cygwin installed then it may also be
[this](https://github.com/charleso/git-cc/issues/10) problem.

2. cleartool: Error: Not an object in a vob: ".".

The Clearcase directory you've specified in init isn't correct. Please note
that the directory must be inside a VOB, which might be one of the folders
inside the view you've specified.

3. fatal: ambiguous argument 'clearcase': unknown revision or path not in the working tree.

If this is your first rebase then please ignore this. This is expected.

4. pathspec 'master_cc' did not match any file(s) known to git

See Issue [8](https://github.com/charleso/git-cc/issues/8).

## Behind the scenes

A smart person would have looked at other git bridge implementations for
inspiration, such as git-svn and the like. I, on the other hand, decided to go
cowboy and re-invent the wheel. I have no idea how those other scripts do their
business and so I hope this isn't a completely stupid way of going about it.

I wanted to have it so that any point in history you could rebase on-top of the
current working directory. I've done this by using the clearcase commit time
for git as well. In addition the last rebased commit is tagged and is used
to limit the history query for any chances since. This tagged changeset is
therefore also used to select which commits need to be checked into clearcase.

## Problems

It is worth nothing that when initially importing the history from Clearcase
that files not currently in your view (ie deleted) cannot be reached without
a config spec change. This is quite sad and means that the imported history is
not a true one and so rolling back to older revisions will be somewhat limited
as it is likely everything won't compile. Other Clearcase importers seem
restricted by the same problem, but none-the-less it is most frustrating. Grr!
