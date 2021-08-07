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


# todo: add ellipse (ie '...') for group command  calls
class TokenKind(enum.Enum):
    IDENT = enum.auto()

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

    # Unknown iss only used to allow for passing a token to TokenError.
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
__COMMAND_REGEX = r"dirname|basename|abspath|env|exists|isfile|isdir"
__STRING_LITERAL_REGEX = r"'.*'"
__STRING_EXPANSION_REGEX = r"\".*\""
__SYMBOL_REGEX = r"\$|\?|:|&&|\|\||!"
__TOKEN_REGEX = re.compile(rf"\s*({__STRING_EXPANSION_REGEX}|{__STRING_LITERAL_REGEX}|{__COMMAND_REGEX}|{__IDENT_REGEX}|{__SYMBOL_REGEX})")


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

    def evaluate(self, env: dict[str, str]) -> str:
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

    def __str__(self):
        return f""

    def evaluate(self, env: dict[str, str]) -> bool:
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

    def __init__(self, identifier: Token):
        self.identifier = identifier

    def __eq__(self, other) -> bool:
        return(isinstance(other, AccessorExpression)
               and self.identifier == other.identifier)

    def evaluate(self, env: dict[str, str]) -> str:
        """Retrieve the value corresponding to this expression's identifier or "" if it does not exist in env."""
        return env.setdefault(self.identifier.body, "")


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

    def evaluate(self, env: dict[str, str]) -> str:
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

    def evaluate(self, env: dict[str, str]) -> str:
        return self.token.body


class StringExpansionExpression(ValueExpression):
    def __init__(self, token: Token):
        self.token = token

    def __eq__(self, other) -> bool:
        return (isinstance(other, StringExpansionExpression)
                and self.token == other.token)

    def evaluate(self, env: dict[str, str]) -> str:
        idents = set(re.findall(r"\$[a-zA-Z0-9][a-zA-Z0-9_]*", self.token.body))
        expanded = self.token.body

        for ident in idents:
            expanded = expanded.replace(ident, env.setdefault(ident[1:], ""))

        return expanded


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

    def evaluate(self, env: dict[str, str]) -> bool:
        if self.negate:
            return env.setdefault(self.identifier.body, "") == ""
        else:
            return env.setdefault(self.identifier.body, "") != ""


# command-expressions


class CommandExpression(abc.ABC):
    """An expression which will generate values based on inputs."""

    def __init__(self, command: Token, argument: ValueExpression):
        self.command = command
        self.argument = argument

    def __eq__(self, other) -> bool:
        return (isinstance(other, CommandExpression)
                and self.command == other.command
                and self.argument == other.argument)


class ValueCommandExpression(CommandExpression, ValueExpression):
    """A command expression which will return a string value."""

    def evaluate(self, env: dict[str, str]) -> str:
        arg = self.argument.evaluate(env)

        if self.command.body == "dirname":
            return os.path.dirname(arg)
        elif self.command.body == "basename":
            return os.path.basename(arg)
        elif self.command.body == "abspath":
            return os.path.abspath(arg)
        elif self.command.body == "env":
            return os.getenv(arg)

        raise UnknownCommandException(self.command)


class ConditionalCommandExpression(CommandExpression, ConditionalExpression):
    """A command expression which will return a boolean value."""

    def __init__(self, negate: bool, command: Token, argument: ValueExpression):
        super(ConditionalCommandExpression, self).__init__(command, argument)
        super(CommandExpression, self).__init__(negate, None, None)

    def __eq__(self, other) -> bool:
        return (isinstance(other, ConditionalCommandExpression)
                and self.negate == other.negate
                and self.command == other.command
                and self.argument == other.argument

                and self.operator == other.operator
                and self.right == other.right)

    def evaluate(self, env: dict[str, str]) -> bool:
        arg = self.argument.evaluate(env)

        if self.command.body == "exists":
            result = os.path.exists(arg)
        elif self.command.body == "isfile":
            result = os.path.isfile(arg)
        elif self.command.body == "isdir":
            result = os.path.isdir(arg)
        else:
            raise UnknownCommandException(self.command)

        return result if not self.negate else not result


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
    except (ParseError, IndexError) as err:
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
    except (ParseError, IndexError) as err:
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
    except (ParseError, IndexError) as err:
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

    return AccessorExpression(tokens[1]), 2


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


def __parse_command_tokens(tokens: list[Token]) -> (Token, ValueExpression, int):
    """Parse the command and argument from a list of tokens"""
    if tokens[0].kind != TokenKind.COMMAND:
        raise UnexpectedTokenError(TokenKind.COMMAND, tokens[0].kind)
    command = tokens[0]

    if tokens[1].kind != TokenKind.OPEN_PARENTHESE:
        raise UnexpectedTokenError(TokenKind.OPEN_PARENTHESE, tokens[1].kind)

    argument, token_count = __parse_value_expression_tokens(tokens[2:])

    offset = token_count + 2

    if tokens[offset].kind != TokenKind.CLOSE_PARENTHESE:
        raise UnexpectedTokenError(TokenKind.CLOSE_PARENTHESE, tokens[offset].kind)

    return command, argument, offset + 1


def __parse_value_command_expression_tokens(tokens: list[Token]) -> (ValueCommandExpression, int):
    command, argument, token_count = __parse_command_tokens(tokens)

    return ValueCommandExpression(command, argument), token_count


def __parse_conditional_command_expression_tokens(tokens: list[Token]) -> (ConditionalCommandExpression, int):
    negate = False
    offset = 0

    if tokens[0].kind == TokenKind.NOT:
        negate = True
        offset += 1

    command, argument, token_count = __parse_command_tokens(tokens[offset:])
    offset += token_count

    return ConditionalCommandExpression(negate, command, argument), offset


def parse(content: str) -> UndoExpression:
    """Parse an UndoExpression from a string."""
    return __parse_tokens(__tokenize(content))
