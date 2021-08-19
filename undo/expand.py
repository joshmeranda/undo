import logging
import re
import typing

from undo import expression


def __join_expanded(expanded: list[typing.Union[str, list[str]]], sep: str) -> str:
    """Join the expanded items into a single or multiple commands.

    :param expanded: the expanded items to join.
    :param sep: the separator to use when expanding a list value across multiple commands.
    :return: The string value
    """

    list_values = [val for val in expanded if isinstance(val, list)]

    if len(list_values) > 1:
        raise ValueError("there can be only one non-expanded list")

    if len(list_values) == 0:
        return "".join(expanded)

    expansion_list = list_values[0]
    index = expanded.index(expansion_list)

    prefix = expanded[:index]
    postfix = expanded[index + 1:]

    return sep.join([
        "".join(prefix + [i] + postfix) for i in expansion_list
    ])


def expand(undo: str, env: dict[str, typing.Union[str, list[str]]]) -> str:
    """Expand a string containing 0 or more UndoExpressions in them using the given environment.

    todo: handle too many multi-command expansions

    :param undo: the undo pattern to expand.
    :param env: the dictionary containing the  values to use for evaluating undo expressions.
    :raise ValueError: for any error with bad syntax or format.
    """
    if undo.count("%") % 2 != 0:
        raise ValueError(f"unbalanced '%' in : {undo}")

    splits = [i
              for i in re.findall(r"\s+|"       # spaces
                                  r"%[^%^]*%|"  # expressions
                                  r"[^%^\s]+", undo)]

    expanded = list()

    for i in splits:
        if len(i) > 2 and i[0] == i[-1] == "%":
            try:
                expr = expression.parse(i.strip("%").strip())
            except expression.ExpressionError as err:
                logging.error(err)
                continue

            if isinstance(expr, expression.ValueExpression):
                expanded.append(expr.evaluate(env))
            else:
                logging.error(f"expected a string value but found a boolean: '{i}'")
        else:
            expanded.append(i)

    command = __join_expanded(expanded, "; ")

    return command
