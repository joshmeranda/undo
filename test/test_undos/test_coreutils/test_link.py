import unittest

from test.test_undos.test_coreutils import common
from undo import expand, resolve


class TestLink(unittest.TestCase):
    def test_something(self):
        command = "link FILE1 FILE2"

        expected = ["rm FILE2"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()