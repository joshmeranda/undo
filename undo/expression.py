import abc
import dataclasses
import enum
import os
import os.path
import re
import typing


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Tokenization classes                                                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
from undo import expand


class TokenKind(enum.Enum):
    IDENT = enum.auto()
    ELLIPSE = enum.auto()
    COMMA = enum.auto()

    STRING_LITERAL = enum.auto()
    STRING_EXPANSION = enum.auto()

    OPEN_PARENTHESE = enum.auto()
    CLOSE_PARENTHESE = enum.auto()

    COMMAND = enum.auto()

    AND = enum.auto()
    OR = enum.auto()
    NOT = enum.auto()

    TERNARY_IF = enum.auto()
    TERNARY_ELSE = enum.auto()

    ACCESSOR = enum.auto()

    # Unknown is only used to allow for passing a token to TokenError.
    UNKNOWN = enum.auto()


@dataclasses.dataclass
class Token:
    """Represents a single token in an expression.
    todo: todo add support for multiple lines for cleaner expressions
    """
    kind: TokenKind
    body: str
    col: int


__IDENT_REGEX = r"[a-zA-Z0-9]([a-zA-Z0-9_])*"
__COMMAND_REGEX = r"dirname|basename|abspath|env|join|exists|isfile|isdir"
__STRING_LITERAL_REGEX = r"'.*?[^\\]'"
__STRING_EXPANSION_REGEX = r"\".*?[^\\]\""
__SYMBOL_REGEX = r"\$|\?|:|&&|\|\||!|\.\.\.|,|\(|\)"

__TOKEN_REGEX = re.compile(rf"\s*({__STRING_EXPANSION_REGEX}|"
                           rf"{__STRING_LITERAL_REGEX}|"
                           rf"{__COMMAND_REGEX}|"
                           rf"{__IDENT_REGEX}|"
                           rf"{__SYMBOL_REGEX})")


def __tokenize(content) -> list[Token]:
    """Split a string individual tokens."""
    offset = 0
    tokens = []

    while offset < len(content):
        m = __TOKEN_REGEX.match(content[offset:])

        if m is None:
            body = content[offset:].lstrip().split()[0]
            col = offset
            token = Token(TokenKind.UNKNOWN, body, col)

            raise TokenError(token, "Unknown token")

        raw_body = m.string[:m.end()]
        body = raw_body.strip()

        col = offset + 1 + m.end() - len(body)

        if body == "?":
            kind = TokenKind.TERNARY_IF
        elif body == ":":
            kind = TokenKind.TERNARY_ELSE
        elif body == "&&":
            kind = TokenKind.AND
        elif body == "||":
            kind = TokenKind.OR
        elif body == "!":
            kind = TokenKind.NOT
        elif body == "...":
            kind = TokenKind.ELLIPSE
        elif body == ",":
            kind = TokenKind.COMMA
        elif body == "(":
            kind = TokenKind.OPEN_PARENTHESE
        elif body == ")":
            kind = TokenKind.CLOSE_PARENTHESE
        elif body == "$":
            kind = TokenKind.ACCESSOR
        elif body in __COMMAND_REGEX.split("|"):
            kind = TokenKind.COMMAND
        elif body[0] == "'":
            kind = TokenKind.STRING_LITERAL
            body = body[1:-1]
        elif body[0] == "\"":
            kind = TokenKind.STRING_EXPANSION
            body = body[1:-1]
        else:
            kind = TokenKind.IDENT

        token = Token(kind, body, col)
        tokens.append(token)

        offset += m.end()

    return tokens


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Error classes                                                               #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class ExpressionError(ValueError):
    """Parent error for any error in parsing or evaluating an UndoException"""
    def __init__(self, message: str):
        super().__init__(message)


class TokenError(ExpressionError):
    """Raise for any error relating to token parsing."""
    def __init__(self, token: Token, message: str):
        self.token = token
        super().__init__(f"{message} at col {token.col}: '{token.body}'")


class ParseError(ExpressionError):
    """Raise for any error relating to expression parsing after tokenization."""


