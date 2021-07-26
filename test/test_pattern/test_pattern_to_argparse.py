import argparse
import unittest

from pattern import CommandPattern, pattern_to_argparse, ArgumentPattern, ArgNum, Quantifier


class TestPatternToArgparse(unittest.TestCase):
    def test_basic(self):
        pattern = CommandPattern("test", list(), list())
        parser = pattern_to_argparse(pattern)

        parser.parse_args([])

        namespace = parser.parse_args([])
        self.assertEqual(argparse.Namespace(), namespace)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(["--verbose"])
            parser.parse_args(["some", "positional", "args"])

    def test_optional_arg(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("VAL", ArgNum(Quantifier.N, 1), ["-V", "--val"], False, False)
        ])
        parser = pattern_to_argparse(pattern)

        namespace = parser.parse_args([])
        self.assertEqual(argparse.Namespace(VAL=None), namespace)

        namespace = parser.parse_args(["-V", "value"])
        self.assertEqual(argparse.Namespace(VAL="value"), namespace)

        namespace = parser.parse_args(["--val", "value"])
        self.assertEqual(argparse.Namespace(VAL="value"), namespace)

    def test_required_arg(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("VAL", ArgNum(Quantifier.N, 1), ["-V", "--val"], False, True)
        ])
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_known_args([])

        namespace = parser.parse_args(["-V", "value"])
        self.assertEqual(argparse.Namespace(VAL="value"), namespace)

        namespace = parser.parse_args(["--val", "value"])
        self.assertEqual(argparse.Namespace(VAL="value"), namespace)

    def test_positional_arg(self):
        pattern = CommandPattern("test", list(), [
            ArgumentPattern("VAL", ArgNum(Quantifier.AT_LEAST_ONE, None), list(), True, True)
        ])
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_known_args([])

        namespace = parser.parse_args(["value"])
        self.assertEqual(argparse.Namespace(VAL=["value"]), namespace)

        namespace = parser.parse_args(["value", "another", "final"])
        self.assertEqual(argparse.Namespace(VAL=["value", "another", "final"]), namespace)

    def test_flag_arg(self):
        command_pattern = CommandPattern("test", list(), [
            ArgumentPattern("verbose", ArgNum(Quantifier.N, 0), ["--verbose"], False, False)
        ])
        parser = pattern_to_argparse(command_pattern)

        namespace = parser.parse_args(["--verbose"])
        self.assertEqual(argparse.Namespace(verbose=True), namespace)

    def test_sub_command(self):
        pattern = CommandPattern("test", ["one"], list())
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args([])
            parser.parse_args(["one", "three"])
            parser.parse_args(["two"])

        expected = argparse.Namespace(command="one")
        actual = parser.parse_args(["one"])

        self.assertEqual(expected, actual)

    def test_nested_sub_commands(self):
        pattern = CommandPattern("test", ["one", "two"], list())
        parser = pattern_to_argparse(pattern)

        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args([])
            parser.parse_args(["one"])
            parser.parse_args(["one", "three"])
            parser.parse_args(["two"])

        expected = argparse.Namespace(command="two")
        actual = parser.parse_args("one two".split())

        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()