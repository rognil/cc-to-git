from os.path import join, exists, abspath, dirname
import sys

import logging
error_logger = logging.getLogger("error")


def fail(string):
    error_logger.error("Migration failed %s" % string)
    sys.exit(2)


