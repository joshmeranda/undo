import io
import logging
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


def __generic_history(cmd: list[str], limit: int, stream: typing.Optional[typing.TextIO],
                      func: typing.Callable[[str], str] = lambda line: line) -> list[str]:
    """Provides a wrapper around a shell history parser function.

    :param cmd: the command to call to retrieve the command history.
    :param limit: the maximum amount off history entries too return.
    :param stream: The file-like object to read history data from.
    :param func: the history parsing function, defaults to a simple pass-through.
    """
    if stream is None:
        logging.debug(f"running history command '{' '.join(cmd)}'")
        proc = subprocess.run(cmd, capture_output=True)
        stream = io.StringIO(proc.stdout.decode("utf-8"))

        return __read_commands(stream, limit, func)

    with stream:
        return __read_commands(stream, limit, func)


def __history_sh(path: str, limit: int, stream: typing.Optional[typing.TextIO]) -> list[str]:
    def parse_sh_history(line: str) -> str:
        match = re.match("  [1-9][0-9]*  (.*)", line)

        if match is None:
            raise ValueError(f"could not parse command from sh history line '{line}'")

        return match.group(1)

    return __generic_history(
        cmd=[path, "-c", f"history {limit + 1}"],
        limit=limit,
        stream=stream,
        func=parse_sh_history)


def __history_fish(path: str, limit: int, stream: typing.Optional[typing.TextIO]) -> list[str]:
    return __generic_history(
        cmd=[path, "--command", f"history --reverse --max {limit + 1}"],
        limit=limit,
        stream=stream)


def history(shell: str, limit: int = 1, stream: typing.Optional[typing.TextIO] = None) -> list[str]:
    """Retrieve the last command(s) of the given shell excluding the command which launched the current command if
    included by the shell.

    The returned commands will be in order from most newest to oldest.

    If `shell` is not specified, the process name of the ppid is used (/proc/<ppid>/comm).

    If `stream` is provided, the given shell's history command is ignored, and the command history is read from stream
    instead; however, the `shell` argument is still needed to specify the history format. It is important to note that
    Undo parses according to the history command output, not the hisstory file format. So in the case of shells like
    fish, whose history command and history file formats are entirely different, to produce a stream a command like
    `cat $HOME/.local/share/fish/fish_history` would not be sufficient, but a command like `history . out & cat out`
    would produce a usable stream.

    Note that the commands returned by this method will be those returned by the given (or determined) shell builtin
    history command.

    :param shell: the name of the shell without any leading path elements ('bash' rather than '/usr/bin/bash').
    :param limit: the maximum amount off history entries too return.
    :param stream: The file-like object to read history data from.
    :return: a list of the last command(s) run through the given shell.
    """

    if shell == "bash" or shell == "sh":
        return __history_sh(shell, limit, stream)
    elif shell == "fish":
        return __history_fish(shell, limit, stream)
    else:
        raise Exception(f"unsupported shell '{shell}'")
