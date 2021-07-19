from __future__ import annotations

import dataclasses
import enum
import re
import typing


class Quantifier(enum.Enum):
    N = 1
    AtLeastOne = 2
    Any = 3


class ArgNum:
    def __init__(self, quantifier: Quantifier, count: typing.Optional[int] = None):
        """Describes the amount of values for a command argument.

        :param quantifier: describes the type of value quantity.
        :param count: the optional amount of arguments (defaults to None), if quantifier is not Quantifier.N this
            parameter is ignored.
        :raises
        """
        self.quantifier = quantifier

        if self.quantifier == Quantifier.N:
            if count is None:
                raise ValueError("'count' must not be None when quantifier is N")

            if count < 0:
                raise ValueError("'count' must be >= 0 but was '{count}'")
            self.count = count
        else:
            self.count = None

    def __eq__(self, other):
        return isinstance(other, ArgNum) and self.quantifier == other.quantifier and self.count == other.count


@dataclasses.dataclass
class ArgumentPattern:
    # if var_name is optional, it should be assigned in order from 1 - n in the calling method / class
    var_name: typing.Optional[str]

    # todo: rare cases have more than one long and or short argument name
    arg_num: typing.Union[ArgNum, int]

    args: list[str]

    is_positional: bool
    is_required: bool


class ArgumentPatternParser:
    """A parser for an argument pattern."""

    __IDENTIFIER_REGEX = re.compile("[A-Z]+")
    __QUANTIFIER_REGEX = re.compile(r"\+|\?|\.\.\.|[1-9][0-9]*")

    __SHORT_REGEX = r"-[a-zA-Z0-9]"
    __LONG_REGEX = r"--[a-zA-Z0-9][a-zA-Z0-9]+(-[a-zA-Z0-9][a-zA-Z0-9]+)*"
    __ARG_REGEX = re.compile(rf"{__SHORT_REGEX}|{__LONG_REGEX}")

    def __parse_identifier(self, content: str) -> (typing.Optional[str], int):
        """Attempt to parse an identifier from th given str.

        Note: this method may return None as there is no guarantee that an identifier is provided by the user, and the
        fallback identifiers have not yet been parsed.
        """
        match = re.match(ArgumentPatternParser.__IDENTIFIER_REGEX, content)

        if match is None:
            return None, 0
        else:
            return content[match.start(): match.end()], match.end()

    def __parse_quantifier(self, content: str) -> (ArgNum, int):
        """Parse a qualifier from the given str."""
        match = re.match(ArgumentPatternParser.__QUANTIFIER_REGEX, content)

        if match is None:
            return ArgNum(Quantifier.N, 1), 0

        quantifier = content[match.start(): match.end()]

        if quantifier == "?":
            arg_num = ArgNum(Quantifier.N, 0)
        elif quantifier == '+':
            arg_num = ArgNum(Quantifier.AtLeastOne)
        elif quantifier == "...":
            arg_num = ArgNum(Quantifier.Any)
        else:
            arg_num = ArgNum(Quantifier.N, int(quantifier))

        return arg_num, len(quantifier)

    def __parse_args(self, content: str) -> list[str]:
        """Parse a list of the short and long argument names without the preceding dashes."""

        if len(content) == 0:
            return list()

        # todo: ignore whitespace when splitting
        all_args = content.split(",")

        for arg in all_args:
            if ArgumentPatternParser.__ARG_REGEX.fullmatch(arg) is None:
                raise ValueError(f"'{arg}' is not a valid long or short argument name")

        return all_args

    def parse(self, content: str) -> ArgumentPattern:
        """Attempt to parse an ArgumentPattern from a str.

        Note: expects to receive the surrounding bracket (ie "[-d,--dir]" not "-d,--dir")

        Basic syntax follows this:

            OPEN_BRACE := '<' | '/'
            CLOSE_BRACE := '>' | ']'

            IDENTIFIER := [A-Z]+

            QUANTIFIER := '' | '?' | '...'

            SHORT := '-[a-zA-Z0-9]'
            LONG := '--[a-zA-Z][a-zA-Z-]*'

            PATTERN := OPEN_BRACE IDENTIFIER? QUANTIFIER? ':'? (SHORT | LONG)* CLOSE_BRACE

        :param content: teh string content to be parsed.
        :return: the parsed ArgumentPattern if successful.
        :raise: todo: this should raise an extension of a ValueError
        """

        if len(content) == 0:
            raise ValueError("content amy not be empty")

        if content[0] not in "[<" or content[-1] not in "]>":
            raise ValueError("content must wrapped in '[]' or '<>'")

        open_brace = content[0]
        close_brace = content[-1]

        if open_brace == "<" and close_brace != ">" or open_brace == "[" and close_brace != "]":
            raise ValueError(f"mismatching brace types, found '{open_brace}' and '{close_brace}")

        is_required = open_brace == "<"

        offset = 1

        ident, size = self.__parse_identifier(content[offset:-1])
        offset += size

        quantifier, size = self.__parse_quantifier(content[offset:-1])
        offset += size

        if content[offset] == ":":
            offset += 1

        args = self.__parse_args(content[offset:-1])

        is_positional = len(args) == 0

        if ident is None and len(args) > 0:
            ident = max(args, key=lambda l: len(l)).lstrip("-").upper()

        return ArgumentPattern(ident, quantifier, args, is_positional, is_required)


@dataclasses.dataclass
class CommandPattern:
    command: str
    sub_commands: list[str]
    arguments: list[ArgumentPattern]


class CommandPatternParser:

    def __init__(self, arg_parser: ArgumentPatternParser):
        self.__arg_parser = arg_parser

    def parse(self, content: str) -> CommandPattern:
        argv = content.split()

        command = argv[0]

        sub_commands = [arg for arg in argv[1:] if arg[0] not in "{<"]
        arguments = [self.__arg_parser.parse(arg) for arg in argv[len(sub_commands) + 1:]]

        return CommandPattern(command, sub_commands, arguments)
