"""Useful functions for the hands-on workshop"""

from typing import Any
import ast
import re


def implies(a: bool, b: bool) -> bool:
    """Logical implication: a ⇒ b."""
    return (not a) or b

ALLOWED_VARS = ["n","m","is_connected","diameter","num_triangles","max_degree","avg_degree","density"]


ALLOWED_FUNCS = {
    "abs": abs,
    "min": min,
    "max": max,
    "implies": implies,
}

# NOTE: expects ALLOWED_VARS to be defined elsewhere in the notebook
ALLOWED_NAMES = set(ALLOWED_VARS) | set(ALLOWED_FUNCS.keys())

ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
    ast.Name, ast.Load, ast.Constant,
    ast.And, ast.Or, ast.Not,
    ast.Add, ast.Sub, ast.Mult, ast.Div,
    ast.USub,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Call,
    ast.Is, ast.IsNot,
)


def rewrite_implies(expr: str) -> str:
    """
    Rewrite infix 'A implies B' into function form 'implies(A, B)'.

    We do this *before* parsing with `ast`, so users can write:
        "connected implies diameter <= 3"

    Rewrites multiple occurrences by repeatedly applying a conservative regex.
    """
    pattern = r"(.+?)\s+implies\s+(.+)"
    while re.search(pattern, expr):
        expr = re.sub(pattern, r"implies(\1, \2)", expr, count=1)
    return expr


def guard_none_comparisons(env: dict) -> dict:
    """
    Make comparisons safe when some invariants are missing (None).

    Strategy:
      - For every key `k`, add a boolean flag `{k}_is_none`.
      - If env[k] is None, replace it with NaN so numeric comparisons become False.

    This prevents runtime errors like:  None <= 3
    while still allowing explicit checks like:  diameter_is_none
    """
    out = dict(env)
    for k, v in env.items():
        out[f"{k}_is_none"] = (v is None)
        if v is None:
            out[k] = float("nan")
    return out


def safe_eval_expr(expr: str, env: dict) -> bool:
    """
    Safely evaluate a boolean expression over a dict of invariants.

    - Parses with `ast` and rejects any syntax outside a small allowlist.
    - Only allows names in `ALLOWED_NAMES`.
    - Only allows calls to `ALLOWED_FUNCS`.
    - Protects against None comparisons via `guard_none_comparisons`.
    - Supports infix `implies` via `rewrite_implies`.
    """
    expr = rewrite_implies(expr)
    tree = ast.parse(expr, mode="eval")

    env = guard_none_comparisons(env)

    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise ValueError(f"Disallowed syntax: {type(node).__name__}")

        if isinstance(node, ast.Name) and node.id not in ALLOWED_NAMES:
            raise ValueError(f"Disallowed name: {node.id}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
                raise ValueError("Only calls to allowed functions are permitted.")

    compiled = compile(tree, "<expr>", "eval")
    full_env = {**ALLOWED_FUNCS, **env}
    return bool(eval(compiled, {"__builtins__": {}}, full_env))

def print_agent(role: str, text: str) -> None:
    line = "=" * 90
    print(f"\n{line}\n{role}\n{line}\n{text}\n")


def format_conjecture(c: Any) -> str:
    return (
        f"Name: {c.name}\n"
        f"Expr: {c.expr}\n"
        f"Intuition: {c.intuition}"
    )