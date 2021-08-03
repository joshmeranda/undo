import argparse
import os
import shlex
import toml

import pattern


class __UndoRegistry:
    __SHELLS = "supported-shells"

    __ENTRIES = "entry"
    __ENTRY_CMD = "cmd"
    __ENTRY_UNDO = "undo"

    def __init__(self, file):
        """A registry of command patterns to undo patterns.

        :param file: a path to a file or file-like object with the toml contents describing the registry.
        """

        data = toml.load(file)

        self.__shells = data.setdefault(self.__SHELLS, [])
        self.__entries = [{
            self.__ENTRY_CMD: pattern.parse_command_pattern(entry[self.__ENTRY_CMD]),
            self.__ENTRY_UNDO: entry[self.__ENTRY_UNDO]
        }
            for entry in data.setdefault(self.__ENTRIES, dict())]

    def is_shell_supported(self, shell: str = None) -> bool:
        """Determine if the given shell is supported by the registry file.

        :param shell: THe name of the shell to check for support, defaults to the basename of the environment variable
            SHELL
        :return: True if supported, and False if not.
        """

        if not shell:
            shell = os.path.basename(os.getenv("SHELL"))

        return shell in self.__shells

    def resolve(self, command: str) -> list[(argparse.Namespace, str)]:
        """Resolve the given command with the registered undo pattern.

        :param command: the command to register.
        :return: the matching undo pattern.
        """
        command, *argv = shlex.split(command)

        undos: list[(argparse.Namespace, str)] = list()

        for entry in self.__entries:
            parser = pattern.pattern_to_argparse(entry[self.__ENTRY_CMD])

            if parser.prog == command:
                try:
                    namespace = parser.parse_args(argv)
                    undo = entry[self.__ENTRY_UNDO]

                    undos.append((namespace, undo))
                except argparse.ArgumentError as err:
                    pass

        return undos


def __resolve_in_dir(include_dir: str, command: str, search_all: bool = False) -> list[(argparse.Namespace, str)]:
    """Attempt to resolve the command from the undo files located in the given directory path.

    Please note that this method will not delve into sub directories, and will only search files with the 'undo'
    extension.

    :param include_dir: the directory to search.
    :param command: the command to resolve.
    :param search_all: allow for finding multiple undo commands across all commands.
    :return: the resolved string command, or None if no appropriate command could be found.
    """
    undos = list()

    for file in os.listdir(include_dir):
        full_path = os.path.join(include_dir, file)

        try:
            registry = __UndoRegistry(full_path)
        except toml.TomlDecodeError:
            # todo: log error on verbose
            continue

        if not registry.is_shell_supported():
            continue

        resolution = registry.resolve(command)

        if resolution:
            undos += resolution

            if not search_all:
                break

    return undos


def resolve(command: str, include_dirs: list[str], search_all: bool = False) -> list[(argparse.Namespace, str)]:
    """Resolve the given command to the appropriate undo command.


    If search_all is False, resolve will return the undo patterns in the first file found with one or more matching undo
    patterns.

    :param command: the command to resolve.
    :param include_dirs: the directories to use for undo resolution.
    :param search_all: search all files rather than stopping at hte first file with a matching undo pattern.
    :return: the resolved string command, or None if no appropriate command could be found.
    """

    # include_dirs = os.getenv("UNDO_INCLUDE_PATH",
    #                          ["~/.local/share/undo", "/usr/local/share", "/usr/share/undo"])

    undos = list()

    for include_dir in include_dirs:
        if os.path.exists(include_dir):
            resolutions = __resolve_in_dir(include_dir, command, search_all)

            if resolutions:

                undos += resolutions

                if not search_all:
                    break

    return undos
