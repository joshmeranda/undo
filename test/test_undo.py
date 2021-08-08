import unittest

import undo


class TestUndo(unittest.TestCase):
    def test_no_expansion(self):
        expected = "no expansion"
        actual = undo.expand("no expansion", dict())

        self.assertEqual(expected, actual)

    def test_leading_expansion(self):
        expected = "hello world"
        actual = undo.expand("% 'hello' % world", dict())

        self.assertEqual(expected, actual)

    def test_trailing_expansion(self):
        expected = "hello world"
        actual = undo.expand("hello % 'world' %", dict())

        self.assertEqual(expected, actual)

    def test_middling_expansion(self):
        expected = "rm --verbose --recursive"
        actual = undo.expand("rm % VERBOSE ? '--verbose' % --recursive", { "VERBOSE": str(True)})

        self.assertEqual(expected, actual)

    def test_back_to_back_expansion(self):
        expected = "FirstSecond"
        actual = undo.expand("% 'First' %% 'Second' %", dict())

        self.assertEqual(expected, actual)

    def test_separated_expressions(self):
        expected = "First something Second"
        actual = undo.expand("% 'First' % something % 'Second' %", dict())

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
