import unittest

from test.test_undos.test_coreutils import common
from undo import expand, resolve


class TestMknod(unittest.TestCase):
    def test_no_major_minor(self):
        command = "mknod NAME p"

        expected = ["rm NAME"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_with_major_minor(self):
        command = "mknod NAME b MAJOR MINOR"

        expected = ["rm NAME"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
