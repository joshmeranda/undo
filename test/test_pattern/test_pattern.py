import unittest

from undo.pattern import ArgNum, ArgumentPattern, CommandPattern, Quantifier, parse_argument, parse_command_pattern


class TestArgumentPattern(unittest.TestCase):

    def test_parse_flag(self):
        content = "[VERBOSE?:--verbose,-v]"

        expected = ArgumentPattern("VERBOSE", ArgNum(Quantifier.N, 0), ["--verbose", "-v"], False, False, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_parse_single(self):
        content = "[DIR:-d,--dir]"

        expected = ArgumentPattern("DIR", ArgNum(Quantifier.N, 1), ["-d", "--dir"], False, False, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_parse_any(self):
        content = "[FIELDS*:-f,--fields]"

        expected = ArgumentPattern("FIELDS", ArgNum(Quantifier.ANY), ["-f", "--fields"], False, False, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_positional_any(self):
        content = "<SRC*>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.ANY), list(), True, True, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_parse_at_least_one(self):
        content = "[FIELDS...:-f,--fields]"

        expected = ArgumentPattern("FIELDS", ArgNum(Quantifier.AT_LEAST_ONE), ["-f", "--fields"], False, False, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_missing_var_name(self):
        content = "[--dir,-d]"

        expected = ArgumentPattern("DIR", ArgNum(Quantifier.N, 1), ["--dir", "-d"], False, False, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_missing_var_name_with_dashes(self):
        content = "[?:--do-something]"

        expected = ArgumentPattern("DO_SOMETHING", ArgNum(Quantifier.N, 0), ["--do-something"], False, False, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_positional_missing_var_name(self):
        content = "<...>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.AT_LEAST_ONE), list(), True, True, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_optional_positional(self):
        content = "[]"

        with self.assertRaises(ValueError):
            parse_argument(content)

    def test_positional_optional_args(self):
        content = "<?>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.N, 0), list(), True, True, None)
        actual = parse_argument(content)

        self.assertEqual(actual, expected)

    def test_empty_delim(self):
        content = "<::>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.N, 1), list(), True, True, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_colan_delim(self):
        content = "<SRC:::>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, ":")
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_quadruple_colan_delim(self):
        content = "<SRC::::::>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, "::::")
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_comma_delim(self):
        content = "<SRC:,:-s,--src>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), ["-s", "--src"], False, True, ",")
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_bad_braces(self):
        with self.assertRaises(ValueError):
            parse_argument("[>")

        with self.assertRaises(ValueError):
            parse_argument("<]")

        with self.assertRaises(ValueError):
            parse_argument("<")

        with self.assertRaises(ValueError):
            parse_argument("]")

        with self.assertRaises(ValueError):
            parse_argument("I am not wrapped at all")

    def test_bad_argument_name(self):
        with self.assertRaises(ValueError):
            parse_argument("<->")

        with self.assertRaises(ValueError):
            parse_argument("<-->")

        with self.assertRaises(ValueError):
            parse_argument("<-aa>")

        with self.assertRaises(ValueError):
            parse_argument("<--a--b>")

        with self.assertRaises(ValueError):
            parse_argument("<-a--a>")

    def test_bad_quantifier_value(self):
        with self.assertRaises(ValueError):
            parse_argument("<VAL-:>")

        with self.assertRaises(ValueError):
            parse_argument("<VAL-:>")

        with self.assertRaises(ValueError):
            parse_argument("<VAL[:>")

        with self.assertRaises(ValueError):
            parse_argument("<VAL--arg:>")

        with self.assertRaises(ValueError):
            parse_argument("<VAL :>")

    def test_ignore_empty_names(self):
        content = "<,>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.N, 1), list(), True, True, None)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)


class TestCommandPattern(unittest.TestCase):

    def test_parse_no_arguments(self):
        content = "test"

        expected = CommandPattern("test", list(), list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_sub_commands(self):
        content = "test one two"

        expected = CommandPattern("test", ["one", "two"], list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_arguments(self):
        content = "test [?:--verbose]"

        expected = CommandPattern("test", list(), [
            ArgumentPattern("VERBOSE", ArgNum(Quantifier.N, 0), ["--verbose"], False, False, None)
        ])
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_positional(self):
        content = "test <SRC> <>"

        expected = CommandPattern("test", list(), [
            ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, None),
            ArgumentPattern(None, ArgNum(Quantifier.N, 1), list(), True, True, None),
        ])
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
