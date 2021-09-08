import dataclasses
import enum
import re
import typing


class PatternError(ValueError):
    """Raise for any error when parsing patterns."""


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

    def __repr__(self):
        return f"{type(self).__name__}({', '.join([f'{name}: {repr(value)}' for name, value in vars(self).items() if name[0] != '_'])})"

    def __eq__(self, other) -> bool:
        return (isinstance(other, ArgNum)
                and self.quantifier == other.quantifier
                and self.count == other.count)


@dataclasses.dataclass
class ArgumentPattern:
    # if var_name is optional, it should be assigned in order from 1 - n in the calling method / class
    var_name: typing.Optional[str]

    # todo: rare cases have more than one long and or short argument name
    arg_num: typing.Union[ArgNum, int]

    args: list[str]

    is_positional: bool
    is_required: bool

    # the delim to use when splitting a list argument into each list element
    delim: typing.Optional[str]


@dataclasses.dataclass
class ArgumentGroupPattern:
    is_exclusive: bool

    is_required: bool

    args: list[ArgumentPattern]


@dataclasses.dataclass
class CommandPattern:
    command: str

    sub_commands: list[str]

    arguments: list[ArgumentPattern]

    groups: list[ArgumentGroupPattern]


__COMMAND_REGEX = re.compile("([a-zA-Z0-9_-]*)")

__IDENTIFIER_REGEX = re.compile("[A-Z]+")
__QUANTIFIER_REGEX = re.compile(r"\*|\?|\.\.\.|[1-9][0-9]*")

__DELIM_REGEX = re.compile(r":(.*):")

__SHORT_REGEX = r"-[a-zA-Z0-9]"
__LONG_REGEX = r"--[a-zA-Z0-9][a-zA-Z0-9]+(-[a-zA-Z0-9][a-zA-Z0-9]+)*"

__ARG_REGEX = re.compile(rf"{__SHORT_REGEX}|"
                         rf"{__LONG_REGEX}")


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
    """Parse an ArgNum from the given str."""
    match = __QUANTIFIER_REGEX.match(content)

    if match is None:
        return ArgNum(Quantifier.N, 1), 0

    quantifier = content[match.start(): match.end()]

    if quantifier == '?':
        arg_num = ArgNum(Quantifier.N, 0)
    elif quantifier == '...':
        arg_num = ArgNum(Quantifier.AT_LEAST_ONE)
    elif quantifier == "*":
        arg_num = ArgNum(Quantifier.ANY)
    else:
        arg_num = ArgNum(Quantifier.N, int(quantifier))

    return arg_num, len(quantifier)


def __parse_delim(content: str) -> (str, int):
    """Parse a list delimiter from the given str."""
    match = __DELIM_REGEX.match(content)

    if match is None:
        return None, 0

    delim = match.group(1)

    return (delim if delim else None,
            max(match.end() - match.start(), 1))  # if


def __parse_arg_names(content: str) -> (list[str], int):
    """Parse a list of the short and long argument names with the preceding dashes, empty names are ignored."""
    names = list()

    for name in content.split():
        if __ARG_REGEX.fullmatch(name) is None:
            raise PatternError(f"'{name}' is not a valid argument name")

        names.append(name)

    return names, len(content)


def parse_argument(content: str) -> (ArgumentPattern, int):
    """Attempt to parse an ArgumentPattern from a str.

    Note: expects to receive the surrounding bracket (ie "[-d,--dir]" not "-d,--dir")

    Basic syntax follows this:

        OPEN_BRACE := '<' | '/'
        CLOSE_BRACE := '>' | ']'

        IDENTIFIER := [A-Z]+

        QUANTIFIER := '' | '?' | '...' | '*'

        SHORT := '-[a-zA-Z0-9]'
        LONG := '--[a-zA-Z][a-zA-Z-]*'

        PATTERN := OPEN_BRACE IDENTIFIER? QUANTIFIER? ':'? (SHORT | LONG)* CLOSE_BRACE

    :param content: teh string content to be parsed.
    :return: the parsed ArgumentPattern if successful.
    """
    if len(content) == 0:
        raise PatternError("content may not be empty")

    if content[0] not in "[<" or content[-1] not in "]>":
        raise PatternError("argument pattern must be wrapped in '[ ]' or '< >'")

    open_brace = content[0]
    close_brace = content[-1]

    if open_brace == "<" and close_brace != ">" or open_brace == "[" and close_brace != "]":
        raise PatternError(f"mismatching brace types, found '{open_brace}' and '{close_brace}'")

    is_required = open_brace == "<"

    offset = 1

    ident, size = __parse_identifier(content[offset: -1])
    offset += size

    arg_num, size = __parse_arg_num(content[offset: -1])
    offset += size

    delim = None

    if content[offset] == ":":
        delim, size = __parse_delim(content[offset:])

        # if no delim is found add 1
        offset += max(size, 1)

    args, size = __parse_arg_names(content[offset: -1])

    # adding +1 to incorporate the closing brace into the offset
    offset += size + 1

    is_positional = len(args) == 0

    if is_positional and not is_required:
        raise PatternError("a positional argument may not be optional, you may specify either '?' or '*' as quantifiers")

    if ident is None and len(args) > 0:
        ident = (max(args, key=lambda l: len(l)).lstrip('-')
                 .upper().replace("-", "_"))

    return ArgumentPattern(ident, arg_num, args, is_positional, is_required, delim), offset


