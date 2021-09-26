import unittest

from undo import expand


join_expanded = expand.__join_expanded
separate = expand.__separate


class TestJoinExpanded(unittest.TestCase):
    def test_join_no_list(self):
        expected = ["mv INNER OUTER"]
        actual = join_expanded(["mv ", "INNER", " ", "OUTER"])

        self.assertListEqual(expected, actual)

    def test_expanded_single_list(self):
        expected = ["list a", "list b"]
        actual = join_expanded(["list ", ["a", "b"]])

        self.assertEqual(expected, actual)

    def test_expanded_multiple_list(self):
        expected = ["a b", "c d"]
        actual = join_expanded([["a", "c"], " ", ["b", "d"]])

        self.assertEqual(expected, actual)


class TestSeparation(unittest.TestCase):
    def test_separation_basic(self):
        content = "$( 'hello' ) world"

        expected = ["$( 'hello' )", " world"]
        actual = separate(content, ("$(", ")"))

        self.assertListEqual(expected, actual)

    def test_nested(self):
        content = "$(\"$(basename('/some/file/path/hello')\") world"

        expected = ["$(\"$(basename('/some/file/path/hello')\")", " world"]
        actual = separate(content, ("$(", ")"))

        self.assertListEqual(expected, actual)

    def test_multiple_expressions_with_same_open_and_close_bounds(self):
        content = "% 'hello' % % 'world' %"

        expected = ["% 'hello' %", " ", "% 'world' %"]
        actual = separate(content, ("%", "%"))

        self.assertListEqual(expected, actual)

    def test_unintended_close_bound(self):
        content = "$(do_something('hello'))"

        expected = ["$(do_something('hello')", ")"]
        actual = separate(content, ("$(", ")"))

        self.assertListEqual(expected, actual)

    @unittest.skip("not yet implemented")
    def test_escaped_open_bound(self):
        content = "\\$( $(hello world)"

        expected = ["$( ", "%(hello world)"]
        actual = separate(content, ("$(", ")"))

        self.assertListEqual(expected, actual)

    @unittest.skip("not yet implemented")
    def test_escaped_close_bound(self):
        content = "$(hello world \\))"

        expected = ["%(hello world)", ")"]
        actual = separate(content, ("$(", ")"))

        self.assertListEqual(expected, actual)


class TestExpansion(unittest.TestCase):
    def test_no_expansion(self):
        expected = "no expansion"
        actual = expand.expand("no expansion", dict(), ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_leading_expansion(self):
        expected = "hello world"
        actual = expand.expand("% 'hello' % world", dict(), ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_trailing_expansion(self):
        expected = "hello world"
        actual = expand.expand("hello % 'world' %", dict(), ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_no_space_prefix(self):
        expected = "aA"
        actual = expand.expand("a% 'A' %", dict(), ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_middling_expansion(self):
        expected = "rm --verbose --recursive"
        actual = expand.expand("rm % VERBOSE ? '--verbose' % --recursive", {"VERBOSE": str(True)}, ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_back_to_back_expansion(self):
        expected = "FirstSecond"
        actual = expand.expand("% 'First' %% 'Second' %", dict(), ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_separated_expressions(self):
        expected = "First something Second"
        actual = expand.expand("% 'First' % something % 'Second' %", dict(), ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_list_expansion_expression(self):
        expected = "list a b c"
        actual = expand.expand("list % $LIST... %", {"LIST": ['a', 'b', 'c']}, ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_no_list_expansion(self):
        expected = "list a; list b; list c"
        actual = expand.expand("list % $LIST %", {"LIST": ['a', 'b', 'c']}, ("%", "%"), "; ")

        self.assertEqual(expected, actual)

    def test_multiple_no_list_expansion(self):
        expected = "list a d; list b e; list c f"
        actual = expand.expand("list % $LISTA % % $LISTB %", {
                "LISTA": ['a', 'b', 'c'],
                "LISTB": ['d', 'e', 'f'],
            }, ("%", "%"), "; ")

        self.assertEqual(expected, actual)

    def test_multiple_no_list_expansion_no_sep(self):
        expected = "list a d; list b e; list c f"
        expected = [
            "list a d",
            "list b e",
            "list c f",
        ]
        actual = expand.expand("list % $LISTA % % $LISTB %", {
                "LISTA": ['a', 'b', 'c'],
                "LISTB": ['d', 'e', 'f'],
            }, ("%", "%"), None)

        self.assertEqual(expected, actual)

    def test_multiple_unique_no_list_expansion(self):
        with self.assertRaises(ValueError):
            expand.expand("% $LISTA % % $LISTB %", {
                "LISTA": ['a', 'b', 'c'],
                "LISTB": ['d', 'e', 'f', 'g'],
            }, ("%", "%"), None)


if __name__ == "__main__":
    unittest.main()
