import abc
import dataclasses
import enum
import os
import os.path
import re
import typing


class BooleanOperator(enum.Enum):
    AND = enum.auto()
    OR = enum.auto()
    NOT = enum.auto()


class TokenKind(enum.Enum):
    IDENT = enum.auto()
    TICK = enum.auto()

    AND = enum.auto()
    OR = enum.auto()
    NOT = enum.auto()

    TERNAY_IF = enum.auto()
    TERNAY_ELSE = enum.auto()

    UNKNOWN = enum.auto()


@dataclasses.dataclass
class Token:
    """Represents a single token in an expression."""
    kind: TokenKind
    body: str
    col: int


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
        super().__init__(f"{message} at col {token.col}: '{token.body}")


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


class UnknownCommandException(EvaluationError):
    def __init__(self, command: Token):
        super().__init__(f"no such command '{command.body}'")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Expression classes                                                          #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class UndoExpression(abc.ABC):
    """Represents an expression resulting in a string command."""


class ValueExpression(abc.ABC, UndoExpression):
    """An expression that will produce a single string value"""

    def evaluate(self, env: dict[str, str]) -> str:
        """Evaluate the result of the expression given the map of identifiers and values."""


class ConditionalExpression(UndoExpression):
    """An expression representing a chain of BooleanExpressions and operators."""

    def __init__(
            self, negate: bool, left: 'ConditionalExpression', operator: typing.Optional[TokenKind],
            right: typing.Optional['ConditionalExpression']):
        self.negate = negate
        self.left = left
        self.operator = operator
        self.right = right

    def evaluate(self, env: dict[str, str]) -> bool:
        """Evaluate the result of the expression given the map of identifier and values."""


class CommandExpression(abc.ABC):
    """An expression which will generate values based on inputs."""

    def __init__(self, command: Token, argument: Token):
        self.command = command
        self.argument = argument


class IdentifierExpression(ValueExpression):
    """A simple expression which will resolve to a value given an identifier."""

    def __init__(self, identifier: Token):
        self.identifier = identifier

    def evaluate(self, env: dict[str, str]) -> str:
        try:
            return env[self.identifier.body]
        except KeyError:
            raise EvaluationError(f"Unknown identifier '{self.identifier.body}' found at col {self.identifier.col}")


class ValueCommandExpression(CommandExpression, ValueExpression):
    """A command expression which will return a string value."""

    def evaluate(self, _env: dict[str, str]) -> str:
        if self.command == "dirname":
            return os.path.dirname(self.argument.body)
        elif self.command == "basename":
            return os.path.basename(self.argument.body)
        elif self.command == "abspath":
            return os.path.abspath(self.argument.body)
        elif self.command == "env":
            return os.getenv(self.argument.body)

        raise UnknownCommandException(self.command)


class TernaryExpression(ValueExpression):
    """An expression allowing for basic conditional expressions."""

    def __init__(self, condition: ConditionalExpression, if_value: ValueExpression, else_value: ValueExpression):
        self.condition = condition
        self.if_value = if_value
        self.else_value = else_value

    def evaluate(self, env: dict[str, str]) -> str:
        if self.condition.evaluate(env):
            return self.if_value.evaluate(env)
        else:
            return self.else_value.evaluate(env)


class ExistenceExpression(ConditionalExpression):
    """An expression which evaluates if a value for the given identifier has been set."""

    def __init__(self, negate: bool, identifier: IdentifierExpression):
        super().__init__(negate, self, None, None)
        self.identifier = identifier

    def evaluate(self, env: dict[str, str]) -> bool:
        return env.get(self.identifier.identifier.body) is not None


class ConditionalCommandExpression(CommandExpression, ConditionalExpression):
    """A command expression which will return a boolean value."""

    def __init__(self, negate: bool, command: Token, argument: Token):
        super(CommandExpression, self).__init__(command, argument)
        super(ConditionalExpression, self).__init__(negate, self, None, None)

    def evaluate(self, _env: dict[str, str]) -> bool:
        if self.command == "exists":
            return os.path.exists(self.argument.body)
        elif self.command == "file":
            return os.path.isfile(self.argument.body)
        elif self.command == "dir":
            return os.path.isdir(self.argument.body)

        raise UnknownCommandException(self.command)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Parsing methods                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def __parse_tokens(tokens: list[Token]) -> UndoExpression:
    """Parse an UndoExpression from a list of tokens."""
    try:
        (expr, _) = __parse_value_expression_tokens(tokens)
    except IndexError:
        raise UnexpectedEndOfLineError()

    return expr


def __parse_value_expression_tokens(tokens: list[Token]) -> (ValueExpression, int):
    try:
        return __parse_identifier_expression_tokens(tokens)
    except ParseError:
        pass

    try:
        return __parse_value_command_expression_tokens(tokens)
    except  ParseError:
        pass

    try:
        return __parse_ternary_expression_tokens(tokens)
    except ParseError:
        pass

    raise ParseError("expected a value expression but found none")


def __parse_conditional_expression_tokens(tokens: list[Token]) -> (ConditionalExpression, int):
    """Parse a ConditionalExpression from a list of tokens."""
    negate = False
    token = tokens[0]
    offset = 0

    if token.kind == TokenKind.NOT:
        negate = True
        offset += 1

    try:
        (left, token_count) = __parse_existence_expression_tokens(tokens)
    except ParseError:
        try:
            (left, token_count) = __parse_conditional_command_expression_tokens(tokens)
        except ParseError:
            raise ParseError("expected a binary expression but found none")

    offset += token_count

    if len(tokens) > offset and tokens[offset].kind in {TokenKind.AND, TokenKind.OR}:
        operator = tokens[offset].kind
        right = __parse_conditional_expression_tokens(tokens[offset + 1:])
    else:
        operator = None
        right = None

    return ConditionalExpression(negate, left, operator, right)


