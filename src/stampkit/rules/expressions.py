"""Sandboxed expression evaluation for declarative rules.

Supports arithmetic over a small variable set ({t, R, material_*}); no
builtins, no attribute access, no calls except a whitelisted function set.
"""

from __future__ import annotations

import ast
import math
from collections.abc import Mapping
from typing import Any

_ALLOWED_FUNCS: dict[str, Any] = {
    "abs": abs,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
}

_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
)


class ExpressionError(ValueError):
    pass


def evaluate_expr(expr: str, variables: Mapping[str, float]) -> float:
    """Evaluate a numeric expression in a restricted sandbox."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ExpressionError(f"bad expression {expr!r}: {e}") from e
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ExpressionError(
                f"disallowed syntax in {expr!r}: {type(node).__name__}"
            )
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS
        ):
            raise ExpressionError(f"disallowed call in {expr!r}")
        if isinstance(node, ast.Name) and node.id not in variables and node.id not in _ALLOWED_FUNCS:
            raise ExpressionError(f"unknown name {node.id!r} in {expr!r}")
    env: dict[str, Any] = {**_ALLOWED_FUNCS, **variables}
    result = eval(compile(tree, "<rule-expr>", "eval"), {"__builtins__": {}}, env)  # noqa: S307
    return float(result)
