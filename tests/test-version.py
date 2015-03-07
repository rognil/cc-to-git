from changeset import ChangeSet
from constants import GitCcConstants


def main():
    line = 'checkindirectory version|20110427.150714|user|/clearcase/proj/dir/util|/main/proj/2|Added element "mkdefs.sparcv9".'
    split = line.split(GitCcConstants.attribute_delimiter())

    cs = ChangeSet(None, None, None, None, split, '')
    print cs.branch


if __name__ == '__main__':
    main()
