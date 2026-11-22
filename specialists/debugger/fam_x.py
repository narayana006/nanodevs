"""Extra untouched helper files so every project has 3-6 files. They are correct code (extra red herrings) that
the hidden tests exercise, so rewriting them counts as collateral damage."""
from fam_a import FAMILIES

X = {
    "page_bounds": ({"labels.py": r'''
def page_label(page, pages):
    return f"Page {page} of {pages}"
'''}, r'''
from labels import page_label
assert page_label(2, @pages@) == "Page 2 of @pages@"
'''),
    "retry_default": ({"logutil.py": r'''
def describe(cfg):
    return ", ".join(f"{k}={cfg[k]}" for k in sorted(cfg))
'''}, r'''
from logutil import describe
assert describe({"b": 1, "a": 2}) == "a=2, b=1"
'''),
    "tally_default": ({"fmt.py": r'''
def render_top(pairs):
    return "\n".join(f"{w}: {n}" for w, n in pairs)
''', "tokens.py": r'''
def split(text):
    return text.lower().split()
'''}, r'''
from fmt import render_top
from tokens import split
assert render_top([("x", 2), ("y", 1)]) == "x: 2\ny: 1"
assert split("A b  C") == ["a", "b", "c"]
'''),
    "grid_alias": ({"moves.py": r'''
def neighbors(r, c, rows, cols):
    out = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            out.append((nr, nc))
    return out
''', "score.py": r'''
def fill_ratio(board, empty="@fill@"):
    cells = [x for row in board for x in row]
    return sum(1 for x in cells if x != empty) / len(cells)
'''}, r'''
from moves import neighbors
from score import fill_ratio
assert sorted(neighbors(0, 0, @R@, @C@)) == [(0, 1), (1, 0)]
assert fill_ratio(b) == 2 / (@R@ * @C@)
'''),
    "to_ms": ({"fmt.py": r'''
def humanize(ms):
    for unit, size in (("d", 86400000), ("h", 3600000), ("m", 60000), ("s", 1000)):
        if ms >= size and ms % size == 0:
            return f"{ms // size}{unit}"
    return f"{ms}ms"
'''}, r'''
from fmt import humanize
assert humanize(120000) == "2m" and humanize(1500) == "1500ms" and humanize(86400000) == "1d"
'''),
    "reserve_swallow": ({"audit.py": r'''
def summarize(shipped, back):
    return f"{len(shipped)} shipped, {len(back)} backordered"
'''}, r'''
from audit import summarize
assert summarize(shipped, back) == "1 shipped, 1 backordered"
'''),
    "nickname_none": ({"badge.py": r'''
from people import initials


def badge(user):
    return f"[{initials(user)}]"
'''}, r'''
from badge import badge
assert badge({"name": "@n1@"}) == "[@ini@]"
'''),
    "leaderboard_order": ({"table.py": r'''
def as_table(pairs):
    return [f"{i}. {name} {score}" for i, (name, score) in enumerate(pairs, 1)]
'''}, r'''
from table import as_table
assert as_table(rank(scores))[0].startswith("1. @first@ ")
assert as_table([]) == []
'''),
    "median_inplace": ({"outliers.py": r'''
def trim(values, k):
    """Drop the k smallest and k largest values."""
    return sorted(values)[k:len(values) - k] if k else list(values)
'''}, r'''
from outliers import trim
assert trim([5, 1, 9, 3, 7], 1) == [3, 5, 7]
assert trim([2, 1], 0) == [2, 1]
'''),
    "tax_half_even": ({"receipt.py": r'''
def line(desc, cents):
    return f"{desc:<10}{cents / 100:>8.2f}"
'''}, r'''
from receipt import line
assert line("tea", 250) == "tea" + " " * 11 + "2.50"
'''),
    "codec_latin1": ({"checksum.py": r'''
import zlib


def crc(text):
    return zlib.crc32(text.encode("utf-8"))
'''}, r'''
from checksum import crc
assert crc("abc") == 891568578
'''),
    "shallow_cfg": ({"sanity.py": r'''
def check(cfg):
    for section in ("db", "cache"):
        if section not in cfg:
            raise ValueError(f"missing section {section}")
    return cfg
'''}, r'''
from sanity import check
assert check(derive({}))["cache"] == {"ttl": 60}
try:
    check({})
    raise SystemExit("expected ValueError")
except ValueError:
    pass
'''),
    "min_score_default": ({"fmtres.py": r'''
def line(row):
    return f"#{row['id']} {row['score']}"
'''}, r'''
from fmtres import line
assert line({"id": 1, "score": 2}) == "#1 2"
'''),
}

for fm in FAMILIES:
    if fm["key"] in X:
        files, extra = X[fm["key"]]
        fm["files"].update(files)
        fm["extra"] = fm["extra"].rstrip("\n") + "\n" + extra.strip("\n") + "\n"
