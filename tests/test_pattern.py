import unittest

from pattern import ArgNum, ArgumentPattern, CommandPattern, Quantifier, parse_argument, parse_command_pattern


class TestArgumentPattern(unittest.TestCase):
    
    def test_parse_flag(self):
        content = "[VERBOSE?:--verbose,-v]"

        expected = ArgumentPattern("VERBOSE", ArgNum(Quantifier.N, 0), ["--verbose", "-v"], False, False)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_parse_single(self):
        content = "[DIR:-d,--dir]"

        expected = ArgumentPattern("DIR", ArgNum(Quantifier.N, 1), ["-d", "--dir"], False, False)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_parse_many(self):
        content = "[FIELDS...:-f,--fields]"

        expected = ArgumentPattern("FIELDS", ArgNum(Quantifier.Any), ["-f", "--fields"], False, False)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_positional_many(self):
        content = "<SRC...>"

        expected = ArgumentPattern("SRC", ArgNum(Quantifier.Any), list(), True, True)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_missing_var_name(self):
        content = "[--dir,-d]"

        expected = ArgumentPattern("DIR", ArgNum(Quantifier.N, 1), ["--dir", "-d"], False, False)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_positional_missing_var_name(self):
        content = "<...>"

        expected = ArgumentPattern(None, ArgNum(Quantifier.Any), list(), True, True)
        actual = parse_argument(content)

        self.assertEqual(expected, actual)

    def test_bad_braces(self):
        self.assertRaises(ValueError, parse_argument, ["[>"])
        self.assertRaises(ValueError, parse_argument, ["<]"])
        self.assertRaises(ValueError, parse_argument, ["<"])
        self.assertRaises(ValueError, parse_argument, ["]"])
        self.assertRaises(ValueError, parse_argument, ["I am not wrapped at all"])

    def test_bad_argument_name(self):
        self.assertRaises(ValueError, parse_argument, "<->")
        self.assertRaises(ValueError, parse_argument, "<-->")
        self.assertRaises(ValueError, parse_argument, "<-aa>")
        self.assertRaises(ValueError, parse_argument, "<--a--b>")
        self.assertRaises(ValueError, parse_argument, "<-a--a>")

    def test_bad_quantifier_value(self):
        self.assertRaises(ValueError, parse_argument, "<VAL-:>")
        self.assertRaises(ValueError, parse_argument, "<VAL[:>")
        self.assertRaises(ValueError, parse_argument, "<VAL--arg:>")
        self.assertRaises(ValueError, parse_argument, "<VAL>")


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
            ArgumentPattern("VERBOSE", ArgNum(Quantifier.N, 0), ["--verbose"], False, False)
        ])
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)

    def test_parse_positional(self):
        content = "test <SRC> <>"

        expected = CommandPattern("test", list(), [
            ArgumentPattern("SRC", ArgNum(Quantifier.N, 1), list(), True, True),
            ArgumentPattern(None, ArgNum(Quantifier.N, 1), list(), True, True),
        ])
        actual = parse_command_pattern(content)

        self.assertEqual(expected, actual)
