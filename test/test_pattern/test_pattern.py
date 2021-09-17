import unittest

from undo.pattern import ArgNum, ArgumentPattern, ArgumentGroupPattern, CommandPattern, PatternError, Quantifier, \
    parse_argument_pattern, parse_argument_group_pattern, parse_commands, parse_command_pattern


class TestArgumentPattern(unittest.TestCase):

    def test_parse_flag(self):
        content = "[-v --verbose [VERBOSE]]"

        expected = ArgumentPattern("VERBOSE", ArgNum(Quantifier.FLAG, ), ["-v", "--verbose"], False, False, None), \
                   len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_flag_no_name(self):
        content = "[-v --verbose]"

        expected = ArgumentPattern("VERBOSE", ArgNum(Quantifier.FLAG, ), ["-v", "--verbose"], False, False, None), \
                   len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_required_flag_no_name(self):
        content = "<-v --verbose>"

        expected = ArgumentPattern("VERBOSE", ArgNum(Quantifier.FLAG, ), ["-v", "--verbose"], False, True, None), \
                   len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_single(self):
        content = "[-d --dir=DIR]"

        expected = ArgumentPattern("DIR", ArgNum(Quantifier.N, 1), ["-d", "--dir"], False, False, None), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_any(self):
        content = "[-f --fields=FIELDS*]"

        expected = ArgumentPattern("FIELDS", ArgNum(Quantifier.ANY), ["-f", "--fields"], False, False, None), \
                   len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_positional_any(self):
        content = "<SRC*>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.ANY), list(), True, True, None), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_positional_one(self):
        content = "<SRC>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, None), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_at_least_one(self):
        content = "[-f --fields=FIELDS...]"

        expected = ArgumentPattern("FIELDS", ArgNum(Quantifier.AT_LEAST_ONE), ["-f", "--fields"], False, False, None), \
                   len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_n_args(self):
        content = "[-2 --two=TWO{2}]"

        expected = ArgumentPattern("TWO", ArgNum(Quantifier.N, 2), ["-2", "--two"], False, False, None), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_optional_arg(self):
        content = "[--optional[=OPTIONAL]]"

        expected = ArgumentPattern("OPTIONAL", ArgNum(Quantifier.OPTIONAL), ["--optional"], False, False, None), len(content)
        actual = parse_argument_pattern(content)

        return self.assertEqual(expected, actual)

    def test_missing_var_name(self):
        content = "[-d --dir=]"

        expected = ArgumentPattern("DIR", ArgNum(Quantifier.N, 1), ["-d", "--dir"], False, False, None), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_positional_missing_var_name(self):
        content = "<...>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.AT_LEAST_ONE), list(), True, True, None), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_optional_positional(self):
        content = "[]"

        with self.assertRaises(PatternError):
            parse_argument_pattern(content)

    def test_positional_optional_args(self):
        content = "<[...]>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.ANY), list(), True, True, None), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_empty_delim(self):
        content = "<--number =NUMBER:>"

        expected = ArgumentPattern("NUMBER", ArgNum(Quantifier.N, 1), ["--number"], False, True, None), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_colan_delim(self):
        content = "<--number =NUMBER::>"

        expected = ArgumentPattern("NUMBER", ArgNum(Quantifier.N, 1), ["--number"], False, True, ":"), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_quadruple_colan_delim(self):
        content = "<--number =NUMBER:::::>"

        expected = ArgumentPattern("NUMBER", ArgNum(Quantifier.N, 1), ["--number"], False, True, "::::"), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_comma_delim(self):
        content = "<-s --src=:,>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), ["-s", "--src"], False, True, ","), len(content)
        actual = parse_argument_pattern(content)

        self.assertEqual(expected, actual)

    def test_missing_var_description(self):
        with self.assertRaises(PatternError):
            parse_argument_pattern("[--src:,]")

    def test_missing_closing_var_brace(self):
        content = "[--number[=NUMBER]"

        with self.assertRaises(PatternError):
            parse_argument_pattern(content)

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

    def test_missing_var_delimiter(self):
        with self.assertRaises(PatternError):
            parse_argument_pattern("[--number NUMBER]")

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

        with self.assertRaises(PatternError):
            parse_argument_pattern("[-a Z]")

    def test_bad_quantifier_value(self):
        with self.assertRaises(PatternError):
            parse_argument_pattern("<{}>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<{}>")

        with self.assertRaises(PatternError):
            parse_argument_pattern("<..>")

    def test_bad_optional_values(self):
        with self.assertRaises(PatternError):
            parse_argument_pattern("[-n[=N{2}]]")

        with self.assertRaises(PatternError):
            parse_argument_pattern("[--at-least-one [=AT_LEAST_ONE...]")


