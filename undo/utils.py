import os


def get_parent_shell() -> str:
    """Get the name of the user's current shell.

    todo: return optional if parent shell could not be determined
    todo: catch file read errors
    todo: allow user to force using the $SHELL env var?

    :return: the name of the shell used to launch undo.
    """

    with open(f"/proc/{os.getppid()}/comm") as proc:
        shell = proc.read().strip()

    return shell
