import dataclasses
import enum
import re


class TokenKind(enum.Enum):
    IDENT = enum.auto()
    TICK = enum.auto()

    AND = enum.auto()
    OR = enum.auto()
    NOT = enum.auto()

    TERNAY_IF = enum.auto()
    TERNAY_ELSE = enum.auto()


@dataclasses.dataclass
class Token:
    """Represents a single token in an expression."""
    kind: TokenKind
    body: str
    col: int


class UndoExpression:
    """Represents an expression resulting in a string command."""

    def result(self, env: dict[str, str]) -> str:
        """Retrieve the result of the expression given the map of identifiers and values."""


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
            raise ValueError(f"Unknown token at col {offset + 1}")

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


def __parse_tokens(tokens: list[Token]) -> UndoExpression:
    """Parse an UndoExpression from a list of tokens."""


def parse(content: str) -> UndoExpression:
    """Parse an UndoExpression from a string."""
    return __parse_tokens(__tokenize(content))
