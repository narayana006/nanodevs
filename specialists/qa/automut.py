"""Simple AST mutation generator. `candidates(source)` yields (description, mutated_source) for single-site mutations.

Operators: comparison swap/boundary (< <= > >= == !=), arithmetic swap (+ - * // %), integer constant +/-1,
and/or swap, True/False flip, min/max swap, sorted -> reverse sorted, `if` condition negation, `return expr` -> `return None`.
Docstrings and string constants are never touched. Equivalence is NOT decided here: build.py keeps a candidate
only if the task's reference tests kill it (so every kept auto-mutant is provably behaviour-changing for the tests).
"""
import ast
import copy

CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
       ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}
ARITH = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add, ast.FloorDiv: ast.Mod, ast.Mod: ast.FloorDiv,
         ast.Div: ast.Mult}
BOOL = {ast.And: ast.Or, ast.Or: ast.And}
FUNC = {"min": "max", "max": "min", "any": "all", "all": "any"}


def _sites(tree):
    """List of (kind, node-path-index, description); we re-walk the copied tree to apply the k-th site."""
    out = []
    for i, n in enumerate(ast.walk(tree)):
        ln = getattr(n, "lineno", 0)
        if isinstance(n, ast.Compare):
            for j, op in enumerate(n.ops):
                if type(op) in CMP:
                    out.append((i, "cmp", j, f"line {ln}: {type(op).__name__} -> {CMP[type(op)].__name__}"))
        elif isinstance(n, ast.BinOp) and type(n.op) in ARITH:
            out.append((i, "bin", 0, f"line {ln}: {type(n.op).__name__} -> {ARITH[type(n.op)].__name__}"))
        elif isinstance(n, ast.BoolOp) and type(n.op) in BOOL:
            out.append((i, "bool", 0, f"line {ln}: {type(n.op).__name__} -> {BOOL[type(n.op)].__name__}"))
        elif isinstance(n, ast.Constant) and type(n.value) is int and n.value not in (0, 1) or \
                isinstance(n, ast.Constant) and type(n.value) is int and n.value in (0, 1):
            out.append((i, "int+", 0, f"line {ln}: constant {n.value} -> {n.value + 1}"))
            out.append((i, "int-", 0, f"line {ln}: constant {n.value} -> {n.value - 1}"))
        elif isinstance(n, ast.Constant) and isinstance(n.value, bool):
            out.append((i, "flip", 0, f"line {ln}: {n.value} -> {not n.value}"))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FUNC:
            out.append((i, "func", 0, f"line {ln}: {n.func.id}() -> {FUNC[n.func.id]}()"))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "sorted" and \
                not any(k.arg == "reverse" for k in n.keywords):
            out.append((i, "rev", 0, f"line {ln}: sorted() -> sorted(reverse=True)"))
        elif isinstance(n, ast.If):
            out.append((i, "neg", 0, f"line {ln}: negate if-condition"))
        elif isinstance(n, ast.Return) and n.value is not None and not (
                isinstance(n.value, ast.Constant) and n.value.value is None):
            out.append((i, "ret", 0, f"line {ln}: return value -> None"))
    return out


def _apply(tree, idx, kind, j):
    t = copy.deepcopy(tree)
    n = list(ast.walk(t))[idx]
    if kind == "cmp":
        n.ops[j] = CMP[type(n.ops[j])]()
    elif kind in ("bin", "bool"):
        n.op = (ARITH if kind == "bin" else BOOL)[type(n.op)]()
    elif kind == "int+":
        n.value += 1
    elif kind == "int-":
        n.value -= 1
    elif kind == "flip":
        n.value = not n.value
    elif kind == "func":
        n.func.id = FUNC[n.func.id]
    elif kind == "rev":
        n.keywords.append(ast.keyword(arg="reverse", value=ast.Constant(value=True)))
    elif kind == "neg":
        n.test = ast.UnaryOp(op=ast.Not(), operand=n.test)
    elif kind == "ret":
        n.value = ast.Constant(value=None)
    ast.fix_missing_locations(t)
    return t


def candidates(source):
    tree = ast.parse(source)
    base = ast.unparse(tree)
    seen = {base}
    for idx, kind, j, desc in _sites(tree):
        try:
            new = ast.unparse(_apply(tree, idx, kind, j))
        except Exception:
            continue
        if new in seen:
            continue
        seen.add(new)
        yield desc, new + "\n"
