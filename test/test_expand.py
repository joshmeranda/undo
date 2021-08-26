import unittest

from undo import expand


class TestExpansion(unittest.TestCase):
    def test_no_expansion(self):
        expected = "no expansion"
        actual = expand.expand("no expansion", dict())

        self.assertEqual(expected, actual)

    def test_leading_expansion(self):
        expected = "hello world"
        actual = expand.expand("% 'hello' % world", dict())

        self.assertEqual(expected, actual)

    def test_trailing_expansion(self):
        expected = "hello world"
        actual = expand.expand("hello % 'world' %", dict())

        self.assertEqual(expected, actual)

    def test_middling_expansion(self):
        expected = "rm --verbose --recursive"
        actual = expand.expand("rm % VERBOSE ? '--verbose' % --recursive", {"VERBOSE": str(True)})

        self.assertEqual(expected, actual)

    def test_back_to_back_expansion(self):
        expected = "FirstSecond"
        actual = expand.expand("% 'First' %% 'Second' %", dict())

        self.assertEqual(expected, actual)

    def test_separated_expressions(self):
        expected = "First something Second"
        actual = expand.expand("% 'First' % something % 'Second' %", dict())

        self.assertEqual(expected, actual)

    def test_list_expansion_expression(self):
        expected = "list a b c"
        actual = expand.expand("list % $LIST... %", {"LIST": ['a', 'b', 'c']})

        self.assertEqual(expected, actual)

    def test_no_list_expansion(self):
        expected = "list a; list b; list c"
        actual = expand.expand("list % $LIST %", {"LIST": ['a', 'b', 'c']})

        self.assertEqual(expected, actual)

    def test_multiple_no_list_expansion(self):
        expected = "list a d; list b e; list c f"
        actual = expand.expand("list % $LISTA % % $LISTB %", {
                "LISTA": ['a', 'b', 'c'],
                "LISTB": ['d', 'e', 'f'],
            })

        self.assertEqual(expected, actual)

    def test_multiple_unique_no_list_expansion(self):
        with self.assertRaises(ValueError):
            expand.expand("% $LISTA % % $LISTB %", {
                "LISTA": ['a', 'b', 'c'],
                "LISTB": ['d', 'e', 'f', 'g'],
            })


if __name__ == "__main__":
    unittest.main()
