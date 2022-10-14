from unittest import TestCase

from paste_bin.core import renderer


class TestIsValidLexerName(TestCase):
    def test_true(self):
        self.assertTrue(renderer.is_valid_lexer_name("python"))

    def test_false(self):
        self.assertFalse(renderer.is_valid_lexer_name("testing123"))
