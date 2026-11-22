"""Select bounded source context and apply one function edit."""
import ast
from dataclasses import dataclass


class EditRejected(ValueError):
    pass


@dataclass(frozen=True)
class Context:
    function_name: str
    code: str
    source_lines: int
    first_line: int
    last_line: int


def _target(tree, name):
    matches = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1:
        raise EditRejected("Expected exactly one top-level target function")
    if matches[0].decorator_list:
        raise EditRejected("Decorated targets are outside the step-1 edit contract")
    return matches[0]


def select_context(source, name, max_lines=50):
    tree = ast.parse(source)
    target = _target(tree, name)
    definitions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            definitions[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    definitions[child.id] = node
    nodes = [target]
    selected = {id(target)}
    imports = {}
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imports[alias.asname or (alias.name.split(".")[0] if isinstance(node, ast.Import) else alias.name)] = node
    pending = [target]
    while pending:
        node = pending.pop()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                dep = definitions.get(child.id) or imports.get(child.id)
                if dep is not None and id(dep) not in selected:
                    selected.add(id(dep))
                    nodes.append(dep)
                    pending.append(dep)
    lines = source.splitlines()
    spans = sorted({(min([n.lineno] + [d.lineno for d in getattr(n, "decorator_list", [])]), n.end_lineno) for n in nodes})
    indices = sorted({i for a, b in spans for i in range(a - 1, b)})
    if len(indices) > max_lines:
        raise EditRejected(f"Context budget exceeded: {len(indices)} > {max_lines}; no silent truncation")
    parts = []
    for start, end in spans:
        parts.append(f"# source lines {start}-{end}\n" + "\n".join(lines[start - 1:end]))
    return Context(name, "\n\n".join(parts), len(indices), target.lineno, target.end_lineno)


def apply_function_edit(source, name, replacement):
    try:
        original_tree = ast.parse(source)
        replacement_tree = ast.parse(replacement)
    except SyntaxError as error:
        raise EditRejected(f"Invalid Python: {error.msg}") from error
    target = _target(original_tree, name)
    if len(replacement_tree.body) != 1:
        raise EditRejected("Output must contain only the target function")
    new = _target(replacement_tree, name)
    annotation = lambda node: ast.dump(node) if node is not None else None
    if ast.dump(target.args) != ast.dump(new.args) or annotation(target.returns) != annotation(new.returns):
        raise EditRejected("Changing the function signature is not permitted")
    lines = source.splitlines(keepends=True)
    edited = "".join(lines[:target.lineno - 1]) + replacement.rstrip() + "\n" + "".join(lines[target.end_lineno:])
    ast.parse(edited)
    return edited
