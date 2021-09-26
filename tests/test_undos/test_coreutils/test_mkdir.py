import unittest

from tests.test_undos.test_coreutils import common
from undo import expand, resolve


class TestMkdir(unittest.TestCase):
    def test_mkdir_single(self):
        command = "mkdir A"

        expected = ["rm A"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)

    def test_mkdir_multiple(self):
        command = "mkdir A B C"

        expected = ["rm A B C"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
