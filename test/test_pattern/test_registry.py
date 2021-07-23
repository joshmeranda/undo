import unittest

from pattern import UndoRegistry, CommandPattern, ArgumentPattern, ArgNum, Quantifier


class TestRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.__registry = UndoRegistry()

    def test_single_entry(self):
        expected = "untest"
        self.__registry.register(CommandPattern("test", list(), list()), expected)

        actual = self.__registry.undo("test")

        self.assertEqual(expected, actual)

    def test_multiple_entry_no_args(self):
        expected = "untest"
        wrong = "wrong"

        self.__registry.register(CommandPattern("test", list(), list()), expected)
        self.__registry.register(CommandPattern("another", list(), list()), wrong)
        self.__registry.register(CommandPattern("yet-another", list(), list()), wrong)

        actual = self.__registry.undo("test")

        self.assertEqual(expected, actual)

    def test_multiple_entry_args(self):
        expected = "untest --all"
        wrong = "wrong"

        self.__registry.register(CommandPattern("test", list(), [
            ArgumentPattern(None, ArgNum(Quantifier.N, 0), ["--all"], False, False)
        ]), expected)

        self.__registry.register(CommandPattern("test", ["sub-command"], list()), wrong)
        self.__registry.register(CommandPattern("test", list(), [
            ArgumentPattern(None, ArgNum(Quantifier.N, 0), ["--some"], False, True)]),
                                 wrong)

        self.__registry.register(CommandPattern("test", list(), list()), wrong)

        actual = self.__registry.undo("test --all")

        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
