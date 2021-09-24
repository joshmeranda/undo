import os
import shutil
import unittest

from test.test_undos.test_coreutils import common
from undo import expand, resolve


class TestLn(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(common.COREUTILS_TEST_ENV_DIR):
            shutil.rmtree(common.COREUTILS_TEST_ENV_DIR)

        os.mkdir(common.COREUTILS_TEST_ENV_DIR)

        os.mkdir(os.path.join(
            common.COREUTILS_TEST_ENV_DIR,
            "DIR"
        ))

        os.mknod(os.path.join(
            common.COREUTILS_TEST_ENV_DIR,
            "DIR",
            "TARGET",
        ))

        cwd_bak = os.getcwd()
        os.chdir(common.COREUTILS_TEST_ENV_DIR)

        cls.addClassCleanup(shutil.rmtree, common.COREUTILS_TEST_ENV_DIR)
        cls.addClassCleanup(os.chdir, cwd_bak)

    def test_link_single(self):
        command = "ln --force A B"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm B"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_single_precise(self):
        command = "ln A B"

        expected = ["rm B"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_no_target_directory(self):
        command = "ln --force -T A B"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm B"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_no_target_directory_precise(self):
        command = "ln -T A B"

        expected = ["rm B"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_single_link_into_dir(self):
        command = "ln --force A DIR"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/A"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_single_link_into_dir_precise(self):
        command = "ln A DIR"

        expected = ["rm DIR/A"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_multiple_link_into_dir(self):
        command = "ln --force A B DIR"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/A; rm DIR/B"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_multiple_link_into_dir_precise(self):
        command = "ln A B DIR"

        expected = ["rm DIR/A; rm DIR/B"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_into_cwd(self):
        command = f"ln --force {os.path.join(common.COREUTILS_TEST_ENV_DIR, 'DIR', 'TARGET')}"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm TARGET"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_into_cwd_precise(self):
        command = f"ln {os.path.join(common.COREUTILS_TEST_ENV_DIR, 'DIR', 'TARGET')}"

        expected = ["rm TARGET"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_target_directory_single(self):
        command = "ln --force -t DIR A"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/A"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_target_directory_single_precise(self):
        command = "ln -t DIR A"

        expected = ["rm DIR/A"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_target_directory_multiple(self):
        command = "ln --force -t DIR A B"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/A; rm DIR/B"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_link_target_directory_multiple_precise(self):
        command = "ln -t DIR A B"

        expected = ["rm DIR/A; rm DIR/B"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