class UnexpectedTokenError(ParseError):
    def __init__(self, expected: TokenKind, actual: TokenKind):
        super().__init__(f"expected token of type '{expected}' but found '{actual}'")


class UnexpectedEndOfLineError(ParseError):
    def __init__(self):
        super().__init__("unexpected end of line")


class EvaluationError(ExpressionError):
    """Raise for any error that occurs during evaluation."""


class WrongArgumentNum(ExpressionError):
    def __init__(self, expected: int, actual: int):
        super().__init__(f"wrong argument count, expected {expected} but found {actual}")


class UnknownCommandException(EvaluationError):
    def __init__(self, command: Token):
        super().__init__(f"no such command '{command.body}' at col {command.col}")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Expression classes                                                          #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class UndoExpression(abc.ABC):
    """Represents an expression resulting in a string command."""

    def __repr__(self):
        return f"{type(self).__name__}({', '.join([f'{name}: {repr(value)}' for name, value in vars(self).items() if name[0] != '_'])})"


class ValueExpression(UndoExpression):
    """An expression that will produce a single string value"""

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> typing.Union[str, list[str]]:
        """Evaluate the result of the expression given the map of identifiers and values."""


class ConditionalExpression(UndoExpression):
    """An expression representing a chain of BooleanExpressions and operators."""

    def __init__(
            self, negate: bool, operator: typing.Optional[Token],
            right: typing.Optional['ConditionalExpression']):
        self.negate = negate
        self.operator = operator
        self.right = right

    def __eq__(self, other) -> bool:
        return (isinstance(other, ConditionalExpression)
                and self.negate and other.negate
                and self.operator == other.operator
                and self.right == other.right)

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> bool:
        """Evaluate the result of the expression given the map of identifier and values."""
        if self.operator.kind == TokenKind.AND:
            return (self.negate
                    and self.evaluate(env)
                    and self.right.evaluate(env))
        elif self.operator.kind == TokenKind.OR:
            return (self.negate
                    and self.evaluate(env)
                    or self.right.evaluate(env))
        elif self.operator.kind is None:
            return self.negate and self.evaluate(env)


# sub-classes


class AccessorExpression(ValueExpression):
    """A simple expression which will resolve to a value given an identifier."""

    def __init__(self, identifier: Token, list_expand: bool, delim: typing.Optional[str] = None):
        self.identifier = identifier
        self.list_expand = list_expand
        self.delim = delim

    def __eq__(self, other) -> bool:
        return(isinstance(other, AccessorExpression)
               and self.identifier == other.identifier
               and self.list_expand == other.list_expand
               and self.delim == other.delim)

    def no_expand_evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> typing.Union[str, list[str]]:
        """Same as evaluate expect that list expansion is not performed.

        Note that this means that responsibility to join the list value with the delimiter is passed to the caller.
        """
        return env.setdefault(self.identifier.body, "")

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> typing.Union[str, list[str]]:
        """Retrieve the value corresponding to this expression's identifier or "" if it does not exist in env."""
        val = env.setdefault(self.identifier.body, "")

        if self.list_expand and isinstance(val, list):
            if self.delim is None:
                raise ValueError(f"delim cannot be None when expanding list")

            return self.delim.join(val)

        return val


class TernaryExpression(ValueExpression):
    """An expression allowing for basic conditional expressions."""

    def __init__(self, condition: ConditionalExpression, if_value: ValueExpression, else_value: typing.Optional[ValueExpression]):
        self.condition = condition
        self.if_value = if_value
        self.else_value = else_value

    def __eq__(self, other) -> bool:
        return (isinstance(other, TernaryExpression)
                and self.condition == other.condition
                and self.if_value == other.if_value
                and self.else_value == other.else_value)

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> typing.Union[str, list[str]]:
        if self.condition.evaluate(env):
            return self.if_value.evaluate(env)
        else:
            return self.else_value.evaluate(env) if self.else_value is not None else ""


class StringLiteralExpression(ValueExpression):
    def __init__(self, token: Token):
        self.token = token

    def __eq__(self, other) -> bool:
        return (isinstance(other, StringLiteralExpression)
                and self.token == other.token)

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> typing.Union[str, list[str]]:
        return self.token.body


