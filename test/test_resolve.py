import io
import os
import unittest

from undo import resolve

UndoRegistry = resolve.__UndoRegistry

RESOURCE_DIR_PATH = os.path.join(os.path.dirname(__file__), "resources")


class TestUndoRegistry(unittest.TestCase):
    def test_is_shell_supported(self):
        registry = UndoRegistry(io.StringIO("supported-shells = ['bash']"))

        self.assertTrue(registry.is_shell_supported("bash"))
        self.assertFalse(registry.is_shell_supported("not_supported"))

    def test_single_entry_no_args(self):
        registry = UndoRegistry(io.StringIO("""supported-shells = ['bash']
        
        [[entry]]
        cmd = "test"
        undo = "untest"
        precise = true
        """))

        expected = [(dict(), "untest")]

        actual = registry.resolve("test", False)

        self.assertListEqual(expected, actual)

    def test_multiple_entry_no_args(self):
        registry = UndoRegistry(io.StringIO("""supported-shells = ["bash"]
        
        [[entry]]
        cmd = "test"
        undo = "untest"
        precise = true
        
        [[entry]]
        cmd = "another"
        undo = "wrong"
        precise = true
        
        [[entry]]
        cmd = "yet-another"
        undo = "another_wrong"
        precise = true
        """))

        expected = [(dict(), "untest")]
        actual = registry.resolve("test", False)

        self.assertEqual(expected, actual)

    def test_multiple_entry_args(self):
        registry = UndoRegistry(io.StringIO(f"""unsupported-shells = ["bash"]
        
        [[entry]]
        cmd = "test [?:--all]"
        undo = "untest --all"
        precise = true
        
        [[entry]]
        cmd = "test sub-command"
        undo = "sub-command-wrong"
        precise = true
        
        [[entry]]
        cmd = "test <--some>"
        undo = "wrorng-some-required"
        precise = true
        
        [[entry]]
        cmd = "test"
        undo = "test-wrong"
        precise = true
        """))

        expected = [({"ALL": True}, "untest --all")]

        actual = registry.resolve("test --all", False)

        self.assertEqual(expected, actual)

    def test_multiple_resolutions(self):
        registry = UndoRegistry(io.StringIO(f"""unsupported-shells = ["bash"]
        
        [[entry]]
        cmd = "test [?:--all]"
        undo = "untest --all"
        precise = true
        
        [[entry]]
        cmd = "test sub-command"
        undo = "sub-command-wrong"
        precise = true
        
        [[entry]]
        cmd = "test [?:--some]"
        undo = "untest --some"
        precise = true
        """))

        expected = [({"ALL": False}, "untest --all"),
                    ({"SOME": False}, "untest --some")]

        actual = registry.resolve("test", False)

        self.assertEqual(expected, actual)

    def test_at_least_one_arg(self):
        registry = UndoRegistry(io.StringIO("""supported-shells = ['bash']
        
        [[entry]]
        cmd = 'mv <SRC...> <DST>'
        undo = 'mv % $DST % % $SRC %'
        precise = true
        """))

        expected = [({"SRC": ["SRC_0", "SRC_1"], "DST": "DST"}, "mv % $DST % % $SRC %")]
        actual = registry.resolve("mv SRC_0 SRC_1 DST", False)

        self.assertListEqual(expected, actual)

    def test_no_resolutions(self):
        registry = UndoRegistry(io.StringIO(f"""unsupported-shells = ["bash"]

        [[entry]]
        cmd = "test <?:--all>"
        undo = "untest --all"
        precise = true

        [[entry]]
        cmd = "test sub-command"
        undo = "sub-command-wrong"
        precise = true

        [[entry]]
        cmd = "test <?:--some>"
        undo = "untest --some"
        precise = true
        """))

        expected = []

        actual = registry.resolve("test", False)

        self.assertEqual(expected, actual)

    def test_precise(self):
        registry = UndoRegistry(io.StringIO("""supported-shells = ['bash']
        
        [[entry]]
        cmd = "test"
        undo = "untest"
        """))

        expected = []
        actual = registry.resolve("test", False)

        self.assertListEqual(expected, actual)

    def test_imprecise(self):
        registry = UndoRegistry(io.StringIO("""supported-shells = ['bash']
        
        [[entry]]
        cmd = "test"
        undo = "untest"
        """))

        expected = [(dict(), "untest")]
        actual = registry.resolve("test", True)

        self.assertListEqual(expected, actual)

    def test_missing_cmd(self):
        with self.assertRaises(resolve.RegistrySpecError):
            UndoRegistry(io.StringIO("""
                    [[entry]]
                    # cmd = "test"
                    undo = "untest"
                    """))

    def test_missing_undo(self):
        with self.assertRaises(resolve.RegistrySpecError):
            UndoRegistry(io.StringIO("""
                    [[entry]]
                    cmd = "test"
                    # undo = "untest"
                    """))


class TestResolve(unittest.TestCase):
    TEST_SEARCH_ALL_DIR = os.path.join(RESOURCE_DIR_PATH, "search_all")
    TEST_ALLOW_IMPRECISE = os.path.join(RESOURCE_DIR_PATH, "allow_imprecise")
    TEST_SUPPORT_ALL = os.path.join(RESOURCE_DIR_PATH, "support_all")

    def test_basic_no_search_all(self):
        expected = [(dict(), "untest")]
        actual = resolve.resolve("test", [TestResolve.TEST_SEARCH_ALL_DIR], False, False, "bash")

        self.assertListEqual(expected, actual)

    def test_search_all(self):
        expected = [
            (dict(), "untest"),
            (dict(), "untest"),
        ]
        actual = resolve.resolve("test", [TestResolve.TEST_SEARCH_ALL_DIR], True, False, "bash")

        self.assertListEqual(expected, actual)

    def test_allow_imprecise_false(self):
        expected = [
            (dict(), "untest"),
        ]
        actual = resolve.resolve("test", [TestResolve.TEST_ALLOW_IMPRECISE], False, False, "bash")

        self.assertListEqual(expected, actual)

    def test_allow_imprecise_true(self):
        expected = [
            (dict(), "untest"),
            (dict(), "untest --all"),
        ]
        actual = resolve.resolve("test", [TestResolve.TEST_ALLOW_IMPRECISE], False, True, "bash")

        self.assertListEqual(expected, actual)

    def test_search_unsupported_shell(self):
        expected = []
        actual = resolve.resolve("test", [TestResolve.TEST_SEARCH_ALL_DIR], False, True, "unsupported_shell")

        self.assertListEqual(expected, actual)

    def test_support_all(self):
        expected = [(dict(), "untest")]
        actual = resolve.resolve("test", [TestResolve.TEST_SUPPORT_ALL], False, True, "unsupported_shell")

        self.assertListEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
