import unittest
import io

from undo import history


class TestFishHistory(unittest.TestCase):
    def test_get_most_recent(self):
        commands = ["d",
                    "c",
                    "b",
                    "a",
                    "ignore.me"]

        stream = io.StringIO("\n".join(commands))

        expected = ["a"]
        actual = history.history(shell="fish", stream=stream)

        self.assertListEqual(expected, actual)

    def test_get_n_most_recent(self):
        commands = ["d",
                    "c",
                    "b",
                    "a",
                    "ignore.me"]

        stream = io.StringIO("\n".join(commands))

        expected = commands[:-1]
        actual = history.history("fish", 4, stream)

        self.assertListEqual(expected, actual)

    def test_get_overflow(self):
        commands = ["d",
                    "c",
                    "b",
                    "a",
                    "ignore.me"]

        stream = io.StringIO("\n".join(commands))

        expected = commands[:-1]
        actual = history.history("fish", 10, stream)

        self.assertListEqual(expected, actual)


class TestShHistory(unittest.TestCase):
    def test_get_most_recent(self):
        commands = ["  1  d",
                    "  2  c",
                    "  3  b",
                    "  4  a",
                    "  5  ignore.me"]

        stream = io.StringIO("\n".join(commands))

        expected = ["a"]
        actual = history.history(shell="sh", stream=stream)

        self.assertListEqual(expected, actual)

    def test_get_n_most_recent(self):
        commands = ["  1  d",
                    "  2  c",
                    "  3  b",
                    "  4  a",
                    "  5  ignore.me"]

        stream = io.StringIO("\n".join(commands))

        expected = ["d", "c", "b", "a"]
        actual = history.history("sh", 4, stream)

        self.assertListEqual(expected, actual)

    def test_get_overflow(self):
        commands = ["  1  d",
                    "  2  c",
                    "  3  b",
                    "  4  a",
                    "  5  ignore.me"]

        stream = io.StringIO("\n".join(commands))

        expected = ["d", "c", "b", "a"]
        actual = history.history("sh", 10, stream)

        self.assertListEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
