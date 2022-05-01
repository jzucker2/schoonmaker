from argparse import ArgumentParser


DEFAULT_SAMPLE_FILE_PATH = 'samples/final_draft_sample.fdx'


# https://docs.python.org/3/library/argparse.html#module-argparse
# https://docs.python.org/3/howto/argparse.html
class CLIArgParser(object):
    def __init__(self):
        self.parser = ArgumentParser()

    def _add_args(self):
        self.parser.add_argument('-f', '--file',
                                 type=str,
                                 help='Path to input file',
                                 default=DEFAULT_SAMPLE_FILE_PATH)

    def _parse_args(self):
        return self.parser.parse_args()

    def get_args(self):
        self._add_args()
        return self._parse_args()

    @classmethod
    def get_cli_args(cls):
        parser = cls()
        return parser.get_args()
