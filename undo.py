#!/usr/bin/env python
import logging
import re

import expression
import history


def expand(undo: str, env: dict[str, str]) -> str:
    """Expand a string containing 0 or more UndoExpressions in them using the given environment.

    :param undo: the undo pattern to expand.
    :param env: the dictionary containing the  values to use for evaluating undo expressions.
    :raise ValueError: for any error with bad syntax or format.
    """
    if undo.count("%") % 2 != 0:
        raise ValueError(f"unbalanced '%' in : {undo}")

    splits = [i
              for i in re.findall(r"\s+|%[^%^]*%|[^%^\s]+", undo)]

    expanded = list()

    for i in splits:
        if len(i) > 2 and i[0] == i[-1] == "%":
            # todo: test this warning
            try:
                expr = expression.parse(i.strip("%").strip())
            except expression.ExpressionError as err:
                logging.warning(err)
                continue

            if isinstance(expr, expression.ValueExpression):
                expanded.append(expr.evaluate(env))
            else:
                logging.warning(f"expected a string value but found a boolean: '{i}'")
        else:
            expanded.append(i)

    return ''.join(expanded)


def main():
    pass


if __name__ == "__main__":
    main()
