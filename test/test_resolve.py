import io
import os
import unittest

import resolve

UndoRegistry = resolve.__UndoRegistry

RESOURCE_DIR_PATH = os.path.join(os.path.dirname(__file__), "resources")


class TestUndoRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["SHELL"] = "/usr/bin/bash"

    def test_is_shell_supported(self):
        registry = UndoRegistry(io.StringIO("supported-shells = ['bash']"))

        self.assertTrue(registry.is_shell_supported())
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

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["SHELL"] = "/usr/bin/bash"

    def test_basic_no_search_all(self):
        expected = [(dict(), "untest")]
        actual = resolve.resolve("test", [TestResolve.TEST_SEARCH_ALL_DIR])

        self.assertListEqual(expected, actual)

    def test_search_all(self):
        expected = [
            (dict(), "untest"),
            (dict(), "untest"),
        ]
        actual = resolve.resolve("test", [TestResolve.TEST_SEARCH_ALL_DIR], search_all=True)

        self.assertListEqual(expected, actual)

    def test_allow_imprecise_false(self):
        expected = [
            (dict(), "untest"),
        ]
        actual = resolve.resolve("test", [TestResolve.TEST_ALLOW_IMPRECISE], allow_imprecise=False)

        self.assertListEqual(expected, actual)

    def test_allow_imprecise_true(self):
        expected = [
            (dict(), "untest"),
            (dict(), "untest --all"),
        ]
        actual = resolve.resolve("test", [TestResolve.TEST_ALLOW_IMPRECISE], allow_imprecise=True)

        self.assertListEqual(expected, actual)

    def test_search_unsupported_shell(self):
        os.environ["SHELL"] = "unsupported_shell"

        expected = []
        actual = resolve.resolve("test", [TestResolve.TEST_SEARCH_ALL_DIR], search_all=True)

        self.assertListEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