def __parse_identifier_expression_tokens(tokens: list[Token]) -> (IdentifierExpression, int):
    """Parse a ValueExpression from a list of tokens (should consist of a single identifier)."""
    token = tokens[0]

    if token.kind != TokenKind.IDENT:
        raise UnexpectedTokenError(TokenKind.IDENT, token.kind)

    return IdentifierExpression(token), 1


def __parse_ternary_expression_tokens(tokens: list[Token]) -> (TernaryExpression, int):
    """Parse a TernayrExpression from a list of tokens.

    Grammar:
        EXISTENCE_EXPR ? VALUE_EXPR [ ':'? VALUE_EXPR ]
    """
    (condition, offset) = __parse_conditional_expression_tokens(tokens)

    token = tokens[offset]

    if token.kind != TokenKind.TERNAY_IF:
        raise UnexpectedTokenError(TokenKind.TERNAY_IF, token.kind)
    offset += 1

    (if_value, token_count) = __parse_value_expression_tokens(tokens[offset:])
    offset += token_count

    token = tokens[offset]

    else_value = None

    if token.kind == TokenKind.TERNAY_ELSE:
        offset += 1
        (else_value, token_count) = __parse_value_expression_tokens(tokens[offset:])

    return TernaryExpression(condition, if_value, else_value), offset


def __parse_value_command_expression_tokens(tokens: list[Token]) -> (ValueCommandExpression, int):
    if tokens[0].kind != TokenKind.TICK:
        raise UnexpectedTokenError(TokenKind.TICK, tokens[0].kind)

    if tokens[1].kind != TokenKind.TICK:
        raise UnexpectedTokenError(TokenKind.IDENT, tokens[1].kind)
    command = tokens[1]

    if tokens[2].kind != TokenKind.TICK:
        raise UnexpectedTokenError(TokenKind.IDENT, tokens[2].kind)
    argument = tokens[2]

    if tokens[3].kind != TokenKind.TICK:
        raise UnexpectedTokenError(TokenKind.TICK, tokens[3].kind)

    return ValueCommandExpression(command, argument), 4


def __parse_conditional_command_expression_tokens(tokens: list[Token]) -> (ConditionalCommandExpression, int):
    negate = tokens[0].kind == TokenKind.NOT

    if tokens[1].kind != TokenKind.TICK:
        raise UnexpectedTokenError(TokenKind.TICK, tokens[1].kind)

    if tokens[2].kind != TokenKind.TICK:
        raise UnexpectedTokenError(TokenKind.IDENT, tokens[2].kind)
    command = tokens[2]

    if tokens[3].kind != TokenKind.TICK:
        raise UnexpectedTokenError(TokenKind.IDENT, tokens[3].kind)
    argument = tokens[3]

    if tokens[4].kind != TokenKind.TICK:
        raise UnexpectedTokenError(TokenKind.TICK, tokens[4].kind)

    return ConditionalCommandExpression(negate, command, argument), 4


def __parse_existence_expression_tokens(tokens: list[Token]) -> (ExistenceExpression, int):
    """Parse an ExistenceExpression from a list of tokens.

    Grammar:
        EXISTENCE_EXPR = '!' ? VALUE_EXPR [ ['||' | '&&'] EXISTENCE_EXPR ]*
    """
    token = tokens[0]
    negate = False

    if token.kind == TokenKind.NOT:
        negate = True

    (left, offset) = __parse_identifier_expression_tokens(tokens[1:])

    offset += 1

    operator = None
    right = None

    token = tokens[offset]

    if token.kind in {TokenKind.AND, TokenKind.OR}:
        offset += 1

        operator = token

        (right, token_count) = __parse_existence_expression_tokens(tokens[offset:])
        offset += token_count

    return ExistenceExpression(negate, left), offset


__IDENT_REGEX = r"[a-zA-Z0-9]([a-zA-Z0-9_])*"
__TOKEN_REGEX = re.compile(rf" *({__IDENT_REGEX}|\?|:|&&|\|\||!|`)")


def __tokenize(content) -> list[Token]:
    """Split a string individual tokens."""
    offset = 0
    tokens = []

    while offset < len(content):
        m = __TOKEN_REGEX.match(content[offset:])

        if m is None:
            # todo: custom error type?
            body = content[offset:].lstrip().split()[0]
            col = offset
            token = Token(TokenKind.UNKNOWN, body, col)

            raise TokenError(token, "Unknown token")

        raw_body = m.string[:m.end()]
        body = raw_body.strip()

        col = offset + 1 + m.end() - len(body)

        if body == "`":
            kind = TokenKind.TICK
        elif body == "?":
            kind = TokenKind.TERNAY_IF
        elif body == ":":
            kind = TokenKind.TERNAY_ELSE
        elif body == "&&":
            kind = TokenKind.AND
        elif body == "||":
            kind = TokenKind.OR
        elif body == "!":
            kind = TokenKind.NOT
        else:
            kind = TokenKind.IDENT

        token = Token(kind, body, col)
        tokens.append(token)

        offset += m.end()

    return tokens


def parse(content: str) -> UndoExpression:
    """Parse an UndoExpression from a string."""
    return __parse_tokens(__tokenize(content))
