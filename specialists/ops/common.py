"""Shared helpers (stdlib only)."""
import datetime as _dt
import json
import math

UTC = _dt.timezone.utc


def iso(epoch):
    return _dt.datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch_of(y, mo, d, h=0, mi=0, s=0):
    return int(_dt.datetime(y, mo, d, h, mi, s, tzinfo=UTC).timestamp())


def deep_equal(a, b, tol=1e-6):
    """JSON-ish deep equality; floats compared with abs/rel tolerance, bool is not int."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(deep_equal(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(deep_equal(x, y, tol) for x, y in zip(a, b))
    return a == b


def json_objects(text):
    """All JSON objects decodable from `text` (scanning every '{'), in order of appearance, non-overlapping."""
    dec = json.JSONDecoder()
    out, i = [], 0
    while True:
        j = text.find("{", i)
        if j < 0:
            return out
        try:
            obj, end = dec.raw_decode(text, j)
        except ValueError:
            i = j + 1
            continue
        if isinstance(obj, dict):
            out.append(obj)
        i = end


def code_blocks(text):
    """Fenced code blocks -> list of (info, body)."""
    import re
    return [(m.group(1), m.group(2)) for m in re.finditer(r"```([A-Za-z0-9_+-]*)[ \t]*\n(.*?)```", text, re.S)]


def seeded_hex(rng, n):
    return "".join(rng.choice("0123456789abcdef") for _ in range(n))
