import unittest
from expression import *
import expression


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tokenization Tests                                                          #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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
            Token(TokenKind.TERNARY_IF, "?", 2),
            Token(TokenKind.IDENT, "B", 3),
            Token(TokenKind.TERNARY_ELSE, ":", 4),
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

            Token(TokenKind.TERNARY_IF, "?", 9),
            Token(TokenKind.IDENT, "D", 10)
        ]
        actual = tokenize("A&&B||!C?D")

        self.assertListEqual(expected, actual)

    def test_ignore_whitespace(self):
        expected = [
            Token(TokenKind.IDENT, "A", 1),
            Token(TokenKind.TERNARY_IF, "?", 3),
            Token(TokenKind.IDENT, "B", 5),
            Token(TokenKind.TERNARY_ELSE, ":", 7),
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

    def test_tokenize_command(self):
        self.assertEqual([Token(TokenKind.COMMAND, "dirname", 1)], tokenize("dirname"))
        self.assertEqual([Token(TokenKind.COMMAND, "basename", 1)], tokenize("basename"))
        self.assertEqual([Token(TokenKind.COMMAND, "abspath", 1)], tokenize("abspath"))
        self.assertEqual([Token(TokenKind.COMMAND, "env", 1)], tokenize("env"))
        self.assertEqual([Token(TokenKind.COMMAND, "exists", 1)], tokenize("exists"))
        self.assertEqual([Token(TokenKind.COMMAND, "isfile", 1)], tokenize("isfile"))
        self.assertEqual([Token(TokenKind.COMMAND, "isdir", 1)], tokenize("isdir"))

    def test_unrecognized_token(self):
        with self.assertRaises(ExpressionError):
            tokenize("_IDENTS_CANNOT_START_WITH_AN_UNDERSCORE")

        with self.assertRaises(ExpressionError):
            tokenize("+")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Parsing Tests                                                               #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


parse_value_tokens = expression.__parse_value_expression_tokens
parse_conditional_tokens = expression.__parse_conditional_expression_tokens


class TestParseValue(unittest.TestCase):
    def test_identifier_expression(self):
        tokens = [
            Token(TokenKind.IDENT, "A", 0),
        ]

        expected = IdentifierExpression(Token(TokenKind.IDENT, "A", 0))
        actual, offset = parse_value_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(1, offset)

    def test_value_command_expression(self):
        command = Token(TokenKind.COMMAND, "basename", 0)
        argument = Token(TokenKind.IDENT, "/some/path", 0)

        tokens = [
            Token(TokenKind.TICK, '`', 0),
            command,
            argument,
            Token(TokenKind.TICK, '`', 0),
        ]

        expected = ValueCommandExpression(command, argument)
        actual, offset = parse_value_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(4, offset)

    def test_ternary_expression(self):
        tokens = [
            Token(TokenKind.IDENT, "A", 0),

            Token(TokenKind.TERNARY_IF, "?", 0),
            Token(TokenKind.IDENT, "B", 0),

            Token(TokenKind.TERNARY_ELSE, ":", 0),
            Token(TokenKind.IDENT, "C", 0),
        ]

        expected = TernaryExpression(
            ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "A", 0))),
            IdentifierExpression(Token(TokenKind.IDENT, "B", 0)),
            IdentifierExpression(Token(TokenKind.IDENT, "C", 0)))

        actual, _ = parse_value_tokens(tokens)

        self.assertEqual(expected, actual)

    def test_unexpected_tokens(self):
        with self.assertRaises(ParseError):
            parse_value_tokens([
                Token(TokenKind.AND, "&&", 0)
            ])

            parse_value_tokens([
                Token(TokenKind.OR, "||", 0)
            ])

            parse_value_tokens([
                Token(TokenKind.TERNARY_IF, "?", 0)
            ])

            parse_value_tokens([
                Token(TokenKind.TERNARY_ELSE, ":", 0)
            ])


