"""Result comparison for the eval. No database needed, so it is unit-tested.

strict:   same number of columns and the same values (column names ignored, floats rounded to 2 dp,
          row order ignored unless the question is a ranking).
lenient:  like strict, but the generated query may return EXTRA columns. Every reference column must
          appear with the same values, and the rows must line up (so a wrong name/number pairing fails).
          Example: reference returns the site name; generated returns the name and the hours. That is
          a correct answer with more detail, so lenient passes it and strict does not.
"""
from decimal import Decimal
from itertools import product


def norm_value(v):
    if isinstance(v, (Decimal, float)):
        return round(float(v), 2)
    if isinstance(v, int):
        return float(v)
    return str(v)


def norm_rows(rows, ordered):
    out = [tuple(norm_value(v) for v in r) for r in rows]
    return out if ordered else sorted(out, key=repr)


def strict_match(got, expected, ordered=False):
    return norm_rows(got, ordered) == norm_rows(expected, ordered)


def lenient_match(got, expected, ordered=False):
    got_n = [tuple(norm_value(v) for v in r) for r in got]
    exp_n = [tuple(norm_value(v) for v in r) for r in expected]
    if len(got_n) != len(exp_n):
        return False
    if not exp_n:
        return True
    width_e, width_g = len(exp_n[0]), len(got_n[0]) if got_n else 0
    if width_g < width_e:
        return False

    def key(col):
        return col if ordered else sorted(col, key=repr)

    exp_cols = [[r[i] for r in exp_n] for i in range(width_e)]
    got_cols = [[r[j] for r in got_n] for j in range(width_g)]
    candidates = [[j for j in range(width_g) if key(got_cols[j]) == key(ec)] for ec in exp_cols]
    if any(not c for c in candidates):
        return False
    target = exp_n if ordered else sorted(exp_n, key=repr)
    for choice in product(*candidates):
        if len(set(choice)) != len(choice):
            continue
        projected = [tuple(r[j] for j in choice) for r in got_n]
        if (projected if ordered else sorted(projected, key=repr)) == target:
            return True
    return False
