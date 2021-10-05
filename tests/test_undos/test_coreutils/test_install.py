import os
import shutil
import unittest

from undo import resolve, expand

from tests.test_undos.test_coreutils import common


class TestInstall(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(common.COREUTILS_TEST_ENV_DIR):
            shutil.rmtree(common.COREUTILS_TEST_ENV_DIR)

        os.mkdir(common.COREUTILS_TEST_ENV_DIR)

        os.mkdir(os.path.join(
            common.COREUTILS_TEST_ENV_DIR,
            "DIR"
        ))

        cwd_bak = os.getcwd()
        os.chdir(common.COREUTILS_TEST_ENV_DIR)

        cls.addClassCleanup(shutil.rmtree, common.COREUTILS_TEST_ENV_DIR)
        cls.addClassCleanup(os.chdir, cwd_bak)

    def test_install_file(self):
        command = "install SRC DIR/DST"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/DST"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_install_file_no_target_directory(self):
        command = "install -T SRC DIR/DST"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/DST"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_install_single(self):
        command = "install SRC DIR"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/SRC"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_install_multiple(self):
        command = "install A B C DIR"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/A DIR/B DIR/C"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_install_single_target_directory(self):
        command = "install -t DIR SRC"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/SRC"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_install_multiple_target_directory(self):
        command = "install -t DIR A B C"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/A DIR/B DIR/C"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_install_directory(self):
        command = "install -d A B C"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm --recursive A B C"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
