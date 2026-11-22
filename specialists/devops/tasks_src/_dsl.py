"""Helpers for writing tasks compactly. Each tasks_src/*.py module exposes TASKS = [T(...), ...]."""
import re
import textwrap

_REG = []


def C(type, desc, bug=False, keep=False, **args):
    """One hidden check. bug=True marks a check that must FAIL on the start state (the injected violation)."""
    d = {"type": type, "desc": desc}
    if bug:
        d["bug"] = True
    if keep:
        d["keep"] = True
    d.update(args)
    return d


def d(s):
    """dedent + strip leading newline, keep trailing newline."""
    return textwrap.dedent(s).lstrip("\n").rstrip("\n") + "\n"


def T(id, kind, domain, difficulty, instruction, reference, checks, start=None, tags=()):
    """kind: write | fix | harden | convert ; domain: dockerfile|compose|k8s|ci|shell|makefile|terraform ;
    start = files given to the model (None => nothing); reference = files that satisfy all checks (also = outputs)."""
    assert kind in ("write", "fix", "harden", "convert"), id
    assert difficulty in ("easy", "medium", "hard"), id
    cs = []
    for i, c in enumerate(checks, 1):
        c = dict(c)
        c["id"] = f"c{i:02d}_{c['type']}"
        cs.append(c)
    return {"id": id, "kind": kind, "domain": domain, "difficulty": difficulty, "tags": list(tags),
            "instruction": textwrap.dedent(instruction).strip(), "files": dict(start or {}),
            "outputs": list(reference.keys()), "reference": dict(reference), "checks": cs}


def Q(desc, file, path, op, value=None, bug=False, keep=False, **kw):
    """Shorthand for a `q` (structured query) check on a YAML/JSON/HCL file."""
    return C("q", desc, bug=bug, keep=keep, file=file, path=path, op=op, value=value, **kw)