class StringExpansionExpression(ValueExpression):
    def __init__(self, token: Token):
        self.token = token

    def __eq__(self, other) -> bool:
        return (isinstance(other, StringExpansionExpression)
                and self.token == other.token)

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> typing.Union[str, list[str]]:
        return expand.expand(self.token.body, env, (r"`", r"`"), None)


class ExistenceExpression(ConditionalExpression):
    """An expression which evaluates if a value for the given identifier has been set."""

    def __init__(self, negate: bool, identifier: Token,
                 operator: typing.Optional[Token] = None, right: typing.Optional[ConditionalExpression] = None):
        super().__init__(negate, operator, right)
        self.identifier = identifier

    def __eq__(self, other) -> bool:
        return (isinstance(other, ExistenceExpression)
                and self.identifier == other.identifier
                and self.operator == other.operator
                and self.right == other.right)

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> bool:
        if self.negate:
            return env.setdefault(self.identifier.body, "") == ""
        else:
            return env.setdefault(self.identifier.body, "") != ""


# command-expressions


class CommandExpression(abc.ABC):
    """An expression which will generate values based on inputs."""

    def __init__(self, command: Token, arguments: list[ValueExpression]):
        self.command = command
        self.arguments = arguments

    def __eq__(self, other) -> bool:
        return (isinstance(other, CommandExpression)
                and self.command == other.command
                and self.arguments == other.arguments)


class ValueCommandExpression(CommandExpression, ValueExpression):
    """A command expression which will return a string value.

    If the given value returns a list of values, evaluate will return a copy of the list with each element having been
    run through the specified command. (eg `dirname(["/a/b", "c/d"])` will return ["a", "c"])
    """

    def __init__(self, command: Token, arguments: list[ValueExpression]):
        if command.body in {"dirname", "basename", "abspath", "env"} and len(arguments) != 1:
            raise WrongArgumentNum(1, len(arguments))
        elif command.body == "join" and len(arguments) != 2:
            raise WrongArgumentNum(2, len(arguments))

        super().__init__(command, arguments)

    @staticmethod
    def __wrapper(f: typing.Callable[[str], str], arg: typing.Union[str, list[str]]) -> typing.Union[str, list[str]]:
        return [f(i) for i in arg] if isinstance(arg, list) else f(arg)

    def __run(self, args: list[str]) -> str:
        if self.command.body == "dirname":
            return self.__wrapper(os.path.dirname, args[0])
        elif self.command.body == "basename":
            return self.__wrapper(os.path.basename, args[0])
        elif self.command.body == "abspath":
            return self.__wrapper(os.path.abspath, args[0])
        elif self.command.body == "env":
            return self.__wrapper(os.getenv, args[0])
        elif self.command.body == "join":
            return args[1].join(args[0])

        raise UnknownCommandException(self.command)

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> typing.Union[str, list[str]]:
        args = [arg.no_expand_evaluate(env) if isinstance(arg, AccessorExpression) and arg.list_expand
                else arg.evaluate(env)
                for arg in self.arguments]

        if len(args) == 1:
            result = self.__run(args)

            if isinstance(args[0], list):
                raw_arg = self.arguments[0]

                if isinstance(raw_arg, AccessorExpression) and raw_arg.list_expand:
                    return raw_arg.delim.join(result)

            return result
        elif len(args) == 2:
            return self.__run(args)


