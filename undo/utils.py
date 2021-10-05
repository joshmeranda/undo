import os
import logging
import typing


def get_parent_shell(use_env: bool = False, env_on_error: bool = False) -> typing.Optional[str]:
    """Get the name of the user's current shell.

    :param use_env: always use the value of the environment variable 'SHELL', overrides `use_env_on_error`.
    :param env_on_error: if the parent shell could not be determined, use the value of the environment variable
        'SHELL'.
    :return: the name of the shell used to launch undo.
    """
    if use_env:
        return os.getenv("SHELL")

    ppid = os.getppid()
    shell = None

    try:
        with open(f"/proc/{ppid}/comm") as proc:
            shell = proc.read().strip()
    except FileNotFoundError:
        logging.warning(f"could not determine parent shell: no procfs file found for ppid '{ppid}'")
    except OSError as err:
        logging.warning(f"could not determine parent shell: {err}")

    if shell is None and env_on_error:
        shell = os.getenv("SHELL")

    return shell
