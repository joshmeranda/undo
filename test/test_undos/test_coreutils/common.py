import os.path

COREUTILS_TEST_ENV_DIR = os.path.join(
    os.path.dirname(__file__),
    "test_env"
)

COREUTILS_UNDO_DIR = os.path.realpath(os.path.join(
    __file__,
    "..", "..", "..", "..",
    "undos",
    "coreutils"
))
