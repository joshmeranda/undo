import unittest

from tests.test_undos.test_coreutils import common
from undo import expand, resolve


class TestLink(unittest.TestCase):
    def test_link(self):
        command = "link SOURCE DEST"

        expected = ["rm DEST"]
        actual = [expand.expand(undo, env, ("%", "%"), "; ")
                  for env, undo in
                  resolve.resolve(command, [common.COREUTILS_UNDO_DIR], False, False, "sh")]

        self.assertListEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
