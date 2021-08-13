import os
import subprocess
import unittest

import undo


class TestExpansion(unittest.TestCase):
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


class TestUndo(unittest.TestCase):
    ENTRYPOINT_PATH = os.path.realpath(os.path.join("..", "undo.py"))

    RESOURCE_DIR_PATH = os.path.join(os.path.dirname(__file__), "resources")
    CLI_RESOURCE_PATH = os.path.join(RESOURCE_DIR_PATH, "cli")

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["SHELL"] = "/usr/bin/bash"
        os.environ["UNDO_INCLUDE_DIRS"] = TestUndo.CLI_RESOURCE_PATH

    def test_no_match(self):
        proc = subprocess.run(["python", TestUndo.ENTRYPOINT_PATH, "--command", "no_match"], capture_output=True)

        expected = b"no command was found to undo 'no_match'\n"
        actual = proc.stdout

        print(TestUndo.ENTRYPOINT_PATH)

        self.assertEqual(expected, actual)
        self.assertEqual(b"", proc.stderr)

    def test_one_command(self):
        proc = subprocess.run(["python", TestUndo.ENTRYPOINT_PATH, "--command", "test_one"],
                              capture_output=True)

        expected = b"command found\n"
        actual = proc.stdout

        self.assertEqual(expected, actual)
        self.assertEqual(b"", proc.stderr)

    def test_multiple_commands(self):
        proc = subprocess.run(["python", TestUndo.ENTRYPOINT_PATH, "--command", "test_multiple"],
                              capture_output=True)

        expected = (b"multiple undo commands found, copy on the the commands below to clipboard to run: \n"
                    b"  1 ) echo 'command found (1)'\n"
                    b"  2 ) echo 'command found (2)'\n")
        actual = proc.stdout

        self.assertEqual(expected, actual)
        self.assertEqual(b"", proc.stderr)

    def test_interactive_one(self):
        proc = subprocess.Popen(["python", TestUndo.ENTRYPOINT_PATH,
                                 "--command", "test_one", "--interactive"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        expected = b"run command 'echo 'command found''? [Y/n] command found\n"
        actual, err = proc.communicate(b"y\n", timeout=1)

        self.assertEqual(expected, actual)
        self.assertEqual(b"", err)

    def test_interactive_multiple(self):
        proc = subprocess.Popen(["python", TestUndo.ENTRYPOINT_PATH,
                                 "--command", "test_multiple", "--interactive"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        expected = (b"Please select the command to run (invalid input will run no commands):\n"
                    b"  1 ) echo 'command found (1)'\n"
                    b"  2 ) echo 'command found (2)'\n"
                    b"selection: "
                    b"command found (2)\n")
        actual, err = proc.communicate(b"2\n")

        self.assertEqual(expected, actual)
        self.assertEqual(b"", err)


if __name__ == '__main__':
    unittest.main()
