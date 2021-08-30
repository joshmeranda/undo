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
    list_values = [(i, val) for i, val in enumerate(expanded) if isinstance(val, list)]

    if len(list_values) == 0:
        return "".join(expanded)

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

    return sep.join(result)


def expand(undo: str, env: dict[str, typing.Union[str, list[str]]], bounds: tuple[str, str] = ("%", "%")) -> str:
    """Expand a string containing 0 or more UndoExpressions in them using the given environment.

    todo: handle too many multi-command expansions

    :param undo: the undo pattern to expand.
    :param env: the dictionary containing the  values to use for evaluating undo expressions.
    :param bounds: the bounds around an expressions.
    :raise ValueError: for any error with bad syntax or format.
    """
    if undo.count("%") % 2 != 0:
        raise ValueError(f"unbalanced '%' in : {undo}")

    expr_regex = rf"{re.escape(bounds[0])}.*?{re.escape(bounds[1])}"

    splits = [i
              for i in re.findall(r"(\s+|"               # spaces
                                  rf"{expr_regex}|"     # expressions
                                  r"[^\s]+)", undo)]

    expanded = list()

    for i in splits:

        # todo: ideally we would not re-run the same regex pattern here
        if re.fullmatch(expr_regex, i):
            try:
                expr = expression.parse(i.removeprefix(bounds[0]).removesuffix(bounds[1]).strip())
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
