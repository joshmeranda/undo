import io
import os
import os.path
import typing
import re
import subprocess


def __read_commands(stream: typing.TextIO, n: int, func: typing.Callable[[str], str]) -> list[str]:
    """Read the last N commands from the stream excluding the current process' command.

    :param stream: the TextIO object to read.
    :param n: the amount off lines to read.
    :param func: a function to apply to each of the returned lines to extract a command, the string passed to func
        will have any trailing whitespace stripped.
    :return: the unprocessed last n lines from the file.
    """
    return list(map(lambda cmd: func(cmd.rstrip()),
                    stream.readlines()[-(n + 1):-1]))


def __generic_history(cmd: list[str], limit: int, file: typing.Optional[typing.TextIO],
                      func: typing.Callable[[str], str] = lambda line: line) -> list[str]:
    if file is None:
        proc = subprocess.run(cmd, capture_output=True)
        stream = io.StringIO(proc.stdout.decode("utf-8"))
    else:
        stream = file

    commands = __read_commands(stream, limit, func)

    if file is None:
        stream.close()

    return commands


def __history_sh(path: str, limit: int, file: typing.Optional[typing.TextIO]) -> list[str]:
    def parse_sh_history(line: str) -> str:
        match = re.match("  [1-9][0-9]*  (.*)", line)

        if match is None:
            raise ValueError(f"could not parse command from sh history line '{line}'")

        return match.group(1)

    return __generic_history(
        cmd=[path, "-c", f"history {limit + 1}"],
        limit=limit,
        file=file,
        func=parse_sh_history)


def __history_fish(path: str, limit: int, file: typing.Optional[typing.TextIO]) -> list[str]:
    return __generic_history(
        cmd=[path, "--command", f"history --reverse --max {limit + 1}"],
        limit=limit,
        file=file)


def history(limit: int = 1, shell: typing.Optional[str] = None, stream: typing.Optional[typing.TextIO] = None) -> list[str]:
    """Retrieve the last command(s) of the given shell excluding the command which launched the current command if
    included by the shell.

    The returned commands will be in order from most newest to oldest. If `shell` is not specified, the basename for the
    value of the `SHELL` environment variable is used. If `file` is not specified, the default file paths for the shell
    is used.

    Note that the commands returned by this method will be those returned by the given (or determined) shell builtin
    history command.

    :param shell: the name of the shell without any leading path elements ('bash' rather than '/usr/bin/bash').
    :param limit: the maximum amount off history entries too return.
    :param stream: The file-like object to read history data from.
    :return: a list of the last command(s) run through the given shell.
    """

    if shell is None:
        shell = os.getenv("SHELL")

        if shell is None:
            raise Exception("could not determine the target shell")

    shell_basename = os.path.basename(shell)

    if shell_basename == "bash" or shell_basename == "sh":
        return __history_sh(shell, limit, stream)
    elif shell_basename == "fish":
        return __history_fish(shell, limit, stream)
    else:
        raise Exception(f"unsupported shell '{shell}'")