class ConditionalCommandExpression(CommandExpression, ConditionalExpression):
    """A command expression which will return a boolean value.

    If the given value returns a lit of values, evaluate will return the value as if the result of the command being
    applied to each element were compared with AND.
    """

    def __init__(self, negate: bool, command: Token, arguments: list[ValueExpression]):
        if len(arguments) != 1:
            raise WrongArgumentNum(1, len(arguments))

        super(ConditionalCommandExpression, self).__init__(command, arguments)
        super(CommandExpression, self).__init__(negate, None, None)

    def __eq__(self, other) -> bool:
        return (isinstance(other, ConditionalCommandExpression)
                and self.negate == other.negate
                and self.command == other.command
                and self.arguments == other.arguments

                and self.operator == other.operator
                and self.right == other.right)

    @staticmethod
    def __wrapper(f: typing.Callable[[str], bool], arg: typing.Union[str, list[str]]) -> bool:
        return all(f(i) for i in arg) if isinstance(arg, list) else f(arg)

    def __run(self, arg: str):
        if self.command.body == "exists":
            result = self.__wrapper(os.path.exists, arg)
        elif self.command.body == "isfile":
            result = self.__wrapper(os.path.isfile, arg)
        elif self.command.body == "isdir":
            result = self.__wrapper(os.path.isdir, arg)
        else:
            raise UnknownCommandException(self.command)

        return result if not self.negate else not result

    def evaluate(self, env: dict[str, typing.Union[str, list[str]]]) -> bool:
        args = [arg.no_expand_evaluate(env) if isinstance(arg, AccessorExpression) and arg.list_expand
                else arg.evaluate(env)
                for arg in self.arguments]
        
        return all(self.__run(i) for i in args)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Parsing methods                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def __parse_tokens(tokens: list[Token]) -> UndoExpression:
    """Parse an UndoExpression from a list of tokens."""
    try:
        expr, _ = __parse_value_expression_tokens(tokens)
    except IndexError:
        raise UnexpectedEndOfLineError()

    return expr


def __parse_value_expression_tokens(tokens: list[Token]) -> (ValueExpression, int):
    # todo: could be optimized by checking first token type and calling the appropriate parser method
    try:
        return __parse_value_command_expression_tokens(tokens)
    except (ParseError, IndexError):
        pass

    try:
        return __parse_string_literal_expression_tokens(tokens)
    except (ParseError, IndexError):
        pass

    try:
        return __parse_string_expansion_expression_tokens(tokens)
    except (ParseError, IndexError):
        pass

    try:
        return __parse_ternary_expression_tokens(tokens)
    except (ParseError, IndexError):
        pass

    try:
        return __parse_accessor_expression_tokens(tokens)
    except (ParseError, IndexError):
        pass

    raise ParseError("expected a value expression but found none")


def __parse_conditional_expression_tokens(tokens: list[Token]) -> (ConditionalExpression, int):
    """Parse a ConditionalExpression from a list of tokens."""
    negate = False
    offset = 0

    try:
        conditional, token_count = __parse_existence_expression_tokens(tokens)
    except (ParseError, IndexError):
        try:
            conditional, token_count = __parse_conditional_command_expression_tokens(tokens)
        except (ParseError, IndexError):
            raise ParseError("expected a conditional expression but found none")

    conditional.negate = negate

    offset += token_count

    # handle chained conditional operators
    if len(tokens) > offset and tokens[offset].kind in {TokenKind.AND, TokenKind.OR}:
        right, token_count = __parse_conditional_expression_tokens(tokens[offset + 1:])

        conditional.right = right
        conditional.operator = tokens[offset]

        offset += token_count + 1

    return conditional, offset


def __parse_accessor_expression_tokens(tokens: list[Token]) -> (AccessorExpression, int):
    """Parse a ValueExpression from a list of tokens (should consist of a single identifier)."""
    if tokens[0].kind != TokenKind.ACCESSOR:
        raise UnexpectedTokenError(TokenKind.ACCESSOR, tokens[0].kind)

    if tokens[1].kind != TokenKind.IDENT:
        raise UnexpectedTokenError(TokenKind.IDENT, tokens[1].kind)

    if len(tokens) >= 3 and tokens[2].kind == TokenKind.ELLIPSE:
        # todo: allow specifying a custom delimiter
        return AccessorExpression(tokens[1], True, " "), 3

    return AccessorExpression(tokens[1], False), 2


