from .pattern import *

import argparse


# def __add_arg_to_parser(parser, arg: ArgumentPattern, positional_count: int):
#     """Add an ArgumentPattern to the parser.
# 
#     :parser: the target parser.
#     :param arg: the argument pattern to add to the parser.
#     :param positional_count: the next number for a positional argument with n given name.
#     """
#     if arg.is_positional:
#         if arg.var_name is not None:
#             names = [arg.var_name]
#         else:
#             names = str(positional_count)
# 
#         positional_count += 1
#     else:
#         names = arg.args
# 
#     kwargs = dict()
# 
#     if arg.arg_num.quantifier == Quantifier.ANY:
#         kwargs["nargs"] = "*"
# 
#         if arg.delim is not None and arg.delim != " ":
#             kwargs["nargs"] = "?"
#             kwargs["const"] = []
#             kwargs["type"] = lambda s: [i for i in s.split(arg.delim) if i]
#     elif arg.arg_num.quantifier == Quantifier.AT_LEAST_ONE:
#         kwargs["nargs"] = "+"
# 
#         if arg.delim is not None:
#             kwargs["nargs"] = None
#             kwargs["type"] = lambda s: [i for i in s.split(arg.delim) if i]
#     elif arg.arg_num.count == 0:
#         kwargs["action"] = "store_true"
#     elif arg.arg_num.count == 1:
#         kwargs["nargs"] = None
#     elif arg.arg_num.count > 1:
#         kwargs["nargs"] = arg.arg_num.count
# 
#     if not arg.is_positional:
#         kwargs["required"] = arg.is_required
#         kwargs["dest"] = arg.var_name
# 
#     parser.add_argument(*names, **kwargs)


# def __add_group_to_parser(parser, group: ArgumentGroupPattern, positional_count: int):
#     """Add an ArgumentGroupPattern to the parser.
# 
#     :param parser: the target parser.
#     :param group: the ArgumentGroupPattern to add to the parser.
#     :param positional_count: the next number for a positional argument with n given name.
#     """
#     group_parser = parser.add_mutually_exclusive_group(required=group.is_required)
# 
#     for arg in group.args:
#         __add_arg_to_parser(group_parser, arg, positional_count)


class _UndoArgumentParser(argparse.ArgumentParser):
    """Simple child class of ArgumentParser designed to allow for handling argument parsing error."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__required_groups: list[list[ArgumentPattern]] = list()
        self.__positional_count: int = 0

    def add_argument_pattern(self, arg: ArgumentPattern):
        """Add an ArgumentPattern to the parser.

        :parser: the target parser.
        :param arg: the argument pattern to add to the parser.
        """
        if arg.is_positional:
            if arg.var_name is not None:
                names = [arg.var_name]
            else:
                names = str(self.__positional_count)

            self.__positional_count += 1
        else:
            names = arg.args

        kwargs = dict()

        if arg.arg_num.quantifier == Quantifier.ANY:
            kwargs["nargs"] = "*"

            if arg.delim is not None and arg.delim != " ":
                kwargs["nargs"] = "?"
                kwargs["const"] = []
                kwargs["type"] = lambda s: [i for i in s.split(arg.delim) if i]
        elif arg.arg_num.quantifier == Quantifier.AT_LEAST_ONE:
            kwargs["nargs"] = "+"

            if arg.delim is not None:
                kwargs["nargs"] = None
                kwargs["type"] = lambda s: [i for i in s.split(arg.delim) if i]
        elif arg.arg_num.count == 0:
            kwargs["action"] = "store_true"
        elif arg.arg_num.count == 1:
            kwargs["nargs"] = None
        elif arg.arg_num.count > 1:
            kwargs["nargs"] = arg.arg_num.count

        if not arg.is_positional:
            kwargs["required"] = arg.is_required
            kwargs["dest"] = arg.var_name

        self.add_argument(*names, **kwargs)

    def add_argument_group_pattern(self, group: ArgumentGroupPattern):
        """Add an ArgumentGroupPattern to the parser.

        :param group: the ArgumentGroupPattern to add to the parser.
        """
        if group.is_required:
            self.__required_groups.append([arg for arg in group.args])

        for arg in group.args:
            if arg.is_required:
                self.error(f"")
            self.add_argument_pattern(arg)

    def parse_args(self, args=None, namespace=None):
        namespace = super().parse_args(args, namespace)

        # ensure that at least one of the required group arguments are present
        for group in self.__required_groups:
            group_found = False

            for arg in group:
                if arg.var_name in vars(namespace) and vars(namespace)[arg.var_name]:

                    group_found = True
                    break

            if not group_found:
                self.error(f"expected at least one of {' '.join(name for arg in group for name in arg.args)}")

        return namespace

    def error(self, message):
        raise argparse.ArgumentError(None, message)


def pattern_to_argparse(command_pattern: CommandPattern) -> argparse.ArgumentParser:
    """Converts the given command pattern to an ArgumentParser.

    Since we do not want the argument parser to exit when a given command does not match any pattern, the
    `exit_on_error` parameter is set to `False` on all returned parsers. Note that due to bgo-41255 there are still
    remaining issues with the `exit_on_error` kwarg and so this subclass with overridden `exit` and `error` methods
    is needed.

    todo: test if setting "help" arguments to "''" rather than None is faster
    todo: will need to handle and test for repeated arguments

    :param command_pattern: the source CommandPattern to build the ArgumentParser from.
    :return: The built ArgumentParser.
    """
    base_parser = _UndoArgumentParser(prog=command_pattern.command, exit_on_error=False, add_help=False)
    parser = base_parser

    for sub_command in command_pattern.sub_commands:
        sub_parser = parser.add_subparsers(dest="command", required=True, parser_class=_UndoArgumentParser)

        parser = sub_parser.add_parser(sub_command)

    for arg in command_pattern.arguments:
        parser.add_argument_pattern(arg)

    for group in command_pattern.groups:
        parser.add_argument_group_pattern(group)

    return base_parser