class TestArgumentGroupPattern(unittest.TestCase):

    def test_parse_optional(self):
        content = "([--interactive] [--no-clobber])"

        expected = ArgumentGroupPattern(False, [
            ArgumentPattern("INTERACTIVE", ArgNum(Quantifier.FLAG), ["--interactive"], False, False, None),
            ArgumentPattern("NO_CLOBBER", ArgNum(Quantifier.FLAG), ["--no-clobber"], False, False, None),
        ]), len(content)
        actual = parse_argument_group_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_required(self):
        content = "(![--interactive] [--no-clobber])"

        expected = ArgumentGroupPattern(True, [
            ArgumentPattern("INTERACTIVE", ArgNum(Quantifier.FLAG), ["--interactive"], False, False, None),
            ArgumentPattern("NO_CLOBBER", ArgNum(Quantifier.FLAG), ["--no-clobber"], False, False, None),
        ]), len(content)
        actual = parse_argument_group_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_bad_argument(self):
        content = "(a [--interactive])"

        with self.assertRaises(PatternError):
            parse_argument_group_pattern(content)

    def test_parse_optional_argument_value(self):
        content = "([--number[=N]])"

        expected = ArgumentGroupPattern(False, [
            ArgumentPattern("N", ArgNum(Quantifier.OPTIONAL), ["--number"], False, False, None)
        ]), len(content)
        actual = parse_argument_group_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_multiple_with_optional(self):
        content = "([--number[=N]] [--verbose])"

        expected = ArgumentGroupPattern(False, [
            ArgumentPattern("N", ArgNum(Quantifier.OPTIONAL), ["--number"], False, False, None),
            ArgumentPattern("VERBOSE", ArgNum(Quantifier.FLAG), ["--verbose"], False, False, None),
        ]), len(content)
        actual = parse_argument_group_pattern(content)

        self.assertEqual(expected, actual)


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
        content = "test [--verbose]"

        expected = CommandPattern("test", list(), [
            ArgumentPattern("VERBOSE", ArgNum(Quantifier.FLAG), ["--verbose"], False, False, None)
        ], list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_arg_with_optional_val(self):
        content = "test [--backup[=CONTROL]]" \
                  ""
        expected = CommandPattern("test", list(), [
            ArgumentPattern("CONTROL", ArgNum(Quantifier.OPTIONAL), ["--backup"], False, False, None)
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
        content = "test [-v --verbose] <SRC>"

        expected = CommandPattern("test", list(), [
            ArgumentPattern("VERBOSE", ArgNum(Quantifier.FLAG), ["-v", "--verbose"], False, False, None),
            ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True, None),
        ], list())
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_argument_group(self):
        content = "test ([--interactive] [--no-clobber])"

        expected = CommandPattern("test", list(), list(), [
            ArgumentGroupPattern(False, [
                ArgumentPattern("INTERACTIVE", ArgNum(Quantifier.FLAG), ["--interactive"], False, False, None),
                ArgumentPattern("NO_CLOBBER", ArgNum(Quantifier.FLAG), ["--no-clobber"], False, False, None),
            ])
        ])
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_with_unexpected_character(self):
        content = "cp {[--interactive]}"

        with self.assertRaises(PatternError):
            parse_command_pattern(content)


if __name__ == "__main__":
    unittest.main()
