import unittest
from pattern import ArgumentPattern, ArgNum, ArgumentPatternParser, CommandPatternParser, CommandPattern


class TestArgumentPattern(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.__parser = ArgumentPatternParser()
    
    def test_parse_flag(self):
        content = "[VERBOSE?:--verbose,-v]"

        expected = ArgumentPattern("VERBOSE", ArgNum.Zero, ["--verbose", "-v"], False, False)
        actual = self.__parser.parse(content)

        self.assertEqual(expected, actual)

    def test_parse_single(self):
        content = "[DIR:-d,--dir]"

        expected = ArgumentPattern("DIR", ArgNum.One, ["-d", "--dir"], False, False)
        actual = self.__parser.parse(content)

        self.assertEqual(expected, actual)

    def test_parse_many(self):
        content = "[FIELDS...:-f,--fields]"

        expected = ArgumentPattern("FIELDS", ArgNum.Many, ["-f", "--fields"], False, False)
        actual = self.__parser.parse(content)

        self.assertEqual(expected, actual)

    def test_positional_many(self):
        content = "<SRC...>"

        expected = ArgumentPattern("SRC", ArgNum.Many, list(), True, True)
        actual = self.__parser.parse(content)

        self.assertEqual(expected, actual)

    def test_missing_var_name(self):
        content = "[--dir,-d]"

        expected = ArgumentPattern("DIR", ArgNum.One, ["--dir", "-d"], False, False)
        actual = self.__parser.parse(content)

        self.assertEqual(expected, actual)

    def test_positional_missing_var_name(self):
        content = "<...>"

        expected = ArgumentPattern(None, ArgNum.Many, list(), True, True)
        actual = self.__parser.parse(content)

        self.assertEqual(expected, actual)

    def test_bad_argument_name(self):
        self.assertRaises(ValueError, self.__parser.parse, "<->")
        self.assertRaises(ValueError, self.__parser.parse, "<-->")
        self.assertRaises(ValueError, self.__parser.parse, "<-aa>")
        self.assertRaises(ValueError, self.__parser.parse, "<--a--b>")
        self.assertRaises(ValueError, self.__parser.parse, "<-a--a>")


class TestCommandPattern(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.__parser = CommandPatternParser(ArgumentPatternParser())

    def test_parse_no_arguments(self):
        content = "test"

        expected = CommandPattern("test", list(), list())
        actual = self.__parser.parse(content)

        self.assertEqual(expected, actual)

    def test_parse_sub_commands(self):
        content = "test one two"

        expected = CommandPattern("test", ["one", "two"], list())
        actual = self.__parser.parse(content)

        self.assertEqual(expected, actual)

    def test_parse_arguments(self):
        content = "test <?:--verbose>"

        actual = self.__parser.parse(content)
        expected = CommandPattern("test", list(), [
            ArgumentPattern("VERBOSE", ArgNum.Zero, ["--verbose"], False, True)
        ])

        self.assertEqual(expected, actual)
