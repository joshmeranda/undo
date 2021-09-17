import dataclasses
import enum
import re
import typing

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Errors                                                                      #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class PatternError(ValueError):
    """Raise for any error when parsing patterns."""


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Objects                                                                     #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class Quantifier(enum.Enum):
    FLAG = enum.auto()
    OPTIONAL = enum.auto()
    AT_LEAST_ONE = enum.auto()
    ANY = enum.auto()
    N = enum.auto()


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

    arg_num: typing.Union[ArgNum, int]

    args: list[str]

    is_positional: bool
    is_required: bool

    # the delim to use when splitting a list argument into each list element
    delim: typing.Optional[str]


@dataclasses.dataclass
class ArgumentGroupPattern:
    is_required: bool

    args: list[ArgumentPattern]


@dataclasses.dataclass
class CommandPattern:
    command: str

    sub_commands: list[str]

    arguments: list[ArgumentPattern]

    groups: list[ArgumentGroupPattern]


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Regex                                                                       #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

__COMMAND_REGEX = re.compile("([a-zA-Z0-9_-]*)")

__IDENTIFIER_REGEX = re.compile("[a-zA-Z_]+")
__QUANTIFIER_REGEX = re.compile(r"\.\.\.|"
                                r"\*|"
                                r"{([0-9]+)}")

__SHORT_REGEX = r"-[a-zA-Z0-9]"
__LONG_REGEX = r"--[a-zA-Z0-9][a-zA-Z0-9\-]*"

__ARG_REGEX = re.compile(rf"{__SHORT_REGEX}|"
                         rf"{__LONG_REGEX}")

__DELIM_REGEX = re.compile(r":(.*)[\]>]")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Parsing                                                                     #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def __parse_names(content: str) -> (list[str], int):
    """Parse the list of argument names leaving the leading '-' in tact."""
    offset = 0

    names = list()

    while offset < len(content) and content[offset] not in "[=:]>":
        if content[offset].isspace():
            offset += 1
            continue

        m = __ARG_REGEX.match(content[offset::])

        if m is None:
            break

        names.append(m.string[m.start(): m.end()])
        offset += m.end()

    return names, offset


def __parse_arg_num(content: str, is_optional: bool, is_flag: bool) -> (ArgNum, int):
    """Parse the quantifier for the argument."""
    match = __QUANTIFIER_REGEX.match(content)

    n = None
    offset = 0

    if match is None:
        if is_flag:
            quantifier = Quantifier.FLAG
        elif is_optional:
            quantifier = Quantifier.OPTIONAL
        else:
            quantifier = Quantifier.N
            n = 1
    else:
        body = match.string[:match.end()]

        if body == "...":
            quantifier = Quantifier.ANY if is_optional else Quantifier.AT_LEAST_ONE
            offset = 3
        elif body == "*":
            quantifier = Quantifier.ANY
            offset = 1
        elif body[0] == "{":
            quantifier = Quantifier.N

            try:
                n = int(match.group(1))
            except ValueError as err:
                raise PatternError(f"bad quantifier: {err}")

            offset = match.end()
        else:
            raise PatternError(f"unknown quantifier found: '{match.string[:match.end()]}")

    if is_optional and (quantifier == Quantifier.N and n != 1):
        raise PatternError("optional argument values must only have a Quantifier of 1")

    return ArgNum(quantifier, n), offset


def __parse_var(content: str, is_positional: bool) -> (typing.Optional[str], ArgNum, int):
    """Parse the argument's meta var and argument count."""
    if content[0] in "]>":
        return None, ArgNum(Quantifier.FLAG), 0

    offset = 0

    has_brace = False
    has_equal = False

    if content[offset] == "[":
        has_brace = True
        offset += 1

    if content[offset] == "=":
        has_equal = True
        offset += 1

    if not is_positional and not has_brace and not has_equal:
        raise PatternError(f"non-positional arguments with quantifier != 1 must have either '[', '=', or '[=' but found"
                           f"'{content[offset]}'")

    if (match := __IDENTIFIER_REGEX.match(content[offset::])) is not None:
        ident = match.string[:match.end():]
        offset += match.end()
    else:
        ident = None

    arg_num, size = __parse_arg_num(content[offset::],
                                    (has_equal or is_positional) and has_brace,
                                    not has_equal and not is_positional)
    offset += size

    if has_brace and content[offset] != "]":
        raise PatternError(f"expected ']' but found '{content[offset]}")
    elif has_brace:
        offset += 1

    return ident, arg_num, offset


