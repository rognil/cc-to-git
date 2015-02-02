import sys
import locale

from constants import GitCcConstants


class Encoding:
    __encoding = None

    def __init__(self):
        if hasattr(sys.stdin, 'encoding'):
            Encoding.__encoding = sys.stdin.encoding
        if Encoding.__encoding is None:
            locale_name, self.__encoding = locale.getdefaultlocale()
        if Encoding.__encoding is None:
            Encoding.__encoding = GitCcConstants.encoding()

    @staticmethod
    def encoding():
        return Encoding.__encoding

    def decode_string(self, encoding_str, output):
        try:
            return output.decode(encoding_str)
        except UnicodeDecodeError as e:
            print >> sys.stderr, output, ":", e
            return output.decode(encoding_str, "ignore")
