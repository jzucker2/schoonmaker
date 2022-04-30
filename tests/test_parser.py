import unittest
from schoonmaker.parser import Parser


class TestParser(unittest.TestCase):
    def test_stub(self):
        parser = Parser()
        self.assertIsNotNone(parser)


if __name__ == '__main__':
    unittest.main()
