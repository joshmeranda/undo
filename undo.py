#!/usr/bin/env python
import re

import expression


def expand(undo: str, env: dict[str, str]) -> str:
    """Expand a string containing 0 or more UndoExpressions in them using the given environment.

    :param undo: the undo pattern to expand.
    :param env: the dictionary containing the  values to use for evaluating undo expressions.
    :raise ValueError: for any error with bad syntax or format.
    """
    if undo.count("%") % 2 != 0:
        raise ValueError(f"unbalanced '%' in : {undo}")

    splits = [i.strip() for i in re.findall("%[^%]*%|[^%]+", undo) if not i.isspace()]

    expanded = list()

    for i in splits:
        if i[0] == i[-1] == "%":
            expr = expression.parse(i.strip("%").strip())

            if isinstance(expr, expression.ValueExpression):
                expanded.append(expr.evaluate(env))
            else:
                raise ValueError(f"expected a string value but found a boolean: '{i}'")
        else:
            expanded.append(i)

    return ' '.join(expanded)


def main():
    undo = expand("""rm % VERBOSE ? '--verbose' % % DIR ? \"$DIR/example\" : '~/example' %""", {
        "VERBOSE": str(True)
    })

    print(undo)


if __name__ == "__main__":
    main()
