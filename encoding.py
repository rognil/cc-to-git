import sys
import locale

import logging
error_logger = logging.getLogger("error")

from constants import GitCcConstants


class Encoding:
    __encoding = None

    def __init__(self):
        if hasattr(sys.stdin, 'encoding'):
            Encoding.__encoding = sys.stdin.encoding
        if Encoding.__encoding is None:
            Encoding.__encoding = GitCcConstants.encoding()
        if Encoding.__encoding is None:
            locale_name, self.__encoding = locale.getdefaultlocale()

    @staticmethod
    def encoding():
        return Encoding.__encoding

    @staticmethod
    def decode(str):
        return str.decode(Encoding.__encoding)

    @staticmethod
    def decode_string(encoding_str, output):
        try:
            return output.decode(encoding_str)
        except UnicodeDecodeError as e:
            error_logger.warn('Error: %s' % e)
            return output.decode(encoding_str, "ignore")
