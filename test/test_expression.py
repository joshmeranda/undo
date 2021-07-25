import unittest
from expression import *
import expression

tokenizer = expression.__tokenize


class TestTokenize(unittest.TestCase):
    def test_tokenize_empty(self):
        expected = list()
        actual = tokenizer("")

        self.assertListEqual(expected, actual)

    def test_single_ident(self):
        expected = [
            Token(TokenKind.IDENT, "A", 1)
        ]
        actual = tokenizer("A")

        self.assertListEqual(expected, actual)

    def test_basic_ternary(self):
        expected = [
            Token(TokenKind.IDENT, "A", 1),
            Token(TokenKind.TERNAY_IF, "?", 2),
            Token(TokenKind.IDENT, "B", 3),
            Token(TokenKind.TERNAY_ELSE, ":", 4),
            Token(TokenKind.IDENT, "C", 5),
        ]
        actual = tokenizer("A?B:C")

        self.assertListEqual(expected, actual)

    def test_chained_ternary(self):
        expected = [
            Token(TokenKind.IDENT, "A", 1),

            Token(TokenKind.AND, "&&", 2),
            Token(TokenKind.IDENT, "B", 4),

            Token(TokenKind.OR, "||", 5),
            Token(TokenKind.NOT, "!", 7),
            Token(TokenKind.IDENT, "C", 8),

            Token(TokenKind.TERNAY_IF, "?", 9),
            Token(TokenKind.IDENT, "D", 10)
        ]
        actual = tokenizer("A&&B||!C?D")

        self.assertListEqual(expected, actual)

    def test_ignore_whitespace(self):
        expected = [
            Token(TokenKind.IDENT, "A", 1),
            Token(TokenKind.TERNAY_IF, "?", 3),
            Token(TokenKind.IDENT, "B", 5),
            Token(TokenKind.TERNAY_ELSE, ":", 7),
            Token(TokenKind.IDENT, "C", 9),
        ]
        actual = tokenizer("A ? B : C")

        self.assertListEqual(expected, actual)

    def test_snake_case_ident(self):
        expected = [Token(TokenKind.IDENT, "UNDERSCORED_IDENT", 0)]
        actual = tokenizer("UNDERSCORED_IDENT")

        self.assertListEqual(expected, actual)

    def test_unrecognized_token(self):
        with self.assertRaises(ValueError):
            tokenizer("_IDENTS_CANNOT_START_WITH_AN_UNDERSCORE")
            tokenizer("+")


if __name__ == "__main__":
    unittest.main()
