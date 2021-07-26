import unittest
from expression import *
import expression

tokenize = expression.__tokenize

parse_tokens = expression.__parse_tokens


class TestTokenize(unittest.TestCase):
    def test_tokenize_empty(self):
        expected = list()
        actual = tokenize("")

        self.assertListEqual(expected, actual)

    def test_single_ident(self):
        expected = [
            Token(TokenKind.IDENT, "A", 1)
        ]
        actual = tokenize("A")

        self.assertListEqual(expected, actual)

    def test_basic_ternary(self):
        expected = [
            Token(TokenKind.IDENT, "A", 1),
            Token(TokenKind.TERNAY_IF, "?", 2),
            Token(TokenKind.IDENT, "B", 3),
            Token(TokenKind.TERNAY_ELSE, ":", 4),
            Token(TokenKind.IDENT, "C", 5),
        ]
        actual = tokenize("A?B:C")

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
        actual = tokenize("A&&B||!C?D")

        self.assertListEqual(expected, actual)

    def test_ignore_whitespace(self):
        expected = [
            Token(TokenKind.IDENT, "A", 1),
            Token(TokenKind.TERNAY_IF, "?", 3),
            Token(TokenKind.IDENT, "B", 5),
            Token(TokenKind.TERNAY_ELSE, ":", 7),
            Token(TokenKind.IDENT, "C", 9),
        ]
        actual = tokenize("A ? B : C")

        self.assertListEqual(expected, actual)

    def test_snake_case_ident(self):
        expected = [
            Token(TokenKind.IDENT, "UNDERSCORED_IDENT", 1)
        ]
        actual = tokenize("UNDERSCORED_IDENT")

        self.assertListEqual(expected, actual)

    def test_unrecognized_token(self):
        with self.assertRaises(ExpressionError):
            tokenize("_IDENTS_CANNOT_START_WITH_AN_UNDERSCORE")
            tokenize("+")


class TestParseIdentifierTokens(unittest.TestCase):
    pass


class TestParseTernaryExpressionTokens(unittest.TestCase):
    pass


class TestParseValueCommandExpressionTokens(unittest.TestCase):
    pass


class TestParseConditionalCommandExpressionTokens(unittest.TestCase):
    pass


class TestParseExistenceTokens(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
