import argparse
import logging
import os
import shlex

import toml

from undo import pattern


class RegistrySpecError(ValueError):
    """An error with an undo file specification."""


# todo: add support for common and/or ignorable arguments for all entries (saves a lot of copy and pasting
class __UndoRegistry:
    __SHELLS = "supported-shells"

    __ENTRIES = "entry"
    __ENTRY_CMD = "cmd"
    __ENTRY_UNDO = "undo"
    __ENTRY_PRECISE = "precise"

    def __init__(self, file):
        """A registry of command patterns to undo patterns.

        :param file: a path to a file or file-like object with the toml contents describing the registry.
        """

        data = toml.load(file)

        self.__shells = data.setdefault(self.__SHELLS, "all")

        try:
            self.__entries = [{
                self.__ENTRY_CMD: entry[self.__ENTRY_CMD],
                self.__ENTRY_UNDO: entry[self.__ENTRY_UNDO],
                self.__ENTRY_PRECISE: entry.setdefault(self.__ENTRY_PRECISE, False)
            }
                for entry in data.setdefault(self.__ENTRIES, dict())]
        except KeyError as err:
            raise RegistrySpecError(f"missing required key {err}")

    def is_shell_supported(self, shell: str) -> bool:
        """Determine if the given shell is supported by the registry file.

        :param shell: THe name of the shell to check for support, defaults to the basename of the environment variable
            SHELL
        :return: True if supported, and False if not.
        """

        is_supported = self.__shells == "all" or shell in self.__shells

        if not is_supported:
            logging.debug(f"shell '{shell}' is not supported")

        return is_supported

    def resolve(self, command: str, allow_imprecise: bool) -> list[(dict, str)]:
        """Resolve the given command with the registered undo pattern.

        :param command: the command to register.
        :param allow_imprecise: include imprecise undo patterns in the returned results.
        :return: the matching undo pattern.
        """
        cmd, *argv = shlex.split(command)

        undos: list[(dict, str)] = list()

        for entry in self.__entries:
            cmd_pattern = pattern.parse_command_pattern(entry[self.__ENTRY_CMD])
            undo_pattern = entry[self.__ENTRY_UNDO]
            precise = entry[self.__ENTRY_PRECISE]

            parser = pattern.pattern_to_argparse(cmd_pattern)

            if parser.prog == cmd:
                try:
                    namespace = parser.parse_args(argv)

                    if precise or not precise and allow_imprecise:
                        undos.append((vars(namespace), undo_pattern))
                        logging.info(f"command '{command}' matched pattern '{entry[self.__ENTRY_CMD]}'")
                    else:
                        logging.debug(f"command '{command}' matched pattern '{entry[self.__ENTRY_CMD]}' but was not "
                                      f"precise enough")
                except argparse.ArgumentError as err:
                    logging.debug(f"command '{command}' does not match '{entry[self.__ENTRY_CMD]}: {err}'")

        return undos


def __resolve_in_dir(include_dir: str, command: str, search_all: bool, allow_imprecise: bool,
                     shell: str) -> list[(dict, str)]:
    """Attempt to resolve the command from the undo files located in the given directory path.

    Please note that this method will not delve into sub directories, and will only search files with the 'undo'
    extension.

    :param include_dir: the directory to search.
    :param command: the command to resolve.
    :param search_all: allow for finding multiple undo commands across all commands.
    :return: the resolved string command, or None if no appropriate command could be found.
    """
    logging.info(f"resolving directory '{include_dir}'")
    undos = list()

    for path in os.listdir(include_dir):
        full_path = os.path.join(include_dir, path)

        if not os.path.isfile(full_path):
            continue

        logging.info(f"resolving in file '{full_path}'")

        try:
            registry = __UndoRegistry(full_path)
        except toml.TomlDecodeError as err:
            logging.error(f"there was an issue deserializing toml file")
            logging.error(err)
            continue

        if not registry.is_shell_supported(shell):
            continue

        resolution = registry.resolve(command, allow_imprecise)

        if resolution:
            undos += resolution

            if not search_all:
                break

    return undos


def resolve(command: str, include_dirs: list[str], search_all: bool, allow_imprecise: bool,
            shell: str) -> list[(dict, str)]:
    """Resolve the given command to the appropriate undo command.

    If search_all is False, resolve will return the undo patterns in the first file found with one or more matching undo
    patterns.

    :param command: the command to resolve.
    :param include_dirs: the directories to use for undo resolution.
    :param search_all: search all files rather than stopping at hte first file with a matching undo pattern.
    :param allow_imprecise: include imprecise undo patterns in the returned results.
    :param shell: the shell to use when checking if the current shell is supported by the undo registry.
    :return: the resolved string command, or None if no appropriate command could be found.
    """
    undos = list()

    for include_dir in include_dirs:

        if os.path.exists(include_dir):
            resolutions = __resolve_in_dir(include_dir, command, search_all, allow_imprecise, shell)

            if resolutions:
                undos += resolutions

                if not search_all:
                    break
        else:
            logging.debug(f"include directory '{include_dir}' does not exists")

    return undos
