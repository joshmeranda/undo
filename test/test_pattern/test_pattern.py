import unittest

from undo.pattern import ArgNum, ArgumentPattern, ArgumentGroupPattern, CommandPattern, PatternError, Quantifier, \
    parse_argument_pattern, parse_argument_group_pattern, parse_commands, parse_command_pattern


class TestArgumentPattern(unittest.TestCase):

    def test_parse_flag(self):
        content = "[VERBOSE?:--verbose -v]"

        expected = ArgumentPattern("VERBOSE", ArgNum(Quantifier.N, 0), ["--verbose", "-v"], False, False, None), 23
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_single(self):
        content = "[DIR:-d --dir]"

        expected = ArgumentPattern("DIR", ArgNum(Quantifier.N, 1), ["-d", "--dir"], False, False, None), 14
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_any(self):
        content = "[FIELDS*:-f --fields]"

        expected = ArgumentPattern("FIELDS", ArgNum(Quantifier.ANY), ["-f", "--fields"], False, False, None), 21
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_positional_any(self):
        content = "<SRC*>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.ANY), list(), True, True, None), 6
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_at_least_one(self):
        content = "[FIELDS...:-f --fields]"

        expected = ArgumentPattern("FIELDS", ArgNum(Quantifier.AT_LEAST_ONE), ["-f", "--fields"], False, False, None), 23
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_missing_var_name(self):
        content = "[--dir -d]"

        expected = ArgumentPattern("DIR", ArgNum(Quantifier.N, 1), ["--dir", "-d"], False, False, None), 10
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_missing_var_name_with_dashes(self):
        content = "[?:--do-something]"

        expected = ArgumentPattern("DO_SOMETHING", ArgNum(Quantifier.N, 0), ["--do-something"], False, False, None), 18
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_positional_missing_var_name(self):
        content = "<...>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.AT_LEAST_ONE), list(), True, True, None), 5
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_optional_positional(self):
        content = "[]"

        with self.assertRaises(PatternError):
            parse_argument_pattern(content)

    def test_positional_optional_args(self):
        content = "<?>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.N, 0), list(), True, True, None), 3
        actual = parse_argument_pattern(content)

        self.assertEqual(actual, expected)

    def test_empty_delim(self):
        content = "<::>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.N, 1), list(), True, True, None), 4
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_colan_delim(self):
        content = "<SRC:::>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, ":"), 8
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_quadruple_colan_delim(self):
        content = "<SRC::::::>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, "::::"), 11
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_comma_delim(self):
        content = "<SRC:,:-s --src>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), ["-s", "--src"], False, True, ","), 16
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_bad_braces(self):
        with self.assertRaises(PatternError):
            parse_argument_pattern("[>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<]")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<")

        with self.assertRaises(PatternError):
            parse_argument_pattern("]")

        with self.assertRaises(PatternError):
            parse_argument_pattern("I am not wrapped at all")

    def test_bad_argument_name(self):
        with self.assertRaises(PatternError):
            parse_argument_pattern("<->")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<-->")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<-aa>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<--a--b>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<-a--a>")

    def test_bad_quantifier_value(self):
        with self.assertRaises(PatternError):
            parse_argument_pattern("<VAL-:>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<VAL-:>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<VAL[:>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<VAL--arg:>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<VAL :>")


class TestArgumentGroupPattern(unittest.TestCase):

    def test_parse_optional(self):
        content = "([?:--interactive] [?:--no-clobber])"

        expected = ArgumentGroupPattern(False, [
            ArgumentPattern("INTERACTIVE", ArgNum(Quantifier.N, 0), ["--interactive"], False, False, None),
            ArgumentPattern("NO_CLOBBER", ArgNum(Quantifier.N, 0), ["--no-clobber"], False, False, None),
        ]), 36
        actual = parse_argument_group_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_required(self):
        content = "(![?:--interactive] [?:--no-clobber])"

        expected = ArgumentGroupPattern(True, [
            ArgumentPattern("INTERACTIVE", ArgNum(Quantifier.N, 0), ["--interactive"], False, False, None),
            ArgumentPattern("NO_CLOBBER", ArgNum(Quantifier.N, 0), ["--no-clobber"], False, False, None),
        ]), 37
        actual = parse_argument_group_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_bad_argument(self):
        content = "(a [?:--interactive])"

        with self.assertRaises(PatternError):
            parse_argument_group_pattern(content)


class TestParseCommands(unittest.TestCase):
    def test_only_command(self):
        expected = "test", list(), 4
        actual = parse_commands("test")

        self.assertEqual(expected, actual)

    def test_leading_spaces(self):
        expected = "test", list(), 6
        actual = parse_commands("  test")

        self.assertEqual(expected, actual)

    def test_trailing_spaces(self):
        expected = "test", list(), 6
        actual = parse_commands("test  ")

        self.assertEqual(expected, actual)

    def test_command_with_sub_commands(self):
        content = "test one two"

        expected = "test", ["one", "two"], 12
        actual = parse_commands(content)

        self.assertEqual(expected, actual)

    def test_point_to_arg(self):
        content = "test one two <ARG>"

        expected = "test", ["one", "two"], 13
        actual = parse_commands(content)

        self.assertEqual(expected, actual)


class TestCommandPattern(unittest.TestCase):

    def test_parse_no_arguments(self):
        content = "test"

        expected = CommandPattern("test", list(), list(), list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_sub_commands(self):
        content = "test one two"

        expected = CommandPattern("test", ["one", "two"], list(), list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_arguments(self):
        content = "test [?:--verbose]"

        expected = CommandPattern("test", list(), [
            ArgumentPattern("VERBOSE", ArgNum(Quantifier.N, 0), ["--verbose"], False, False, None)
        ], list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_positional(self):
        content = "test <SRC>"

        expected = CommandPattern("test", list(), [
            ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, None),
        ], list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_multiple_arguments(self):
        content = "test [?:-v --verbose] <SRC>"

        expected = CommandPattern("test", list(), [
            ArgumentPattern("VERBOSE", ArgNum(Quantifier.N, 0), ["-v", "--verbose"], False, False, None),
            ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, None),
        ], list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_argument_group(self):
        content = "test ([?:--interactive] [?:--no-clobber])"

        expected = CommandPattern("test", list(), list(), [
            ArgumentGroupPattern(False, [
                ArgumentPattern("INTERACTIVE", ArgNum(Quantifier.N, 0), ["--interactive"], False, False, None),
                ArgumentPattern("NO_CLOBBER", ArgNum(Quantifier.N, 0), ["--no-clobber"], False, False, None),
            ])
        ])
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_with_unexpected_character(self):
        content = "cp {[?:--interactive]}"

        with self.assertRaises(PatternError):
            parse_command_pattern(content)


if __name__ == "__main__":
    unittest.main()