class TestParseConditionalExpression(unittest.TestCase):
    def test_existence_expression(self):
        tokens = [
            Token(TokenKind.IDENT, "A", 0),
        ]

        expected = ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "A", 0)))
        actual, offset = parse_conditional_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(1, offset)

    def test_conditional_command_expression(self):
        command = Token(TokenKind.COMMAND, "exists", 0)
        argument = Token(TokenKind.IDENT, "/some/path", 0)

        tokens = [
            Token(TokenKind.TICK, '`', 0),
            command,
            argument,
            Token(TokenKind.TICK, '`', 0),
        ]

        expected = ConditionalCommandExpression(False, command, argument)
        actual, offset = parse_conditional_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(4, offset)

    def test_chain_conditional(self):
        tokens = [
            Token(TokenKind.NOT, "!", 0),
            Token(TokenKind.IDENT, "A", 0),
            Token(TokenKind.AND, "&&", 0),
            Token(TokenKind.IDENT, "B", 0),
        ]

        expected = ExistenceExpression(True, IdentifierExpression(Token(TokenKind.IDENT, "A", 0)),
                                       operator=Token(TokenKind.AND, "&&", 0),
                                       right=ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "B", 0))))
        actual, offset = parse_conditional_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(4, offset)


parse_identifier_tokens = expression.__parse_identifier_expression_tokens
parse_ternary_tokens = expression.__parse_ternary_expression_tokens
parse_existence_tokens = expression.__parse_existence_expression_tokens

parse_value_command_tokens = expression.__parse_value_command_expression_tokens
parse_conditional_command_tokens = expression.__parse_conditional_command_expression_tokens


class TestParseIdentifierTokens(unittest.TestCase):
    def test_basic(self):
        tokens = [
            Token(TokenKind.IDENT, "A", 0)
        ]

        expected = IdentifierExpression(tokens[0])
        actual, offset = parse_identifier_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(1, offset)

    def test_unexpected_token(self):
        for kind in list(TokenKind):
            if kind != TokenKind.IDENT:
                with self.assertRaises(ParseError):
                    parse_identifier_tokens([Token(kind, "", 0)])


class TestParseTernaryExpressionTokens(unittest.TestCase):
    def test_basic_full_ternary(self):
        tokens = [
            Token(TokenKind.IDENT, "A", 0),

            Token(TokenKind.TERNARY_IF, "?", 0),
            Token(TokenKind.IDENT, "B", 0),

            Token(TokenKind.TERNARY_ELSE, ":", 0),
            Token(TokenKind.IDENT, "C", 0),
        ]

        expected = TernaryExpression(
            ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "A", 0))),
            IdentifierExpression(Token(TokenKind.IDENT, "B", 0)),
            IdentifierExpression(Token(TokenKind.IDENT, "C", 0)))

        actual, offset = parse_ternary_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(5, offset)

    def test_basic_abbreviated_ternary(self):
        tokens = [
            Token(TokenKind.IDENT, "A", 0),

            Token(TokenKind.TERNARY_IF, "?", 0),
            Token(TokenKind.IDENT, "B", 0),
        ]

        expected = TernaryExpression(
            ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "A", 0))),
            IdentifierExpression(Token(TokenKind.IDENT, "B", 0)),
            None)
        actual, offset = parse_ternary_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(3, offset)

    def test_complex_conditional(self):
        tokens = [
            Token(TokenKind.NOT, "!", 0),
            Token(TokenKind.IDENT, "A", 0),
            Token(TokenKind.AND, "&&", 0),
            Token(TokenKind.IDENT, "B", 0),

            Token(TokenKind.TERNARY_IF, "?", 0),
            Token(TokenKind.IDENT, "B", 0),
        ]

        expected = TernaryExpression(
            ExistenceExpression(True, IdentifierExpression(Token(TokenKind.IDENT, "A", 0)),
                                operator=Token(TokenKind.AND, "&&", 0), right=ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "B", 0)))),
            IdentifierExpression(Token(TokenKind.IDENT, "B", 0)),
            None)
        actual, offset = parse_ternary_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(6, offset)

    @unittest.skip("string literals not yet implemented")
    def test_nested_ternary(self):
        tokens = [
            Token(TokenKind.IDENT, "A", 0),
            Token(TokenKind.TERNARY_IF, "?", 0),

            # nested ternary
            Token(TokenKind.IDENT, "B", 0),
            Token(TokenKind.TERNARY_IF, "?", 0),
            Token(TokenKind.IDENT, "B", 0),

            Token(TokenKind.TERNARY_ELSE, ":", 0),
            Token(TokenKind.IDENT, "C", 0),
        ]

        expected = TernaryExpression(
            ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "A", 0))),
            TernaryExpression(
                ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "B", 0))),
                IdentifierExpression(Token(TokenKind.IDENT, "B", 0)),
                None),
            IdentifierExpression(Token(TokenKind.IDENT, "C", 0)))
        actual, offset = parse_ternary_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(8, offset)


