import os
import shutil
import unittest

import undo.resolve as resolve
import undo.expand as expand

import tests.test_undos.test_coreutils.common as common


class TestMv(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(common.COREUTILS_TEST_ENV_DIR):
            shutil.rmtree(common.COREUTILS_TEST_ENV_DIR)

        os.mkdir(common.COREUTILS_TEST_ENV_DIR)

        os.mknod(os.path.join(
            common.COREUTILS_TEST_ENV_DIR,
            "OUTER"
        ))

        os.mkdir(os.path.join(
            common.COREUTILS_TEST_ENV_DIR,
            "DIR"
        ))

        os.mknod(os.path.join(
            common.COREUTILS_TEST_ENV_DIR,
            "DIR",
            "INNER"
        ))

        os.mknod(os.path.join(
            common.COREUTILS_TEST_ENV_DIR,
            "DIR",
            "ANOTHER_INNER"
        ))

        cwd_bak = os.getcwd()
        os.chdir(common.COREUTILS_TEST_ENV_DIR)

        cls.addClassCleanup(shutil.rmtree, common.COREUTILS_TEST_ENV_DIR)
        cls.addClassCleanup(os.chdir, cwd_bak)

    def test_rename(self):
        command = "mv ORIGINAL OUTER"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["mv OUTER ORIGINAL"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_rename_precise(self):
        command = "mv --no-clobber ORIGINAL OUTER"

        expected = ["mv OUTER ORIGINAL"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_move_single(self):
        command = "mv INNER DIR"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["mv DIR/INNER INNER"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_move_single_precise(self):
        command = "mv --no-clobber INNER DIR"

        expected = ["mv DIR/INNER INNER"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_move_multiple(self):
        command = "mv INNER ANOTHER_INNER DIR"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["mv DIR/INNER INNER; mv DIR/ANOTHER_INNER ANOTHER_INNER"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_move_multiple_precise(self):
        command = "mv --no-clobber INNER ANOTHER_INNER DIR"

        expected = ["mv DIR/INNER INNER; mv DIR/ANOTHER_INNER ANOTHER_INNER"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_move_single_with_target_directory(self):
        command = "mv -t DIR INNER"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["mv DIR/INNER INNER"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_move_single_with_target_directory_precise(self):
        command = "mv --no-clobbe -t DIR INNER"

        expected = ["mv DIR/INNER INNER"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_move_multiple_with_target_directory(self):
        command = "mv -t DIR INNER ANOTHER_INNER"

        expected = []
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

        expected = ["mv DIR/INNER INNER; mv DIR/ANOTHER_INNER ANOTHER_INNER"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, True, "sh")]

        self.assertListEqual(expected, actual)

    def test_move_multiple_with_target_directory_precise(self):
        command = "mv --no-clobber -t DIR INNER ANOTHER_INNER"

        expected = ["mv DIR/INNER INNER; mv DIR/ANOTHER_INNER ANOTHER_INNER"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()

