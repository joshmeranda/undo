from .pattern import *

import argparse


class _UndoArgumentParser(argparse.ArgumentParser):
    """Simple child class of ArgumentParser designed to allow for handling argument parsing error."""

    def error(self, message):
        raise argparse.ArgumentError(None, message)


def pattern_to_argparse(command_pattern: CommandPattern) -> argparse.ArgumentParser:
    """Converts the given command pattern to an ArgumentParser.

    Since we do not want the argument parser to exit when a given command does not match any pattern, the
    `exit_on_error` parameter is set to `False` on all returned parsers. Note that due to bgo-41255 there are still
    remaining issues with the `exit_on_error` kwarg and so this subclass with overridden `exit` and `error` methods
    is needed.

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

        if arg.arg_num.quantifier == Quantifier.ANY:
            kwargs["nargs"] = "*"
        elif arg.arg_num.quantifier == Quantifier.AT_LEAST_ONE:
            kwargs["nargs"] = "+"
        elif arg.arg_num.count == 0:
            kwargs["action"] = "store_true"
        elif arg.arg_num.count == 1:
            kwargs["nargs"] = None
        elif arg.arg_num.count > 1:
            kwargs["nargs"] = arg.arg_num.count

        if not arg.is_positional:
            kwargs["required"] = arg.is_required
            kwargs["dest"] = arg.var_name

        parser.add_argument(*names, **kwargs)

    return base_parser
