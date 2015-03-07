# git-cc for migration

Hi, this branch of git-cc focus on migrating from ClearCase to Git. It is compiled to
support migration of one ClearCase view with multiple branches into a new Git repository.
No syncing or updating ClearCase supported, just migration from ClearCase to Git.

The idea on this git-cc branch is to prepare the configuration once and then just run the
command git-cc migrate to migrate the repository to Git.

The git tree will be created in a subfolder to the directory you start from.

### Configuration

#### Common Configuration

Start with running configure to set up environment, this will create a configuration file
gitcc.conf in the subfolder conf:

    gitcc configure --cc_dir='/clearcase/proj' --git_dir='gitname', --branches='master'

Or just create the conf/gitcc.conf file.

    [git_cc_core]
    clearcase = /clearcase/proj
    git = /home/username/git-cc/proj
    branches = main|1.1.0|Linux|pgsql|work

### Include

You can choose to include a subset of folders

    include = FolderA|FolderB

### Exclude

You can choose to exclude a subset of folders

    exclude = FolderA/sub/folder|FolderB/other/file


#### User configuration

You need to add a mapping for each user in your clearcase history to conf/users.py, look at the users.py.example file
to get an idea about the syntax.

    users = {
        'charles': "Charles Smith",\
        'js': 'Jan Smith <jan.smith@dummy.xxx>',\
    }

    mailSuffix = 'dummy.xxx'

### Migration

After the configuration is in place run the migration command:

    gitcc migrate

This will create a subfolder for git, initialize git and mirror the ClearCase view into
the newly created Git folder.

### Add remote hosting

Now you got your newly local Git project, you probably want to put it at your preferred host.

First verify that you are in the master branch:

    git checkout master

Then add the project to your favourite git host (favourite.gitsite.com) with a suitable
project name (projname):

    git remote add origin git@favourite.gitsite.com:projname/main.git
    git remote show origin

## Troubleshooting

### Encoding

This project is setup with europe encoding ISO8859-15.

So you might want to change the default encoding by editing the constants.py file.

That is the encoding:

    __default_encoding = "ISO8859-15"

For latin1 encoding:

    __default_encoding = "ISO8859-1"

For UTF-8 encoding

    __default_encoding = "UTF-8"


## NOTICE!

### Branches

Branches get flattened, that is branch_a/sub_branch_a/sub_branch_a_b will be a new level one branch called branch_a_sub_branch_a_sub_branch_a_b

### Labels / Tags

All tags will end up on the main branch :(.

## Problems

It is worth nothing that when initially importing the history from Clearcase
that files not currently in your view (ie deleted) cannot be reached without
a config spec change. This is quite sad and means that the imported history is
not a true one and so rolling back to older revisions will be somewhat limited
as it is likely everything won't compile. Other Clearcase importers seem
restricted by the same problem, but none-the-less it is most frustrating. Grr!


## Parts of the original Readme for git-cc by Charles O'Farrell, refactored to match new conditions


### Warning

Also, I have made a change recently to support adding binary files which uses
git-cat. Unfortunately git-cat doesn't handle end line conversions and so I
have made gitcc init set core.autocrlf to false. This is only relevant for
Windows users. Don't try changing this after your first commit either as it
will only make matters worse. My apologies to anyone that is stung by this.


### Notes

Can either work with static or dynamic views. I use dynamic at work because
it's much faster not having to update. I've done an update in rebase anyway,
just-in-case someone wants to use it that way.

Can also work with UCM, which requires the 'type' config to be set to 'UCM'.
This is still a work in progress as I only recently switched to this at work.
Note the history is still retrieved via lshistory and not specifically from
any activity information. This is largely for convenience for me so I don't have
to rewrite everything. Therefore things like 'recommended' baselines are ignored.
I don't know if this will cause any major dramas or not.

### Troubleshooting

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

