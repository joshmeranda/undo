from .pattern import *

import argparse
import shlex
import typing


class _UndoArgumentParser(argparse.ArgumentParser):
    """Simple child class of ArgumentParser designed to allow for handling argument parsing error."""
    def exit(self, status=0, message=None):
        """Do nothing..."""

    def error(self, message):
        raise argparse.ArgumentError(None, message)


def pattern_to_argparse(command_pattern: CommandPattern) -> argparse.ArgumentParser:
    """Converts the given command pattern to an ArgumentParser.

    Since we do not want the argument parser to exit when a given command does not match any pattern, the
    `exit_on_error` parameter is set to `False` on all returned parsers. Note that due to bgo-41255 there are still
    remaining issues with the `exit_on_error` kwarg and so this subclass with overridden `exit` and `error` methods
    is needed.

    todo: add more documentation
        how are un-named positional arguments named?
        nargs?
        required?
        flags?
        error_on_exit == false

    todo: test if setting "help" arguments to "''" rather than None is faster

    :param command_pattern: the source CommandPattern to build the ArgumentParser from.
    :return: The built ArgumentParser.
    """
    base_parser = _UndoArgumentParser(prog=command_pattern.command, exit_on_error=False)
    parser = base_parser

    for sub_command in command_pattern.sub_commands:
        sub_parser = parser.add_subparsers(dest="command", required=True)

        parser = sub_parser.add_parser(sub_command)

    positional_count = 0

    kwargs = dict()

    for arg in command_pattern.arguments:
        if arg.is_positional:
            if arg.var_name is not None:
                names = [arg.var_name]
            else:
                names = str(positional_count)

            positional_count += 1
        else:
            names = arg.args

        if arg.arg_num.quantifier == Quantifier.Any:
            kwargs["nargs"] = "*"
        elif arg.arg_num.quantifier == Quantifier.AtLeastOne:
            kwargs["nargs"] = "+"
        elif arg.arg_num.count == 1:
            kwargs["nargs"] = None
        elif arg.arg_num.count != 0:
            kwargs["nargs"] = arg.arg_num.count
        elif arg.arg_num.count == 0:
            # kwargs["type"] = bool
            kwargs["action"] = "store_true"

        if not arg.is_positional:
            kwargs["required"] = arg.is_required
            kwargs["dest"] = arg.var_name

        parser.add_argument(*names, **kwargs)

    return base_parser


class UndoRegistry:
    def __init__(self):
        # todo: consider segmenting by command first for faster lookup in `undo`
        # todo: consider tracking the command patter as well for more detailed error messages in `undo`
        self.__registry: dict[argparse.ArgumentParser, str] = dict()

    def register(self, command: CommandPattern, undo: str):
        parser = pattern_to_argparse(command)

        self.__registry[parser] = undo

    def undo(self, command: str) -> typing.Optional[str]:
        """Retrieve the command to run to undo the given command.

        :param command: the command to be undone.
        :return: a command as a string or None if no matching command pattern could be found.
        """
        command, *argv = shlex.split(command)

        undos: list[str] = list()

        for parser, undo in self.__registry.items():
            try:
                if parser.prog == command:
                    parser.parse_args(argv)
                    undos.append(undo)
            except argparse.ArgumentError:
                pass

        if len(undos) > 1:
            # todo: add custom error type
            raise Exception(f"too many matches found for '{command}', could not undo")

        return None if len(undos) == 0 else undos[0]