class TestParseExistenceTokens(unittest.TestCase):
    def parse_basic(self):
        tokens = [
            Token(TokenKind.IDENT, "A", 0)
        ]

        expected = ExistenceExpression(
            False, IdentifierExpression(Token(TokenKind.IDENT, "A", 0))
        )
        actual, offset = parse_existence_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(1, offset)

    def parse_basic_negate(self):
        tokens = [
            Token(TokenKind.NOT, "!", 0),
            Token(TokenKind.IDENT, "A", 0),
        ]

        expected = ExistenceExpression(
            True, IdentifierExpression(Token(TokenKind.IDENT, "A", 0))
        )
        actual, offset = parse_existence_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(1, offset)

    def test_unexpected_token(self):
        for kind in list(TokenKind):
            if kind != TokenKind.IDENT:
                with self.assertRaises(ParseError):
                    parse_identifier_tokens([Token(kind, "", 0)])


class TestParseCommandExpressionTokens(unittest.TestCase):
    def test_parse_basic(self):
        tokens = [
            Token(TokenKind.TICK, "`", 0),
            Token(TokenKind.COMMAND, "dirname", 0),
            Token(TokenKind.IDENT, "A", 0),
            Token(TokenKind.TICK, "`", 0),
        ]

        expected = ValueCommandExpression(
            Token(TokenKind.COMMAND, "dirname", 0),
            Token(TokenKind.IDENT, "A", 0))
        actual, offset = parse_value_command_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(4, offset)

    def test_unexpected_token(self):
        for kind in list(TokenKind):
            if kind != TokenKind.TICK:
                with self.assertRaises(ParseError):
                    parse_value_command_tokens([
                        Token(kind, "", 0)
                    ])

            if kind != TokenKind.COMMAND:
                with self.assertRaises(ParseError):
                    parse_value_command_tokens([
                        Token(TokenKind.TICK, "`", 0),
                        Token(kind, "", 0)
                    ])


class TestParseConditionalCommandExpressionTokens(unittest.TestCase):
    def test_parse_basic_not(self):
        tokens = [
            Token(TokenKind.NOT, "!", 0),
            Token(TokenKind.TICK, "`", 0),
            Token(TokenKind.COMMAND, "isfile", 0),
            Token(TokenKind.IDENT, "A", 0),
            Token(TokenKind.TICK, "`", 0),
        ]

        expected = ConditionalCommandExpression(
            True,
            Token(TokenKind.COMMAND, "isfile", 0),
            Token(TokenKind.IDENT, "A", 0))
        actual, offset = parse_conditional_command_tokens(tokens)

        self.assertEqual(expected, actual)
        self.assertEqual(5, offset)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Expression Tests                                                            #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TestIdentifierExpression(unittest.TestCase):
    def setUp(self) -> None:
        self.env = {
            "A": "some_value"
        }

    def test_exists(self):
        expr = IdentifierExpression(Token(TokenKind.IDENT, "A", 0))

        expected = "some_value"
        actual = expr.evaluate(self.env)

        self.assertEqual(expected, actual)

    def test_does_not_exist(self):
        expr = IdentifierExpression(Token(TokenKind.IDENT, "DOES_NOT_EXIST", 0))

        expected = ""
        actual = expr.evaluate(self.env)

        self.assertEqual(expected, actual)


class TestTernaryExpression(unittest.TestCase):
    class YesManConditional(ConditionalExpression):
        def __init__(self):
            super().__init__(False, None, None)
        
        def evaluate(self, env: dict[str, str]) -> bool:
            return True

    class NoManConditional(ConditionalExpression):
        def __init__(self):
            super().__init__(False, None, None)

        def evaluate(self, env: dict[str, str]) -> bool:
            return False

    class EchoValueExpression(ValueExpression):
        def __init__(self, val: str):
            self.val = val

        def evaluate(self, env: dict[str, str]) -> str:
            return self.val

    def test_basic_full_true(self):
        expr = TernaryExpression(
            self.YesManConditional(),
            self.EchoValueExpression("some_value"),
            self.EchoValueExpression("some_other_value"),)

        expected = "some_value"
        actual = expr.evaluate(dict())

        self.assertEqual(expected, actual)

    def test_basic_full_false(self):
        expr = TernaryExpression(
            self.NoManConditional(),
            self.EchoValueExpression("some_value"),
            self.EchoValueExpression("some_other_value"),
        )

        expected = "some_other_value"
        actual = expr.evaluate(dict())

        self.assertEqual(expected, actual)

    def test_basic_abbrev_true(self):
        expr = TernaryExpression(
            self.YesManConditional(),
            self.EchoValueExpression("some_value"),
            None)

        expected = "some_value"
        actual = expr.evaluate(dict())

        self.assertEqual(expected, actual)

    def test_basic_abbrev_false(self):
        expr = TernaryExpression(
            self.NoManConditional(),
            self.EchoValueExpression("some_value"),
            None)

        expected = ""
        actual = expr.evaluate(dict())

        self.assertEqual(expected, actual)


