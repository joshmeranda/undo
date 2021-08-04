import io
import os
import unittest

import resolve
from pattern import *

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
        """))

        expected = [(dict(), "untest")]

        actual = registry.resolve("test")

        self.assertListEqual(expected, actual)

    def test_multiple_entry_no_args(self):
        registry = UndoRegistry(io.StringIO("""supported-shells = ["bash"]
        
        [[entry]]
        cmd = "test"
        undo = "untest"
        
        [[entry]]
        cmd = "another"
        undo = "wrong"
        
        [[entry]]
        cmd = "yet-another"
        undo = "another_wrong"
        """))

        expected = [(dict(), "untest")]
        actual = registry.resolve("test")

        self.assertEqual(expected, actual)

    def test_multiple_entry_args(self):
        registry = UndoRegistry(io.StringIO(f"""unsupported-shells = ["bash"]
        
        [[entry]]
        cmd = "test [?:--all]"
        undo = "untest --all"
        
        [[entry]]
        cmd = "test sub-command"
        undo = "sub-command-wrong"
        
        [[entry]]
        cmd = "test <--some>"
        undo = "wrorng-some-required"
        
        [[entry]]
        cmd = "test"
        undo = "test-wrong"
        """))

        expected = [({"ALL": True}, "untest --all")]

        actual = registry.resolve("test --all")

        self.assertEqual(expected, actual)

    def test_multiple_resolutions(self):
        registry = UndoRegistry(io.StringIO(f"""unsupported-shells = ["bash"]
        
        [[entry]]
        cmd = "test [?:--all]"
        undo = "untest --all"
        
        [[entry]]
        cmd = "test sub-command"
        undo = "sub-command-wrong"
        
        [[entry]]
        cmd = "test [?:--some]"
        undo = "untest --some"
        """))

        expected = [({"ALL": False}, "untest --all"),
                    ({"SOME": False}, "untest --some")]

        actual = registry.resolve("test")

        self.assertEqual(expected, actual)

    def test_no_resolutions(self):
        registry = UndoRegistry(io.StringIO(f"""unsupported-shells = ["bash"]

        [[entry]]
        cmd = "test <?:--all>"
        undo = "untest --all"

        [[entry]]
        cmd = "test sub-command"
        undo = "sub-command-wrong"

        [[entry]]
        cmd = "test <?:--some>"
        undo = "untest --some"
        """))

        expected = []

        actual = registry.resolve("test")

        self.assertEqual(expected, actual)


class TestResolve(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["SHELL"] = "/usr/bin/bash"

    def test_basic_no_search_all(self):
        expected = [(dict(), "untest")]
        actual = resolve.resolve("test", [RESOURCE_DIR_PATH])

        self.assertListEqual(expected, actual)

    def test_search_all(self):
        expected = [
            (dict(), "untest"),
            (dict(), "untest"),
        ]
        actual = resolve.resolve("test", [RESOURCE_DIR_PATH], True)

        self.assertListEqual(expected, actual)

    def test_search_unsupported_shell(self):
        os.environ["SHELL"] = "unsupported_shell"

        expected = []
        actual = resolve.resolve("test", [RESOURCE_DIR_PATH], True)

        self.assertListEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