def __parse_delim(content: str) -> (typing.Optional[str], int):
    """Parse a list delimiter from the given str."""
    match = __DELIM_REGEX.match(content)

    if match is None:
        return None, 0

    delim = match.group(1)

    offset = len(delim) + 1  # length of delimiter + initial ':'

    return delim if delim else None, offset


def parse_argument_pattern(content: str) -> (ArgumentPattern, int):
    """Attempt to parse an ArgumentPattern from a str.

    Note: expects to receive the surrounding bracket (ie "[-d --dir]" not "-d --dir")

    Grammar:
        OPEN_BRACE := '[' | '<'
        CLOSE_BRACE := ']' | '>'

        IDENTIFIER := [A-Za-z_]+

        SHORT := '-[a-zA-Z0-9]'
        LONG := '--[a-zA-Z][a-zA-Z-]*'

        N := '{' [0-9]+ '}'

        DELIM := ':' + .*

        PATTER := OPEN_BRACE (SHORT | LONG)* '['? '='? IDENT? N? ']' DELIM? CLOSE_BRACE

    :param content: the string to parse.
    :return: the parsed ArgumentPattern if successful.
    """
    if len(content) == 0:
        raise PatternError("content may not be empty")

    if content[0] not in "[<" or content[-1] not in "]>":
        raise PatternError("argument pattern must be wrapped in '[ ]' or '< >'")

    open_brace = content[0]

    is_required = open_brace == "<"

    offset = 1

    names, size = __parse_names(content[offset::])
    offset += size

    is_positional = len(names) == 0

    ident, arg_num, size = __parse_var(content[offset::], is_positional)
    offset += size

    delim, size = __parse_delim(content[offset::])
    offset += size

    try:
        if (close_brace := content[offset]) in "]>":
            if open_brace == "<" and close_brace != ">" or open_brace == "[" and close_brace != "]":
                raise PatternError(f"mismatching brace types, found '{open_brace}' and '{close_brace}'")

            offset += 1
        else:
            raise PatternError(f"expected '{']' if open_brace == '[' else '>'}' but found '{content[offset]}")
    except IndexError as err:
        raise PatternError(f"error parsing arguments pattern: {err}")

    if is_positional and not is_required:
        raise PatternError("a positional argument may not be optional, you may specify either '?' or '*' as quantifiers")

    if ident is None and len(names) > 0:
        ident = (max(names, key=lambda l: len(l)).lstrip('-')
                 .upper().replace("-", "_"))

    return ArgumentPattern(ident, arg_num, names, is_positional, is_required, delim), offset


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

    if content[0] != "(" or content[-1] != ")":
        raise PatternError("argument group pattern must be wrapped '( )'")

    if content[1] == "!":
        is_required = True
        offset = 2
    else:
        is_required = False
        offset = 1

    arguments = list()
    while offset < len(content) - 1:
        if content[offset].isspace():
            offset += 1
            continue

        arg_match = re.match(r"([\[<].*[]>])",

                             content[offset::])

        if arg_match is not None:
            arg, size = parse_argument_pattern(arg_match.group(1))
            offset += size

            arguments.append(arg)
            continue
        else:
            raise PatternError(f"could not parse arguments in group '{content}'")

    offset += 1

    return ArgumentGroupPattern(is_required, arguments), offset


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
            arg, size = parse_argument_pattern(arg_match.group(1))
            offset += size

            arguments.append(arg)
            continue

        group_match = re.match(r"(\(.*?\))",
                               content[offset::])

        if group_match is not None:
            group, size = parse_argument_group_pattern(group_match.group(1))
            offset += size

            groups.append(group)
            continue

        raise PatternError(f"unexpected value '{content[offset]}'")

    return CommandPattern(command, sub_commands, arguments, groups)
