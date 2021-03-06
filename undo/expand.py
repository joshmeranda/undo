import logging
import re
import typing

from undo import expression


def __join_expanded(expanded: list[typing.Union[str, list[str]]]) -> list[str]:
    """Join the expanded items into a single or multiple commands.

    :param expanded: the expanded items to join.
    :return: The string value
    """
    list_values = [(i, val) for i, val in enumerate(expanded) if isinstance(val, list)]

    if len(list_values) == 0:
        return ["".join(expanded)]

    initial_len = len(list_values[0][1]) if list_values else None

    if not all(len(i) == initial_len for _, i in list_values[1::]):
        raise ValueError("not all non-expanded list are of the same size")

    pairs = zip(*[[(i, j) for j in val] for i, val in list_values])

    result = list()
    for pair in pairs:
        cc = expanded.copy()

        for i, v in pair:
            del(cc[i])
            cc.insert(i, v)

        result.append("".join(cc))

    return result


def __find_matching_closing_bound(content: str, head: int, open_bound: str, close_bound: str) -> int:
    depth = 0

    while head < len(content):
        if content[head::].startswith(open_bound) and not (open_bound == close_bound and depth != 0):
            depth += 1
            head += len(open_bound)
        elif content[head::].startswith(close_bound) and content[head - 1] != "\\":
            depth -= 1
            head += len(close_bound)

            if depth == 0:
                return head
        else:
            head += 1

    return head


def __separate(content: str, bounds: tuple[str, str]) -> list[str]:
    open_bound = bounds[0]
    close_bound = bounds[1]

    result = list()

    last = 0
    head = 0

    while head < len(content):

        if content[head::].startswith(open_bound) and content[head - 1] != "\\":
            if head != last:
                result.append(content[last:head:])
                last = head

            head = __find_matching_closing_bound(content, head, open_bound, close_bound)

            result.append(content[last:head:])
            last = head
        else:
            head += 1

    if head != last:
        result.append(content[last:head:])

    return result


def expand(undo: str, env: dict[str, typing.Union[str, list[str]]], bounds: tuple[str, str],
           command_sep: typing.Optional[str]) -> typing.Union[str, list[str]]:
    """Expand a string containing 0 or more UndoExpressions in them using the given environment.

    :param undo: the undo pattern to expand.
    :param env: the dictionary containing the  values to use for evaluating undo expressions.
    :param bounds: the bounds around an expressions.
    :param command_sep: the join delimiter to use if expansion results in a string.
    :return: if command_sep is not None or only one command is expanded, then a string of the one or more expanded
        commands join on command-sep. Otherwise the list of expanded commands.
    :raise ValueError: for any error with bad syntax or format.
    """
    if undo.count("%") % 2 != 0:
        raise ValueError(f"unbalanced '%' in : {undo}")

    expr_regex = rf"{re.escape(bounds[0])}.*?{re.escape(bounds[1])}"

    splits = __separate(undo, bounds)

    expanded = list()

    for i in splits:
        if re.fullmatch(expr_regex, i):
            expr = expression.parse(i.removeprefix(bounds[0]).removesuffix(bounds[1]).strip())

            if isinstance(expr, expression.ValueExpression):
                expanded.append(expr.evaluate(env))
            else:
                logging.error(f"expected a string value but found a boolean: '{i}'")
        else:
            expanded.append(i)

    command = __join_expanded(expanded)

    if len(command) == 1:
        return command[0]

    if command_sep is not None:
        return command_sep.join(command)

    return command