def parse_argument_group_pattern(content: str) -> (ArgumentGroupPattern, int):
    """Attempt to parse an ArgumentGroup from a str.

    Node: expected to receive the surrounding parentheses.

    Basic grammar:

        EXCLUSIVE := '!'

        GROUP_PATTERN := '(' EXCLUSIVE? ARGUMENT_PATTERN+ ')'

    :param content: the content to parse.
    :return: The parsed ArgumentGroupPattern and the offset pointing to the next character in content.
    """

    if len(content) == 0:
        raise PatternError("content may not be empty")

    if content[0] not in "({" or content[-1] not in ")}":
        raise PatternError("argument group pattern must be wrapped '( )' or '{ }'")

    open_brace = content[0]
    close_brace = content[-1]

    if open_brace == "(" and close_brace != ")" or open_brace == "{" and close_brace != "}":
        raise PatternError(f"mismatching brace types, found '{open_brace}' and '{close_brace}'")

    is_required = open_brace == "{"

    offset = 1

    if content[1] == "!":
        is_exclusive = True
        offset += 1
    else:
        is_exclusive = False

    arguments = list()
    while offset < len(content) - 1:
        if content[offset].isspace():
            offset += 1
            continue

        arg_match = re.match(r"([\[<].*?[]>])",
                             content[offset::])

        if arg_match is not None:
            arg, size = parse_argument(arg_match.group(1))
            offset += size

            arguments.append(arg)
            continue
        else:
            raise PatternError(f"could not parse arguments in group '{content}'")

    offset += 1

    return ArgumentGroupPattern(is_exclusive, is_required, arguments), offset


def parse_commands(content: str) -> (str, list[str], int):
    """Parse the command and sub_commands from the given content.

    :param content; the content to parse.
    :return: the parsed command, and the index of the next meaningful character in the string.
    """

    cmd_match = re.match(rf"\s*([a-zA-Z0-9_-]*)\s*", content)
    sub_cmd_match = re.match(r"((?:[a-zA-Z0-9_-]*\s*)*)\s*", content[cmd_match.end()::])

    command = cmd_match.group(1)
    sub_commands = sub_cmd_match.group(1).split()
    offset = cmd_match.end() + sub_cmd_match.end()

    return command, sub_commands, offset


def parse_command_pattern(content: str) -> CommandPattern:
    """Attempt to parse a CommandPattern from a str.

    :param content: the content to parse.
    :return: the parsed CommandPattern.
    :raise: PatternError on any error parsing input.
    """
    if len(content) == 0:
        raise PatternError("content may not be empty")

    command, sub_commands, offset = parse_commands(content)

    arguments = list()
    groups = list()

    while offset < len(content):
        if content[offset].isspace():
            offset += 1
            continue

        # check for an argument
        arg_match = re.match(r"([\[<].*?[]>])",
                             content[offset::])

        if arg_match is not None:
            arg, size = parse_argument(arg_match.group(1))
            offset += size

            arguments.append(arg)
            continue

        group_match = re.match(r"([({].*?[)}])",
                               content[offset::])

        if group_match is not None:
            group, size = parse_argument_group_pattern(group_match.group(1))
            offset += size

            groups.append(group)
            continue

        offset += 1

    return CommandPattern(command, sub_commands, arguments, groups)
