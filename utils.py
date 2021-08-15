import os


def get_parent_shell() -> str:
    """Get the name of the user's current shell.

    :return: the name of the shell used to launch undo.
    """

    with open(f"/proc/{os.getppid()}/comm") as proc:
        shell = proc.read().strip()

    return shell
