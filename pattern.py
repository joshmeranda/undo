from __future__ import annotations

import dataclasses
import enum
import re
import typing


class ArgNum(enum.Enum):
    Flag = 0
    One = 1
    Many = 2


@dataclasses.dataclass
class ArgumentPattern:
    # if var_name is optional, it should be assigned in order from 1 - n in the calling method / class
    var_name: typing.Optional[str]

    # todo: rare cases have more than one long and or short argument name
    arg_num: ArgNum

    args: list[str]

    is_positional: bool
    is_required: bool


class ArgumentPatternParser:
    """A parser for an argument pattern."""

    __IDENTIFIER_REGEX = re.compile("[A-Z]+")
    __QUANTIFIER_REGEX = re.compile(r"\?|\.\.\.")

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
            return ArgNum.One, 0

        quantifier = content[match.start(): match.end()]

        if quantifier == "?":
            return ArgNum.Flag, 1
        elif quantifier == "...":
            return ArgNum.Many, 3
        else:
            raise ValueError(f"unexpected quantifier value '{quantifier}'")

    def __parse_args(self, content: str) -> list[str]:
        """Parse a list of the short and long argument names without the preceding dashes."""

        if len(content) == 0:
            return list()

        # todo: ignore whitespace when splitting
        all_args = content.split("|")

        for arg in all_args:
            if ArgumentPatternParser.__ARG_REGEX.fullmatch(arg) is None:
                raise ValueError(f"'{arg}' is not a valid long or short argument name")

        return all_args

    def parse(self, content: str) -> ArgumentPattern:
        """Attempt to parse an ArgumentPattern from a str.

        Note: expects to receive the surrounding bracket (ie "[-d|--dir]" not "-d|--dir")

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

        qualifier, size = self.__parse_quantifier(content[offset:-1])
        offset += size

        if content[offset] == ":":
            offset += 1

        args = self.__parse_args(content[offset:-1])

        is_positional = len(args) == 0

        if ident is None and len(args) > 0:
            ident = max(args, key=lambda l: len(l)).lstrip("-").upper()

        return ArgumentPattern(ident, qualifier, args, is_required, is_positional)
