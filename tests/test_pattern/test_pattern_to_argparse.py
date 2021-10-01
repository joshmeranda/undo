import argparse
import unittest

from undo.pattern import CommandPattern, pattern_to_argparse, ArgumentPattern, ArgNum, Quantifier, ArgumentGroupPattern


class TestPatternToArgparse(unittest.TestCase):
    def test_basic(self):
        pattern = CommandPattern("test", list(), list(), list())
        parser = pattern_to_argparse(pattern)

        parser.parse_args([])

        namespace = parser.parse_args([])
        self.assertEqual(argparse.Namespace(), namespace)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["--verbose"])

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["some", "positional", "args"])

    def test_sub_command(self):
        pattern = CommandPattern("test", ["one"], list(), list())
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args([])

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["one", "three"])

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["two"])

        expected = argparse.Namespace(command="one")
        actual = parser.parse_args(["one"])

        self.assertEqual(expected, actual)

    def test_nested_sub_commands(self):
        pattern = CommandPattern("test", ["one", "two"], list(), list())
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args([])

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["one"])

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["one", "three"])

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["two"])

        expected = argparse.Namespace(command="two")
        actual = parser.parse_args("one two".split())

        self.assertEqual(expected, actual)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Required Testing                                                        #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_optional_arg(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("VAL", ArgNum(Quantifier.N, 1), ["-V", "--val"], False, False, None)
        ], list())
        parser = pattern_to_argparse(pattern)

        namespace = parser.parse_args([])
        self.assertEqual(argparse.Namespace(VAL=None), namespace)

        namespace = parser.parse_args(["-V", "value"])
        self.assertEqual(argparse.Namespace(VAL="value"), namespace)

        namespace = parser.parse_args(["--val", "value"])
        self.assertEqual(argparse.Namespace(VAL="value"), namespace)

    def test_required_arg(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("VAL", ArgNum(Quantifier.N, 1), ["-V", "--val"], False, True, None)
        ], list())
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_known_args([])

        namespace = parser.parse_args(["-V", "value"])
        self.assertEqual(argparse.Namespace(VAL="value"), namespace)

        namespace = parser.parse_args(["--val", "value"])
        self.assertEqual(argparse.Namespace(VAL="value"), namespace)

    def test_arg_group_optional(self):
        pattern = CommandPattern("test", list(), list(), [
            ArgumentGroupPattern(False, [
                ArgumentPattern("INTERACTIVE", ArgNum(Quantifier.FLAG), ["--interactive"], False, False, None),
                ArgumentPattern("NO_CLOBBER", ArgNum(Quantifier.FLAG), ["--no-clobber"], False, False, None),
            ])
        ])

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace(INTERACTIVE=False, NO_CLOBBER=False)
        actual = parser.parse_args([])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(INTERACTIVE=True, NO_CLOBBER=False)
        actual = parser.parse_args(["--interactive"])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(INTERACTIVE=False, NO_CLOBBER=True)
        actual = parser.parse_args(["--no-clobber"])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(INTERACTIVE=True, NO_CLOBBER=True)
        actual = parser.parse_args(["--interactive", "--no-clobber"])

        self.assertEqual(expected, actual)

    def test_arg_group_required(self):
        pattern = CommandPattern("test", list(), list(), [
            ArgumentGroupPattern(True, [
                ArgumentPattern("INTERACTIVE", ArgNum(Quantifier.FLAG), ["--interactive"], False, False, None),
                ArgumentPattern("NO_CLOBBER", ArgNum(Quantifier.FLAG), ["--no-clobber"], False, False, None),
            ])
        ])

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace(INTERACTIVE=True, NO_CLOBBER=False)
        actual = parser.parse_args(["--interactive"])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(INTERACTIVE=False, NO_CLOBBER=True)
        actual = parser.parse_args(["--no-clobber"])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(INTERACTIVE=True, NO_CLOBBER=True)
        actual = parser.parse_args(["--no-clobber", "--interactive"])

        self.assertEqual(expected, actual)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args([])

    def test_empty_arg_group_required(self):
        pattern = CommandPattern("test", list(), list(), [
            ArgumentGroupPattern(True, [])
        ])

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace()
        actual = parser.parse_args([])

        self.assertEqual(expected, actual)

    def test_empty_list_arg_group_required(self):
        pattern = CommandPattern("test", list(), list(), [
            ArgumentGroupPattern(True, [
                ArgumentPattern("LIST", ArgNum(Quantifier.ANY), ["--list"], False, False, None)
            ])
        ])

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace(LIST=[])
        actual = parser.parse_args(["--list"])

        self.assertEqual(expected, actual)

    def test_optional_argument(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("NUMBER", ArgNum(Quantifier.OPTIONAL), ["--number"], False, False, None)
        ], list())

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace(NUMBER=None)
        actual = parser.parse_args(["--number"])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(NUMBER="10")
        actual = parser.parse_args(["--number", "10"])

        self.assertEqual(expected, actual)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Identifier Testing                                                      #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_mixed_positional_args(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern(None, ArgNum(Quantifier.N, 1), list(), True, True, None),
            ArgumentPattern("FILE", ArgNum(Quantifier.N, 1), list(), True, True, None),
            ArgumentPattern(None, ArgNum(Quantifier.N, 1), list(), True, True, None),
        ], list())
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["a"])

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["a", "b"])

        namespace = parser.parse_args(["a", "b", "c"])
        self.assertEqual(argparse.Namespace(FILE="b", **{"1": "a", "3": "c"}), namespace)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Quantifier Testing                                                      #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_positional_arg(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("VAL", ArgNum(Quantifier.AT_LEAST_ONE, None), list(), True, True, None)
        ], list())
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args([])

        namespace = parser.parse_args(["value"])
        self.assertEqual(argparse.Namespace(VAL=["value"]), namespace)

        namespace = parser.parse_args(["value", "another", "final"])
        self.assertEqual(argparse.Namespace(VAL=["value", "another", "final"]), namespace)

    def test_flag_arg(self):
        command_pattern = CommandPattern("test", list(), [
            ArgumentPattern("verbose", ArgNum(Quantifier.FLAG), ["--verbose"], False, False, None)
        ], list())
        parser = pattern_to_argparse(command_pattern)

        namespace = parser.parse_args(["--verbose"])
        self.assertEqual(argparse.Namespace(verbose=True), namespace)

    def test_at_least_one_argument(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("LIST", ArgNum(Quantifier.AT_LEAST_ONE), ["--list"], False, False, None)
        ], list())

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace(LIST=["a", "b", "c", "d"])
        actual = parser.parse_args("--list a b c d".split())

        self.assertEqual(expected, actual)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args("--list".split())

    def test_any_argnum(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("LIST", ArgNum(Quantifier.ANY), ["--list"], False, False, None)
        ], list())

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace(LIST=[])
        actual = parser.parse_args("--list".split())

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(LIST=["a", "b"])
        actual = parser.parse_args("--list a b".split())

        self.assertEqual(expected, actual)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Delimiter Testing                                                       #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_delim_splitting(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("LIST", ArgNum(Quantifier.N, 1), ["--list"], False, True, ","),
        ], list())

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace(LIST=["a", "b", "c"])
        actual = parser.parse_args(["--list", "a,b,c"])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(LIST=["a"])
        actual = parser.parse_args(["--list", "a"])

        self.assertEqual(expected, actual)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["--list"])

    def test_delim_splitting_optional(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("LIST", ArgNum(Quantifier.OPTIONAL), ["--list"], False, True, ","),
        ], list())

        parser = pattern_to_argparse(pattern)

        expected = argparse.Namespace(LIST=["a", "b", "c"])
        actual = parser.parse_args(["--list", "a,b,c"])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(LIST=["a"])
        actual = parser.parse_args(["--list", "a"])

        self.assertEqual(expected, actual)

        expected = argparse.Namespace(LIST=[])
        actual = parser.parse_args(["--list"])

        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