def __parse_ternary_expression_tokens(tokens: list[Token]) -> (TernaryExpression, int):
    """Parse a TernaryExpression from a list of tokens.

    Grammar:
        EXISTENCE_EXPR ? VALUE_EXPR [ ':'? VALUE_EXPR ]
    """
    condition, offset = __parse_conditional_expression_tokens(tokens)

    if tokens[offset].kind != TokenKind.TERNARY_IF:
        raise UnexpectedTokenError(TokenKind.TERNARY_IF, tokens[offset].kind)
    offset += 1

    if_value, token_count = __parse_value_expression_tokens(tokens[offset:])
    offset += token_count

    else_value = None

    if len(tokens) > offset and tokens[offset].kind == TokenKind.TERNARY_ELSE:
        offset += 1
        else_value, token_count = __parse_value_expression_tokens(tokens[offset:])
        offset += token_count

    return TernaryExpression(condition, if_value, else_value), offset


def __parse_string_literal_expression_tokens(tokens: list[Token]) -> (StringLiteralExpression, int):
    """Parse a StringLiteralExpression from a list of tokens."""
    if tokens[0].kind != TokenKind.STRING_LITERAL:
        raise UnexpectedTokenError(TokenKind.STRING_LITERAL, tokens[0].kind)

    return StringLiteralExpression(tokens[0]), 1


def __parse_string_expansion_expression_tokens(tokens: list[Token]) -> (StringExpansionExpression, int):
    """Parse a StringExpansionExpression from a list of tokens."""
    if tokens[0].kind != TokenKind.STRING_EXPANSION:
        raise UnexpectedTokenError(TokenKind.STRING_EXPANSION, tokens[0].kind)

    return StringExpansionExpression(tokens[0]), 1


def __parse_existence_expression_tokens(tokens: list[Token]) -> (ExistenceExpression, int):
    """Parse an ExistenceExpression from a list of tokens.

    Grammar:
        EXISTENCE_EXPR = '!' ? IDENT
    """
    negate = False
    offset = 0

    if tokens[0].kind == TokenKind.NOT:
        negate = True
        offset += 1

    if tokens[offset].kind != TokenKind.IDENT:
        raise UnexpectedTokenError(TokenKind.IDENT, tokens[offset].kind)

    ident = tokens[offset]

    offset += 1

    return ExistenceExpression(negate, ident), offset


def __parse_command_tokens(tokens: list[Token]) -> (Token, list[ValueExpression], int):
    """Parse the command and argument from a list of tokens"""
    if tokens[0].kind != TokenKind.COMMAND:
        raise UnexpectedTokenError(TokenKind.COMMAND, tokens[0].kind)
    command = tokens[0]

    if tokens[1].kind != TokenKind.OPEN_PARENTHESE:
        raise UnexpectedTokenError(TokenKind.OPEN_PARENTHESE, tokens[1].kind)

    offset = 2
    arguments = list()

    while True:
        try:
            argument, token_count = __parse_value_expression_tokens(tokens[offset:])
        except ParseError:
            break

        arguments.append(argument)
        offset += token_count

        if tokens[offset].kind == TokenKind.COMMA:
            offset += 1
        else:
            break

    if tokens[offset].kind != TokenKind.CLOSE_PARENTHESE:
        raise UnexpectedTokenError(TokenKind.CLOSE_PARENTHESE, tokens[offset].kind)

    return command, arguments, offset + 1


def __parse_value_command_expression_tokens(tokens: list[Token]) -> (ValueCommandExpression, int):
    command, arguments, offset = __parse_command_tokens(tokens)

    if command.body not in {"dirname", "basename", "abspath", "env", "join"}:
        raise ParseError("expected ValueCommand but found none")

    return ValueCommandExpression(command, arguments), offset


def __parse_conditional_command_expression_tokens(tokens: list[Token]) -> (ConditionalCommandExpression, int):
    negate = False
    offset = 0

    if tokens[0].kind == TokenKind.NOT:
        negate = True
        offset += 1

    command, arguments, token_count = __parse_command_tokens(tokens[offset:])

    if command.body not in {"exists", "isfile", "isdir"}:
        raise ParseError("expected ConditionalCommand but found none")

    offset += token_count

    return ConditionalCommandExpression(negate, command, arguments), offset


def parse(content: str) -> UndoExpression:
    """Parse an UndoExpression from a string."""
    return __parse_tokens(__tokenize(content))
