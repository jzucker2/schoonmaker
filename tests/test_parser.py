"""Tests for the FDX parser (single parser in schoonmaker)."""

import unittest
from pathlib import Path

from schoonmaker.fdx import FDXParser


def _fixture_path():
    return Path(__file__).parent / "fixtures" / "sample.fdx"


class TestParser(unittest.TestCase):
    def test_parse_returns_screenplay(self):
        screenplay = FDXParser().parse(str(_fixture_path()))
        self.assertIsNotNone(screenplay)
        self.assertEqual(screenplay.document_type, "Script")
        self.assertGreaterEqual(len(screenplay.scenes), 1)