class TestExistenceExpression(unittest.TestCase):
    def setUp(self):
        self.env = {
            "A": "some_value"
        }

    def test_exists(self):
        expr = ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "A", 0)))

        self.assertTrue(expr.evaluate(self.env))

    def test_exists_negate(self):
        expr = ExistenceExpression(True, IdentifierExpression(Token(TokenKind.IDENT, "A", 0)))

        self.assertFalse(expr.evaluate(self.env))

    def test_does_not_exist(self):
        expr = ExistenceExpression(False, IdentifierExpression(Token(TokenKind.IDENT, "DOES_NOT_EXIST", 0)))

        self.assertFalse(expr.evaluate(self.env))

    def test_does_not_exist_negate(self):
        expr = ExistenceExpression(True, IdentifierExpression(Token(TokenKind.IDENT, "DOES_NOT_EXIST", 0)))

        self.assertTrue(expr.evaluate(self.env))


class TestValueCommandExpression(unittest.TestCase):
    def test_dirname(self):
        expr = ValueCommandExpression(
            Token(TokenKind.IDENT, "dirname", 0),
            Token(TokenKind.IDENT, "/some/dir/and_a_file", 0))

        expected = "/some/dir"
        actual = expr.evaluate(dict())

        self.assertEqual(expected, actual)

    def test_basename(self):
        expr = ValueCommandExpression(
            Token(TokenKind.IDENT, "basename", 0),
            Token(TokenKind.IDENT, "/some/path/to/a/file", 0))

        expected = "file"
        actual = expr.evaluate(dict())

        self.assertEqual(expected, actual)

    def test_abspath(self):
        cwd = os.getcwd()
        basename = "file"

        expr = ValueCommandExpression(
            Token(TokenKind.IDENT, "abspath", 0),
            Token(TokenKind.IDENT, basename, 0))

        expected = os.path.join(cwd, basename)
        actual = expr.evaluate(dict())

        self.assertEqual(expected, actual)

    def test_env(self):
        env_var = self.id()
        env_var_value = "SET"

        os.environ[env_var] = env_var_value
        self.addCleanup(lambda: os.unsetenv(env_var))

        expr = ValueCommandExpression(
            Token(TokenKind.IDENT, "env", 0),
            Token(TokenKind.IDENT, env_var, 0))

        expected = env_var_value
        actual = expr.evaluate(dict())

        self.assertEqual(expected, actual)

    def test_unknown_command(self):
        expr = ValueCommandExpression(
            Token(TokenKind.IDENT, "unknown_commnd", 0),
            Token(TokenKind.IDENT, "arg", 0))

        with self.assertRaises(UnknownCommandException):
            expr.evaluate(dict())


class TestConditionalCommandExpression(unittest.TestCase):
    def test_exists(self):
        expr = ConditionalCommandExpression(
            False,
            Token(TokenKind.IDENT, "exists", 0),
            Token(TokenKind.IDENT, __file__, 0))

        self.assertTrue(expr.evaluate(dict()))

        expr.negate = True

        self.assertFalse(expr.evaluate(dict()))

    def test_isfile(self):
        expr = ConditionalCommandExpression(
            False,
            Token(TokenKind.IDENT, "isfile", 0),
            Token(TokenKind.IDENT, __file__, 0))

        self.assertTrue(expr.evaluate(dict()))

        expr.negate = True

        self.assertFalse(expr.evaluate(dict()))

    def test_isdir(self):
        expr = ConditionalCommandExpression(
            False,
            Token(TokenKind.IDENT, "isdir", 0),
            Token(TokenKind.IDENT, os.path.dirname(__file__), 0))

        self.assertTrue(expr.evaluate(dict()))

        expr.negate = True

        self.assertFalse(expr.evaluate(dict()))

    def test_unknown_command(self):
        expr = ConditionalCommandExpression(
            False,
            Token(TokenKind.IDENT, "unknown_commnd", 0),
            Token(TokenKind.IDENT, "arg", 0))

        with self.assertRaises(UnknownCommandException):
            expr.evaluate(dict())


if __name__ == "__main__":
    unittest.main()
