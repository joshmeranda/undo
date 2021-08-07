import dataclasses
import enum
import re
import typing


class Quantifier(enum.Enum):
    N = 1
    AT_LEAST_ONE = 2
    ANY = 3


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

    def __eq__(self, other) -> bool:
        return (isinstance(other, ArgNum)
                and self.quantifier == other.quantifier
                and self.count == other.count)


# todo: may need to support argument groups
@dataclasses.dataclass
class ArgumentPattern:
    # if var_name is optional, it should be assigned in order from 1 - n in the calling method / class
    var_name: typing.Optional[str]

    # todo: rare cases have more than one long and or short argument name
    arg_num: typing.Union[ArgNum, int]

    args: list[str]

    is_positional: bool
    is_required: bool


@dataclasses.dataclass
class CommandPattern:
    command: str
    sub_commands: list[str]
    arguments: list[ArgumentPattern]


__IDENTIFIER_REGEX = re.compile("[A-Z]+")
__QUANTIFIER_REGEX = re.compile(r"\+|\?|\.\.\.|[1-9][0-9]*")

__SHORT_REGEX = r"-[a-zA-Z0-9]"
__LONG_REGEX = r"--[a-zA-Z0-9][a-zA-Z0-9]+(-[a-zA-Z0-9][a-zA-Z0-9]+)*"
__ARG_REGEX = re.compile(rf"{__SHORT_REGEX}|{__LONG_REGEX}")


def __parse_identifier(content: str) -> (typing.Optional[str], int):
    """Attempt to parse an identifier from th given str.

    Note: this method may return None as there is no guarantee that an identifier is provided by the user, and the
    fallback identifiers have not yet been parsed.
    """
    match = __IDENTIFIER_REGEX.match(content)

    if match is None:
        return None, 0
    else:
        return content[match.start(): match.end()], match.end()


def __parse_arg_num(content: str) -> (ArgNum, int):
    """Parse an ArgNum from teh given str."""
    match = __QUANTIFIER_REGEX.match(content)

    if match is None:
        return ArgNum(Quantifier.N, 1), 0

    quantifier = content[match.start(): match.end()]

    if quantifier == '?':
        arg_num = ArgNum(Quantifier.N, 0)
    elif quantifier == '+':
        arg_num = ArgNum(Quantifier.AT_LEAST_ONE)
    elif quantifier == "...":
        arg_num = ArgNum(Quantifier.ANY)
    else:
        arg_num = ArgNum(Quantifier.N, int(quantifier))

    return arg_num, len(quantifier)


def __parse_args(content: str) -> list[str]:
    """Parse a list of the short and long argument names with the preceding dashes."""

    if len(content) == 0:
        return list()

    # todo: ignore whitespace?
    all_args = [arg for arg in content.split(',')]

    for arg in all_args:
        if __ARG_REGEX.fullmatch(arg) is None:
            raise ValueError(f"'{arg}' is not a valid long or short argument name")

    return all_args


def parse_argument(content: str) -> ArgumentPattern:
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
        raise ValueError("content may not be empty")

    if content[0] not in "[<" or content[-1] not in "]>":
        raise ValueError("content must be wrapped in '[]' or '<>'")

    open_brace = content[0]
    close_brace = content[-1]

    if open_brace == "<" and close_brace != ">" or open_brace == "[" and close_brace != "]":
        raise ValueError(f"mismatching brace types, found '{open_brace}' and '{close_brace}'")

    is_required = open_brace == "<"

    offset = 1

    ident, size = __parse_identifier(content[offset: -1])
    offset += size

    arg_num, size = __parse_arg_num(content[offset: -1])
    offset += size

    if content[offset] == ":":
        offset += 1

    args = __parse_args(content[offset: -1])

    is_positional = len(args) == 0

    if is_positional and not is_required:
        raise ValueError("a positional argument may not be optional, you may specify either '?' or '*' as quantifiers")

    if ident is None and len(args) > 0:
        ident = (max(args, key=lambda l: len(l)).lstrip('-')
                 .upper().replace("-", "_"))

    return ArgumentPattern(ident, arg_num, args, is_positional, is_required)


def parse_command_pattern(content: str, arg_parser: typing.Callable[[str], ArgumentPattern] = parse_argument) -> CommandPattern:
    """Attempt to parse a CommandPattern from a str.

    :param content: the content to parse.
    :param arg_parser: the method to use when parsing each argument pattern (defaults to pattern.parse_argument)
    :return: the parsed CommandPattern.
    :raise: ValueError on any error parsing input.
    """
    if len(content) == 0:
        raise ValueError("content may not be empty")

    argv = content.split()

    command = argv[0]

    sub_commands = [arg for arg in argv[1:] if arg[0] not in "[<"]
    arguments = [arg_parser(arg) for arg in argv[len(sub_commands) + 1:]]

    return CommandPattern(command, sub_commands, arguments)
