import os
import shutil
import unittest

from undo import resolve, expand

from test.test_undos.test_coreutils import common

# import logging
# logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.DEBUG)


class TestCp(unittest.TestCase):
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

    def test_copy_single(self):
        command = "cp SRC DST"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DST"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_copy_single_precise(self):
        command = "cp --interactive SRC DST"

        expected = ["rm DST"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_copy_many_into_dir(self):
        command = "cp A B C DIR"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/A; rm DIR/B; rm DIR/C"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_copy_many_into_dir_precise(self):
        command = "cp --no-clobber A B C DIR"

        expected = ["rm DIR/A; rm DIR/B; rm DIR/C"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_copy_into_target_dir(self):
        command = "cp --target-directory DIR A B C"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["rm DIR/A; rm DIR/B; rm DIR/C"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_copy_into_target_dir_precise(self):
        command = "cp --no-clobber --target-directory DIR A B C"

        expected = ["rm DIR/A; rm DIR/B; rm DIR/C"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
