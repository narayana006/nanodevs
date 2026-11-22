TASKS = []

TASKS.append(dict(
    id="qa_deep_merge", diff="medium",
    spec="Write tests for `deep_merge(a, b)` and `get_path(d, path, default)` in dicts.py.",
    files={"dicts.py": r'''
def deep_merge(a, b):
    """Return a NEW dict: keys of b override keys of a; when both values are dicts they are merged recursively.
    Neither input is modified (nested dicts of the result do not alias the inputs)."""
    out = {}
    for k, v in a.items():
        out[k] = deep_merge(v, {}) if isinstance(v, dict) else v
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = deep_merge(v, {}) if isinstance(v, dict) else v
    return out


def get_path(d, path, default=None):
    """Look up 'a.b.c' in nested dicts. Missing key or a non-dict on the way -> default. Empty path returns d."""
    if path == "":
        return d
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur
'''},
    tests=r'''
from dicts import deep_merge, get_path

assert deep_merge({}, {}) == {}
assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}
assert deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 3, "z": 4}}) == {"a": {"x": 1, "y": 3, "z": 4}}
assert deep_merge({"a": {"x": 1}}, {"a": 5}) == {"a": 5}
assert deep_merge({"a": 5}, {"a": {"x": 1}}) == {"a": {"x": 1}}
assert deep_merge({"a": {"b": {"c": 1}}}, {"a": {"b": {"d": 2}}}) == {"a": {"b": {"c": 1, "d": 2}}}
assert deep_merge({"a": 1}, {"a": None}) == {"a": None}
a = {"n": {"x": 1}, "k": 1}
b = {"n": {"y": 2}, "m": {"z": 3}}
r = deep_merge(a, b)
assert a == {"n": {"x": 1}, "k": 1} and b == {"n": {"y": 2}, "m": {"z": 3}}
r["n"]["x"] = 99
r["m"]["z"] = 99
assert a["n"]["x"] == 1 and b["m"]["z"] == 3
only = {"o": {"x": 1}}
ro = deep_merge(only, {})
ro["o"]["x"] = 9
assert only == {"o": {"x": 1}}
r2 = deep_merge({}, b)
r2["m"]["z"] = 0
assert b["m"]["z"] == 3
assert get_path({"a": {"b": {"c": 5}}}, "a.b.c") == 5
assert get_path({"a": {"b": 1}}, "a.b") == 1
assert get_path({"a": {"b": 1}}, "a.x", "dflt") == "dflt"
assert get_path({"a": {"b": 1}}, "a.b.c", "dflt") == "dflt"
assert get_path({"a": 1}, "") == {"a": 1}
assert get_path({}, "a") is None
assert get_path({"a": None}, "a", "d") is None
assert get_path({"a": {"b": 0}}, "a.b", 9) == 0
''',
    muts=[
        ("logic: b does not override", "            out[k] = deep_merge(v, {}) if isinstance(v, dict) else v\n\n\ndef get", "            out.setdefault(k, deep_merge(v, {}) if isinstance(v, dict) else v)\n\n\ndef get") if False else ("logic: b does not override", "        if k in out and isinstance(out[k], dict) and isinstance(v, dict):\n            out[k] = deep_merge(out[k], v)\n        else:\n            out[k] = deep_merge(v, {}) if isinstance(v, dict) else v", "        if k in out and isinstance(out[k], dict) and isinstance(v, dict):\n            out[k] = deep_merge(out[k], v)\n        elif k not in out:\n            out[k] = deep_merge(v, {}) if isinstance(v, dict) else v"),
        ("logic: shallow merge", "out[k] = deep_merge(out[k], v)", "out[k] = v"),
        ("logic: input aliased (a)", "out[k] = deep_merge(v, {}) if isinstance(v, dict) else v\n    for", "out[k] = v\n    for"),
        ("logic: input aliased (b)", "        else:\n            out[k] = deep_merge(v, {}) if isinstance(v, dict) else v", "        else:\n            out[k] = v"),
        ("missing-edge-case: non-dict on the way", "if not isinstance(cur, dict) or part not in cur:", "if part not in cur:"),
        ("missing-edge-case: empty path", '    if path == "":\n        return d\n', ""),
        ("wrong-default: default argument", "def get_path(d, path, default=None):", "def get_path(d, path, default=0):"),
        ("logic: falsy values replaced by default", "    return cur\n", "    return cur or default\n"),
    ],
    weak=10,
))

TASKS.append(dict(
    id="qa_flatten_dict", diff="medium",
    spec="Write tests for `flatten(d, sep='.')` and `unflatten(d, sep='.')` in flat.py.",
    files={"flat.py": r'''
def flatten(d, sep="."):
    """{'a': {'b': 1}, 'c': 2} -> {'a.b': 1, 'c': 2}. Empty nested dicts are kept as {} under their key.
    Keys must be strings (else TypeError). Result keys are in depth-first insertion order."""
    out = {}

    def walk(node, prefix):
        for k, v in node.items():
            if not isinstance(k, str):
                raise TypeError("keys must be strings")
            key = prefix + sep + k if prefix else k
            if isinstance(v, dict) and v:
                walk(v, key)
            else:
                out[key] = v

    walk(d, "")
    return out


def unflatten(d, sep="."):
    """Inverse of flatten. A key that is both a leaf and a prefix of another key -> ValueError."""
    out = {}
    for key, v in d.items():
        parts = key.split(sep)
        cur = out
        for p in parts[:-1]:
            nxt = cur.setdefault(p, {})
            if not isinstance(nxt, dict):
                raise ValueError("conflict at %r" % p)
            cur = nxt
        if parts[-1] in cur and isinstance(cur[parts[-1]], dict) and cur[parts[-1]]:
            raise ValueError("conflict at %r" % key)
        cur[parts[-1]] = v
    return out
'''},
    tests=r'''
from flat import flatten, unflatten

assert flatten({}) == {}
assert flatten({"a": 1}) == {"a": 1}
assert flatten({"a": {"b": 1}, "c": 2}) == {"a.b": 1, "c": 2}
assert flatten({"a": {"b": {"c": {"d": 4}}}}) == {"a.b.c.d": 4}
assert flatten({"a": {}}) == {"a": {}}
assert flatten({"a": {"b": {}}}) == {"a.b": {}}
assert flatten({"a": {"b": 1}}, sep="/") == {"a/b": 1}
assert flatten({"a": [1, 2], "b": {"c": [3]}}) == {"a": [1, 2], "b.c": [3]}
assert list(flatten({"z": {"y": 1, "x": 2}, "a": 3})) == ["z.y", "z.x", "a"]
assert flatten({"a": None}) == {"a": None}
try:
    flatten({1: 2})
except TypeError:
    pass
else:
    raise AssertionError("expected TypeError")
try:
    flatten({"a": {2: 3}})
except TypeError:
    pass
else:
    raise AssertionError("expected TypeError")
assert unflatten({}) == {}
assert unflatten({"a.b": 1, "c": 2}) == {"a": {"b": 1}, "c": 2}
assert unflatten({"a.b.c.d": 4}) == {"a": {"b": {"c": {"d": 4}}}}
assert unflatten({"a/b": 1}, sep="/") == {"a": {"b": 1}}
assert unflatten({"a.b": 1, "a.c": 2}) == {"a": {"b": 1, "c": 2}}
assert unflatten({"a": {}}) == {"a": {}}
for case in ({"a": 1, "a.b": 2}, {"a.b": 2, "a": 1}, {"a.b": 1, "a.b.c": 2}):
    try:
        unflatten(case)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % case)
orig = {"x": {"y": {"z": 1}, "w": 2}, "v": 3}
assert unflatten(flatten(orig)) == orig
''',
    muts=[
        ("missing-edge-case: empty dict dropped", "if isinstance(v, dict) and v:", "if isinstance(v, dict):"),
        ("logic: separator hardcoded", "prefix + sep + k", 'prefix + "." + k'),
        ("missing-edge-case: non-string keys", '            if not isinstance(k, str):\n                raise TypeError("keys must be strings")\n', ""),
        ("exception-type", 'raise TypeError("keys must be strings")', 'raise ValueError("keys must be strings")'),
        ("missing-edge-case: leaf/prefix conflict", '            if not isinstance(nxt, dict):\n                raise ValueError("conflict at %r" % p)\n', ""),
        ("missing-edge-case: later conflict", 'if parts[-1] in cur and isinstance(cur[parts[-1]], dict) and cur[parts[-1]]:\n            raise ValueError("conflict at %r" % key)', "if False:\n            pass"),
        ("logic: unflatten splits only once", "key.split(sep)", "key.split(sep, 1)"),
        ("logic: prefix and key swapped", "prefix + sep + k", "k + sep + prefix"),
    ],
    weak=10,
))

TASKS.append(dict(
    id="qa_group_by", diff="easy",
    spec="Write tests for `group_by(items, key)` and `partition(items, pred)` in grouping.py.",
    files={"grouping.py": r'''
def group_by(items, key):
    """Dict key(item) -> list of items, preserving the input order inside each list and the first-seen order of
    keys."""
    out = {}
    for x in items:
        out.setdefault(key(x), []).append(x)
    return out


def partition(items, pred):
    """(matching, others) -- two lists, each in input order. The input may be any iterable (a generator is
    consumed exactly once)."""
    yes, no = [], []
    for x in items:
        (yes if pred(x) else no).append(x)
    return yes, no
'''},
    tests=r'''
from grouping import group_by, partition

assert group_by([], len) == {}
assert group_by(["a", "bb", "c", "dd", "eee"], len) == {1: ["a", "c"], 2: ["bb", "dd"], 3: ["eee"]}
assert list(group_by(["bb", "a", "cc"], len)) == [2, 1]
assert group_by([3, 1, 2, 1, 3], lambda x: x % 2) == {1: [3, 1, 1, 3], 0: [2]}
assert group_by(range(6), lambda x: x % 3 == 0) == {True: [0, 3], False: [1, 2, 4, 5]}
assert group_by([1, 2, 3], lambda x: "all") == {"all": [1, 2, 3]}
g = group_by([1, 2], str)
g["1"].append(9)
assert group_by([1, 2], str) == {"1": [1], "2": [2]}
assert partition([], bool) == ([], [])
assert partition([1, 2, 3, 4, 5], lambda x: x > 2) == ([3, 4, 5], [1, 2])
assert partition([5, 1, 4, 2], lambda x: x % 2 == 0) == ([4, 2], [5, 1])
assert partition([1, 2], lambda x: True) == ([1, 2], [])
assert partition([1, 2], lambda x: False) == ([], [1, 2])
assert partition(iter([0, 1, 2, 0]), bool) == ([1, 2], [0, 0])
assert partition((x for x in range(4)), lambda x: x < 2) == ([0, 1], [2, 3])
''',
    muts=[
        ("ordering: group order reversed", "setdefault(key(x), []).append(x)", "setdefault(key(x), []).insert(0, x)"),
        ("ordering: partition reversed", "(yes if pred(x) else no).append(x)", "(yes if pred(x) else no).insert(0, x)"),
        ("logic: partition swapped", "(yes if pred(x) else no).append(x)", "(no if pred(x) else yes).append(x)"),
        ("logic: key evaluated on wrong value", "setdefault(key(x), [])", "setdefault(x, [])"),
        ("logic: truthiness instead of predicate", "(yes if pred(x) else no)", "(yes if x else no)"),
        ("logic: last item per group only", "out.setdefault(key(x), []).append(x)", "out[key(x)] = [x]"),
        ("logic: shared list", "    yes, no = [], []\n", "    yes = no = []\n"),
    ],
    weak=7,
))

TASKS.append(dict(
    id="qa_paginate", diff="easy",
    spec="Write tests for `paginate(items, page, per_page)` and `page_count(total, per_page)` in paging.py.",
    files={"paging.py": r'''
def page_count(total, per_page):
    """Number of pages needed for `total` items (at least 1, even when total is 0). per_page < 1 -> ValueError."""
    if per_page < 1:
        raise ValueError("per_page must be >= 1")
    return max(1, -(-total // per_page))


def paginate(items, page, per_page):
    """Return dict with keys: items (the slice for 1-based `page`), page, pages, has_prev, has_next.
    page < 1 or page > pages -> ValueError. per_page < 1 -> ValueError."""
    pages = page_count(len(items), per_page)
    if not 1 <= page <= pages:
        raise ValueError("page out of range")
    start = (page - 1) * per_page
    return {"items": items[start:start + per_page], "page": page, "pages": pages,
            "has_prev": page > 1, "has_next": page < pages}
'''},
    tests=r'''
from paging import paginate, page_count

assert page_count(0, 10) == 1
assert page_count(1, 10) == 1
assert page_count(10, 10) == 1
assert page_count(11, 10) == 2
assert page_count(20, 10) == 2
assert page_count(21, 10) == 3
assert page_count(5, 1) == 5
try:
    page_count(5, 0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
xs = list(range(1, 11))
r = paginate(xs, 1, 4)
assert r == {"items": [1, 2, 3, 4], "page": 1, "pages": 3, "has_prev": False, "has_next": True}
r = paginate(xs, 2, 4)
assert r == {"items": [5, 6, 7, 8], "page": 2, "pages": 3, "has_prev": True, "has_next": True}
r = paginate(xs, 3, 4)
assert r == {"items": [9, 10], "page": 3, "pages": 3, "has_prev": True, "has_next": False}
assert paginate([], 1, 5) == {"items": [], "page": 1, "pages": 1, "has_prev": False, "has_next": False}
assert paginate([1, 2], 1, 2) == {"items": [1, 2], "page": 1, "pages": 1, "has_prev": False, "has_next": False}
assert paginate("abcde", 2, 2)["items"] == "cd"
for page in (0, -1, 4):
    try:
        paginate(xs, page, 4)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for page %r" % page)
try:
    paginate(xs, 1, 0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("rounding: page count floors", "-(-total // per_page)", "total // per_page"),
        ("missing-edge-case: zero items has one page", "max(1, -(-total // per_page))", "-(-total // per_page)"),
        ("off-by-one: slice start", "start = (page - 1) * per_page", "start = page * per_page"),
        ("boundary: last page rejected", "not 1 <= page <= pages", "not 1 <= page < pages"),
        ("boundary: page 0 accepted", "not 1 <= page <= pages", "not 0 <= page <= pages"),
        ("comparison: has_next", '"has_next": page < pages', '"has_next": page <= pages'),
        ("comparison: has_prev", '"has_prev": page > 1', '"has_prev": page >= 1'),
        ("boundary: per_page 1 rejected", "if per_page < 1:", "if per_page < 2:"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_text_wrap", diff="hard",
    spec="Write tests for `wrap(text, width)` in wrapper.py.",
    files={"wrapper.py": r'''
def wrap(text, width):
    """Greedy word wrap into a list of lines no longer than width. Words are separated by whitespace (any run).
    A word longer than width is split into chunks of width characters. Empty or whitespace-only text -> [].
    width < 1 -> ValueError. Lines contain single spaces between words and no trailing spaces."""
    if width < 1:
        raise ValueError("width must be >= 1")
    lines = []
    cur = ""
    for word in text.split():
        while len(word) > width:
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(word[:width])
            word = word[width:]
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines
'''},
    tests=r'''
from wrapper import wrap

assert wrap("", 10) == []
assert wrap("   \n ", 10) == []
assert wrap("hello", 10) == ["hello"]
assert wrap("hello world", 11) == ["hello world"]
assert wrap("hello world", 10) == ["hello", "world"]
assert wrap("a b c d e", 3) == ["a b", "c d", "e"]
assert wrap("a b c d e", 4) == ["a b", "c d", "e"]
assert wrap("aaa bbb ccc", 7) == ["aaa bbb", "ccc"]
assert wrap("aaa bbb ccc", 8) == ["aaa bbb", "ccc"]
assert wrap("aaa bbb ccc", 11) == ["aaa bbb ccc"]
assert wrap("a    b\n\nc", 10) == ["a b c"]
assert wrap("abcdefgh", 3) == ["abc", "def", "gh"]
assert wrap("abcd", 3) == ["abc", "d"]
assert wrap("abcdef", 3) == ["abc", "def"]
assert wrap("hi abcdefg yo", 3) == ["hi", "abc", "def", "g", "yo"]
assert wrap("x abcdef", 3) == ["x", "abc", "def"]
assert wrap("ab abcd", 4) == ["ab", "abcd"]
assert wrap("abc d", 3) == ["abc", "d"]
assert wrap("a b", 1) == ["a", "b"]
assert wrap("  lead and trail  ", 20) == ["lead and trail"]
assert all(len(l) <= 5 for l in wrap("the quick brown fox jumps over the lazy dog", 5))
assert wrap("the quick brown fox", 9) == ["the quick", "brown fox"]
for w in (0, -3):
    try:
        wrap("a", w)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("boundary: line exactly width rejected", "len(cur) + 1 + len(word) <= width", "len(cur) + 1 + len(word) < width"),
        ("boundary: line too long by one", "len(cur) + 1 + len(word) <= width", "len(cur) + 1 + len(word) <= width + 1"),
        ("boundary: word one longer than width not split", "while len(word) > width:", "while len(word) > width + 1:"),
        ("missing-edge-case: last line dropped", "    if cur:\n        lines.append(cur)\n    return lines", "    return lines"),
        ("missing-edge-case: pending line before long word", "            if cur:\n                lines.append(cur)\n                cur = \"\"\n", ""),
        ("logic: long-word remainder dropped", "            word = word[width:]\n", "            word = ''\n"),
        ("logic: only single spaces split", "text.split()", 'text.split(" ")'),
        ("boundary: width 1 rejected", "if width < 1:", "if width < 2:"),
    ],
    weak=12,
))

TASKS.append(dict(
    id="qa_mutable_default", diff="medium",
    spec="Write tests for `add_tag`, `Counter2` and `make_report` in tags.py. Watch for state leaking between calls.",
    files={"tags.py": r'''
def add_tag(tag, tags=None):
    """Return a list with `tag` appended to `tags` (a new list; the argument is never modified). With no list
    given, start from an empty one: independent calls never share state."""
    if tags is None:
        tags = []
    return list(tags) + [tag]


class Counter2:
    """Counts events per name. __init__(initial=None): optional dict of starting counts (copied, not aliased).
    hit(name, n=1) adds n; reset() clears everything; snapshot() returns a copy of the counts."""

    def __init__(self, initial=None):
        self.counts = dict(initial) if initial else {}

    def hit(self, name, n=1):
        self.counts[name] = self.counts.get(name, 0) + n

    def reset(self):
        self.counts = {}

    def snapshot(self):
        return dict(self.counts)


def make_report(title, rows=None, footer=None):
    """Dict {'title', 'rows': list copy of rows or [], 'footer': footer or 'end'}. Mutating the returned rows never
    affects the argument or later reports."""
    return {"title": title, "rows": list(rows) if rows else [], "footer": footer or "end"}
'''},
    tests=r'''
from tags import add_tag, Counter2, make_report

assert add_tag("a") == ["a"]
assert add_tag("b") == ["b"]
assert add_tag("c") == ["c"]
base = ["x"]
assert add_tag("y", base) == ["x", "y"]
assert base == ["x"]
assert add_tag("z", []) == ["z"]
r = add_tag("q")
r.append("junk")
assert add_tag("q") == ["q"]

c = Counter2()
c.hit("a")
c.hit("a", 2)
assert c.snapshot() == {"a": 3}
d = Counter2()
assert d.snapshot() == {}
init = {"x": 1}
e = Counter2(init)
e.hit("x")
assert init == {"x": 1} and e.snapshot() == {"x": 2}
s = e.snapshot()
s["x"] = 100
assert e.snapshot() == {"x": 2}
e.reset()
assert e.snapshot() == {}
e.hit("y", 5)
assert e.snapshot() == {"y": 5}
f = Counter2({})
f.hit("k")
assert Counter2().snapshot() == {} and Counter2({}).snapshot() == {}

r1 = make_report("T")
assert r1 == {"title": "T", "rows": [], "footer": "end"}
r1["rows"].append(1)
r2 = make_report("U")
assert r2["rows"] == []
rows = [1, 2]
r3 = make_report("V", rows, "bye")
assert r3 == {"title": "V", "rows": [1, 2], "footer": "bye"}
r3["rows"].append(3)
assert rows == [1, 2]
assert make_report("W", [], "")["footer"] == "end"
assert make_report("X", None, None) == {"title": "X", "rows": [], "footer": "end"}
''',
    muts=[
        ("mutable-default: shared default list", "def add_tag(tag, tags=None):", "def add_tag(tag, tags=[]):") if False else ("mutable-default: add_tag mutates shared list", "def add_tag(tag, tags=None):\n    \"\"\"Return a list with `tag` appended to `tags` (a new list; the argument is never modified). With no list\n    given, start from an empty one: independent calls never share state.\"\"\"\n    if tags is None:\n        tags = []\n    return list(tags) + [tag]", "_SHARED = []\n\n\ndef add_tag(tag, tags=None):\n    if tags is None:\n        tags = _SHARED\n    tags.append(tag)\n    return list(tags)"),
        ("logic: add_tag mutates argument", "return list(tags) + [tag]", "tags.append(tag)\n    return tags"),
        ("logic: counter aliases initial", "self.counts = dict(initial) if initial else {}", "self.counts = initial if initial else {}"),
        ("logic: snapshot aliases", "return dict(self.counts)", "return self.counts"),
        ("logic: reset keeps counts", "        self.counts = {}\n\n    def snapshot", "        pass\n\n    def snapshot"),
        ("wrong-default: hit increment", "def hit(self, name, n=1):", "def hit(self, name, n=2):"),
        ("mutable-default: shared rows", "\"rows\": list(rows) if rows else []", "\"rows\": rows if rows is not None else _ROWS"),
        ("logic: footer empty string kept", 'footer or "end"', 'footer if footer is not None else "end"'),
        ("logic: rows aliased", "list(rows) if rows else []", "rows if rows else []"),
    ][:8] if False else [
        ("mutable-default: add_tag shares list", "def add_tag(tag, tags=None):\n    \"\"\"Return a list with `tag` appended to `tags` (a new list; the argument is never modified). With no list\n    given, start from an empty one: independent calls never share state.\"\"\"\n    if tags is None:\n        tags = []\n    return list(tags) + [tag]", "_SHARED = []\n\n\ndef add_tag(tag, tags=None):\n    if tags is None:\n        tags = _SHARED\n    tags.append(tag)\n    return list(tags)"),
        ("logic: add_tag mutates argument", "return list(tags) + [tag]", "tags.append(tag)\n    return tags"),
        ("logic: counter aliases initial", "self.counts = dict(initial) if initial else {}", "self.counts = initial if initial else {}"),
        ("logic: snapshot aliases", "return dict(self.counts)", "return self.counts"),
        ("logic: reset keeps counts", "        self.counts = {}\n\n    def snapshot", "        pass\n\n    def snapshot"),
        ("wrong-default: hit increment", "def hit(self, name, n=1):", "def hit(self, name, n=2):"),
        ("logic: footer empty string kept", 'footer or "end"', 'footer if footer is not None else "end"'),
        ("logic: rows aliased", "list(rows) if rows else []", "rows if rows else []"),
    ],
    weak=8,
))

TASKS.append(dict(
    id="qa_stats", diff="easy",
    spec="Write tests for `mean`, `median`, `mode` and `variance` in descstats.py.",
    files={"descstats.py": r'''
def mean(xs):
    """Arithmetic mean. Empty -> ValueError."""
    if not xs:
        raise ValueError("empty")
    return sum(xs) / len(xs)


def median(xs):
    """Median (average of the two middle values for even length). Does not modify xs. Empty -> ValueError."""
    if not xs:
        raise ValueError("empty")
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def mode(xs):
    """Most common value; if several tie, the SMALLEST of them. Empty -> ValueError."""
    if not xs:
        raise ValueError("empty")
    counts = {}
    for x in xs:
        counts[x] = counts.get(x, 0) + 1
    best = max(counts.values())
    return min(k for k, c in counts.items() if c == best)


def variance(xs, sample=False):
    """Population variance, or sample variance (n - 1 divisor) when sample=True.
    Empty -> ValueError; sample variance of a single value -> ValueError."""
    if not xs or (sample and len(xs) < 2):
        raise ValueError("not enough data")
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1 if sample else len(xs))
'''},
    tests=r'''
from descstats import mean, median, mode, variance

assert mean([1, 2, 3, 4]) == 2.5
assert mean([5]) == 5
assert mean([-1, 1]) == 0
assert median([3, 1, 2]) == 2
assert median([4, 1, 3, 2]) == 2.5
assert median([7]) == 7
assert median([1, 2]) == 1.5
assert median([5, 5, 1, 9, 9]) == 5
xs = [3, 1, 2]
median(xs)
assert xs == [3, 1, 2]
assert mode([1, 2, 2, 3]) == 2
assert mode([1, 1, 2, 2]) == 1
assert mode([3, 3, 2, 2, 1]) == 2
assert mode(["b", "a", "b"]) == "b"
assert mode([5]) == 5
assert variance([2, 4, 4, 4, 5, 5, 7, 9]) == 4.0
assert variance([1, 2, 3, 4], sample=True) == 5 / 3
assert variance([5, 5, 5]) == 0
assert variance([1, 3]) == 1.0
assert variance([1, 3], sample=True) == 2.0
for fn, args in ((mean, ([],)), (median, ([],)), (mode, ([],)), (variance, ([],)), (variance, ([1], True)), (variance, ([], True))):
    try:
        fn(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % (args,))
assert variance([4]) == 0
''',
    muts=[
        ("logic: mean divisor", "return sum(xs) / len(xs)", "return sum(xs) / (len(xs) + 1)"),
        ("off-by-one: median even index", "(s[mid - 1] + s[mid]) / 2", "(s[mid] + s[mid + 1 if mid + 1 < n else mid]) / 2"),
        ("missing-edge-case: median sorts input in place", "s = sorted(xs)", "s = xs\n    s.sort()"),
        ("ordering: median unsorted", "s = sorted(xs)", "s = list(xs)"),
        ("ordering: mode tie picks largest", "return min(k for k, c in counts.items() if c == best)", "return max(k for k, c in counts.items() if c == best)"),
        ("logic: sample divisor ignored", "(len(xs) - 1 if sample else len(xs))", "len(xs)"),
        ("boundary: single sample", "(sample and len(xs) < 2)", "(sample and len(xs) < 1)"),
        ("logic: median odd/even", "s[mid] if n % 2 else", "s[mid] if n % 2 == 0 else"),
    ],
    weak=12,
))

TASKS.append(dict(
    id="qa_bit_tricks", diff="medium",
    spec="Write tests for `popcount`, `is_power_of_two`, `set_bit`, `clear_bit`, `toggle_bit`, `test_bit` in bits.py.",
    files={"bits.py": r'''
def popcount(n):
    """Number of 1 bits in a non-negative int. Negative -> ValueError."""
    if n < 0:
        raise ValueError("negative")
    c = 0
    while n:
        n &= n - 1
        c += 1
    return c


def is_power_of_two(n):
    """True for 1, 2, 4, 8, ...; False for 0 and negatives."""
    return n > 0 and n & (n - 1) == 0


def set_bit(n, i):
    """Set bit i (0 = least significant). i < 0 -> ValueError."""
    if i < 0:
        raise ValueError("negative bit")
    return n | (1 << i)


def clear_bit(n, i):
    if i < 0:
        raise ValueError("negative bit")
    return n & ~(1 << i)


def toggle_bit(n, i):
    if i < 0:
        raise ValueError("negative bit")
    return n ^ (1 << i)


def test_bit(n, i):
    if i < 0:
        raise ValueError("negative bit")
    return (n >> i) & 1 == 1
'''},
    tests=r'''
from bits import popcount, is_power_of_two, set_bit, clear_bit, toggle_bit, test_bit

assert popcount(0) == 0
assert popcount(1) == 1
assert popcount(7) == 3
assert popcount(8) == 1
assert popcount(255) == 8
assert popcount(2 ** 40 + 1) == 2
try:
    popcount(-1)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
for n in (1, 2, 4, 8, 1024, 2 ** 40):
    assert is_power_of_two(n) is True
for n in (0, 3, 5, 6, 12, 1023, -2, -4):
    assert is_power_of_two(n) is False
assert set_bit(0, 0) == 1
assert set_bit(0, 3) == 8
assert set_bit(5, 1) == 7
assert set_bit(5, 0) == 5
assert clear_bit(7, 1) == 5
assert clear_bit(5, 1) == 5
assert clear_bit(1, 0) == 0
assert toggle_bit(5, 1) == 7
assert toggle_bit(7, 1) == 5
assert toggle_bit(0, 4) == 16
assert test_bit(5, 0) is True
assert test_bit(5, 1) is False
assert test_bit(5, 2) is True
assert test_bit(5, 3) is False
assert test_bit(0, 100) is False
for fn in (set_bit, clear_bit, toggle_bit, test_bit):
    try:
        fn(5, -1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("boundary: zero is power of two", "return n > 0 and", "return n >= 0 and"),
        ("logic: power of two check", "n & (n - 1) == 0", "n & (n + 1) == 0"),
        ("logic: popcount", "n &= n - 1", "n >>= 1"),
        ("missing-edge-case: popcount negative", 'if n < 0:\n        raise ValueError("negative")\n    c = 0', "c = 0"),
        ("logic: set_bit uses xor", "return n | (1 << i)", "return n ^ (1 << i)"),
        ("logic: clear_bit uses toggle", "return n & ~(1 << i)", "return n ^ (1 << i)"),
        ("off-by-one: test_bit index", "(n >> i) & 1 == 1", "(n >> (i + 1)) & 1 == 1"),
        ("missing-edge-case: negative bit in toggle", '        raise ValueError("negative bit")\n    return n ^ (1 << i)', '        pass\n    return n ^ (1 << i) if i >= 0 else n'),
    ],
    weak=14,
))

TASKS.append(dict(
    id="qa_base_convert", diff="medium",
    spec="Write tests for `to_base(n, base)` and `from_base(s, base)` in baseconv.py.",
    files={"baseconv.py": r'''
DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def to_base(n, base):
    """Integer -> string in base 2..36 using lower-case digits; negative numbers get a leading '-'.
    base outside 2..36 -> ValueError."""
    if not 2 <= base <= 36:
        raise ValueError("bad base")
    if n == 0:
        return "0"
    sign = "-" if n < 0 else ""
    n = abs(n)
    out = []
    while n:
        n, r = divmod(n, base)
        out.append(DIGITS[r])
    return sign + "".join(reversed(out))


def from_base(s, base):
    """Inverse of to_base; accepts upper or lower case and a leading '-' or '+'. Empty string, a lone sign, or
    a digit not valid in the base -> ValueError."""
    if not 2 <= base <= 36:
        raise ValueError("bad base")
    sign = 1
    if s[:1] in ("-", "+"):
        sign = -1 if s[0] == "-" else 1
        s = s[1:]
    if not s:
        raise ValueError("no digits")
    n = 0
    for ch in s.lower():
        d = DIGITS.find(ch)
        if d < 0 or d >= base:
            raise ValueError("bad digit %r" % ch)
        n = n * base + d
    return sign * n
'''},
    tests=r'''
from baseconv import to_base, from_base

assert to_base(0, 2) == "0"
assert to_base(5, 2) == "101"
assert to_base(255, 16) == "ff"
assert to_base(255, 8) == "377"
assert to_base(35, 36) == "z"
assert to_base(36, 36) == "10"
assert to_base(-10, 2) == "-1010"
assert to_base(1, 10) == "1"
assert to_base(1000, 10) == "1000"
for b in (0, 1, 37, -2):
    try:
        to_base(5, b)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
assert from_base("101", 2) == 5
assert from_base("ff", 16) == 255
assert from_base("FF", 16) == 255
assert from_base("-ff", 16) == -255
assert from_base("+7", 10) == 7
assert from_base("z", 36) == 35
assert from_base("0", 2) == 0
assert from_base("-0", 10) == 0
assert from_base("377", 8) == 255
for s, b in (("", 10), ("-", 10), ("+", 2), ("2", 2), ("g", 16), ("1.5", 10), ("a", 10), ("9", 8)):
    try:
        from_base(s, b)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r base %r" % (s, b))
for b in (1, 37):
    try:
        from_base("1", b)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
for n in (0, 1, 99, -1234, 2 ** 70):
    for b in (2, 7, 16, 36):
        assert from_base(to_base(n, b), b) == n
''',
    muts=[
        ("boundary: base 36 rejected", "not 2 <= base <= 36:\n        raise ValueError(\"bad base\")\n    if n == 0", "not 2 <= base < 36:\n        raise ValueError(\"bad base\")\n    if n == 0"),
        ("boundary: base 2 rejected", "not 2 <= base <= 36:\n        raise ValueError(\"bad base\")\n    if n == 0", "not 2 < base <= 36:\n        raise ValueError(\"bad base\")\n    if n == 0"),
        ("missing-edge-case: zero", '    if n == 0:\n        return "0"\n', ""),
        ("logic: negative sign lost", 'sign = "-" if n < 0 else ""', 'sign = ""'),
        ("ordering: digits not reversed", '"".join(reversed(out))', '"".join(out)'),
        ("boundary: digit equal to base accepted", "d < 0 or d >= base", "d < 0 or d > base"),
        ("missing-edge-case: upper case digits", "for ch in s.lower():", "for ch in s:"),
        ("missing-edge-case: lone sign", '    if not s:\n        raise ValueError("no digits")\n', ""),
    ],
    weak=10,
))

TASKS.append(dict(
    id="qa_string_utils", diff="easy",
    spec="Write tests for `truncate`, `is_palindrome`, `center` and `count_vowels` in strutil.py.",
    files={"strutil.py": r'''
def truncate(s, n, ellipsis="..."):
    """Shorten s to at most n characters INCLUDING the ellipsis: s itself if len(s) <= n; otherwise
    s[:n - len(ellipsis)] + ellipsis. If n is smaller than the ellipsis, return ellipsis[:n]. n < 0 -> ValueError."""
    if n < 0:
        raise ValueError("n must be >= 0")
    if len(s) <= n:
        return s
    if n < len(ellipsis):
        return ellipsis[:n]
    return s[:n - len(ellipsis)] + ellipsis


def is_palindrome(s):
    """Ignoring case and every non-alphanumeric character. The empty string is a palindrome."""
    t = [c.lower() for c in s if c.isalnum()]
    return t == t[::-1]


def center(s, width, fill=" "):
    """Center s in width characters. If the padding is odd the extra fill goes on the RIGHT.
    If s is already as wide as width, return it unchanged. fill must be one character else ValueError."""
    if len(fill) != 1:
        raise ValueError("fill must be one character")
    pad = width - len(s)
    if pad <= 0:
        return s
    left = pad // 2
    return fill * left + s + fill * (pad - left)


def count_vowels(s):
    """Number of a, e, i, o, u (either case); 'y' is not a vowel."""
    return sum(1 for c in s.lower() if c in "aeiou")
'''},
    tests=r'''
from strutil import truncate, is_palindrome, center, count_vowels

assert truncate("hello", 10) == "hello"
assert truncate("hello", 5) == "hello"
assert truncate("hello world", 8) == "hello..."
assert truncate("hello world", 6) == "hel..."
assert truncate("hello", 4) == "h..."
assert truncate("hello", 3) == "..."
assert truncate("hello", 2) == ".."
assert truncate("hello", 0) == ""
assert truncate("", 0) == ""
assert truncate("hello world", 8, "~") == "hello w~"
assert truncate("abcdef", 5, "") == "abcde"
try:
    truncate("a", -1)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert is_palindrome("") is True
assert is_palindrome("a") is True
assert is_palindrome("racecar") is True
assert is_palindrome("A man, a plan, a canal: Panama") is True
assert is_palindrome("hello") is False
assert is_palindrome("ab") is False
assert is_palindrome("12321") is True
assert is_palindrome("12345") is False
assert is_palindrome("!!") is True
assert is_palindrome("Aa") is True
assert center("ab", 6) == "  ab  "
assert center("ab", 5) == " ab  "
assert center("ab", 2) == "ab"
assert center("abc", 2) == "abc"
assert center("", 3, "*") == "***"
assert center("x", 4, "-") == "-x--"
try:
    center("x", 5, "ab")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert count_vowels("") == 0
assert count_vowels("hello") == 2
assert count_vowels("AEIOU") == 5
assert count_vowels("rhythm") == 0
assert count_vowels("yY") == 0
assert count_vowels("Queue") == 4
''',
    muts=[
        ("boundary: exact length truncated", "if len(s) <= n:", "if len(s) < n:"),
        ("off-by-one: ellipsis counted", "return s[:n - len(ellipsis)] + ellipsis", "return s[:n - len(ellipsis) + 1] + ellipsis"),
        ("missing-edge-case: tiny n", "    if n < len(ellipsis):\n        return ellipsis[:n]\n", ""),
        ("boundary: n=0 rejected", "if n < 0:", "if n < 1:"),
        ("missing-edge-case: non-alnum ignored", "for c in s if c.isalnum()", "for c in s"),
        ("logic: case-sensitive palindrome", "c.lower() for c in s if", "c for c in s if"),
        ("logic: extra pad on left", "left = pad // 2", "left = (pad + 1) // 2"),
        ("logic: y is a vowel", 'c in "aeiou"', 'c in "aeiouy"'),
    ],
    weak=13,
))

TASKS.append(dict(
    id="qa_memoize", diff="hard",
    spec="Write tests for the `memoize` decorator and `cache_info` in memo.py.",
    files={"memo.py": r'''
def memoize(fn):
    """Cache results by positional AND keyword arguments (f(1, b=2) and f(1, 2) are different keys; keyword order
    does not matter). Exceptions are NOT cached (the function is called again next time). Arguments must be
    hashable. The wrapper has .hits, .misses (ints) and .clear() which empties the cache and resets the counters."""
    cache = {}

    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key in cache:
            wrapper.hits += 1
            return cache[key]
        result = fn(*args, **kwargs)
        wrapper.misses += 1
        cache[key] = result
        return result

    def clear():
        cache.clear()
        wrapper.hits = 0
        wrapper.misses = 0

    wrapper.hits = 0
    wrapper.misses = 0
    wrapper.clear = clear
    return wrapper
'''},
    tests=r'''
from memo import memoize

calls = []


@memoize
def f(a, b=0):
    calls.append((a, b))
    return a * 10 + b


assert f(1) == 10
assert f(1) == 10
assert calls == [(1, 0)]
assert (f.hits, f.misses) == (1, 1)
assert f(1, 2) == 12
assert f(1, b=2) == 12
assert calls == [(1, 0), (1, 2), (1, 2)]
assert (f.hits, f.misses) == (1, 3)
assert f(1, b=2) == 12
assert (f.hits, f.misses) == (2, 3)
assert f(2) == 20 and f(2) == 20
assert (f.hits, f.misses) == (3, 4)


@memoize
def g(**kw):
    calls.append(kw)
    return sum(kw.values())


calls.clear()
assert g(x=1, y=2) == 3
assert g(y=2, x=1) == 3
assert len(calls) == 1
assert g() == 0 and g() == 0
assert len(calls) == 2

boom = {"n": 0}


@memoize
def h(x):
    boom["n"] += 1
    if boom["n"] == 1:
        raise RuntimeError("first call fails")
    return x


try:
    h(5)
except RuntimeError:
    pass
else:
    raise AssertionError("expected RuntimeError")
assert (h.hits, h.misses) == (0, 0)
assert h(5) == 5
assert h(5) == 5
assert boom["n"] == 2 and (h.hits, h.misses) == (1, 1)
h.clear()
assert (h.hits, h.misses) == (0, 0)
assert h(5) == 5
assert boom["n"] == 3 and (h.hits, h.misses) == (0, 1)


@memoize
def none(x):
    calls.append("none")
    return None


calls.clear()
assert none(1) is None and none(1) is None
assert calls == ["none"]
assert none(1.0) is None
assert calls == ["none"]
assert none("1") is None
assert calls == ["none", "none"]
''',
    muts=[
        ("logic: kwargs ignored in key", "key = (args, tuple(sorted(kwargs.items())))", "key = (args,)"),
        ("logic: kwarg order matters", "tuple(sorted(kwargs.items()))", "tuple(kwargs.items())"),
        ("logic: args ignored in key", "key = (args, tuple(sorted(kwargs.items())))", "key = (tuple(sorted(kwargs.items())),)"),
        ("logic: exceptions cached", "        result = fn(*args, **kwargs)\n        wrapper.misses += 1\n        cache[key] = result", "        wrapper.misses += 1\n        try:\n            result = fn(*args, **kwargs)\n        except Exception:\n            result = None\n        cache[key] = result"),
        ("logic: hits not counted", "            wrapper.hits += 1\n", ""),
        ("logic: clear keeps counters", "        wrapper.hits = 0\n        wrapper.misses = 0\n\n    wrapper.hits", "        pass\n\n    wrapper.hits"),
        ("logic: clear keeps cache", "        cache.clear()\n", ""),
        ("logic: falsy results recomputed", "        if key in cache:\n            wrapper.hits += 1\n            return cache[key]", "        if cache.get(key):\n            wrapper.hits += 1\n            return cache[key]"),
    ],
    weak=14,
))

TASKS.append(dict(
    id="qa_env_parser", diff="medium",
    spec="Write tests for `parse_env(text)` in envfile.py.",
    files={"envfile.py": r'''
def parse_env(text):
    """Parse .env style text into a dict.
    - blank lines and lines starting with '#' are ignored;
    - an optional leading 'export ' is stripped;
    - KEY=VALUE where KEY matches [A-Za-z_][A-Za-z0-9_]* else ValueError; missing '=' -> ValueError;
    - values may be wrapped in matching single or double quotes (quotes removed, inner text kept verbatim);
    - unquoted values are stripped and an inline ' #' starts a comment that is removed;
    - later assignments override earlier ones."""
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep:
            raise ValueError("missing =: %r" % raw)
        if not key or not (key[0].isalpha() or key[0] == "_") or not all(c.isalnum() or c == "_" for c in key):
            raise ValueError("bad key: %r" % key)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            idx = value.find(" #")
            if idx >= 0:
                value = value[:idx].rstrip()
        out[key] = value
    return out
'''},
    tests=r'''
from envfile import parse_env

assert parse_env("") == {}
assert parse_env("A=1") == {"A": "1"}
assert parse_env("A=1\nB=2") == {"A": "1", "B": "2"}
assert parse_env("# comment\n\nA=1\n   # indented comment") == {"A": "1"}
assert parse_env("export A=1") == {"A": "1"}
assert parse_env("export   A=1") == {"A": "1"}
assert parse_env("A = 1") == {"A": "1"}
assert parse_env("A=") == {"A": ""}
assert parse_env('A="hello world"') == {"A": "hello world"}
assert parse_env("A='hello world'") == {"A": "hello world"}
assert parse_env('A="  spaced  "') == {"A": "  spaced  "}
assert parse_env('A="x # not comment"') == {"A": "x # not comment"}
assert parse_env("A=x # comment") == {"A": "x"}
assert parse_env("A=x#notcomment") == {"A": "x#notcomment"}
assert parse_env("A=1\nA=2") == {"A": "2"}
assert parse_env("URL=http://x/?a=b") == {"URL": "http://x/?a=b"}
assert parse_env("_priv=1\nK_2=3") == {"_priv": "1", "K_2": "3"}
assert parse_env('A="mismatch\'') == {"A": '"mismatch\''}
assert parse_env('A=""') == {"A": ""}
assert parse_env('A="') == {"A": '"'}
assert parse_env("A=1\r\nB=2\r\n") == {"A": "1", "B": "2"}
for bad in ("JUSTTEXT", "1A=2", "A-B=1", "=1", "A B=1", "export "):
    try:
        parse_env(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)
''',
    muts=[
        ("missing-edge-case: export prefix", '    if line.startswith("export "):\n            line = line[7:].lstrip()\n', "") if False else ("missing-edge-case: export prefix", '        if line.startswith("export "):\n            line = line[7:].lstrip()\n', ""),
        ("missing-edge-case: comments", '        if not line or line.startswith("#"):', "        if not line:"),
        ("logic: quotes kept", "            value = value[1:-1]", "            pass"),
        ("logic: mismatched quotes stripped", "value[0] == value[-1] and value[0] in", "value[0] in"),
        ("missing-edge-case: inline comment", "            if idx >= 0:\n                value = value[:idx].rstrip()\n", "            pass\n"),
        ("logic: inline comment without space", 'value.find(" #")', 'value.find("#")'),
        ("logic: first = split", 'key, sep, value = line.partition("=")', 'key, sep, value = line.rpartition("=")'),
        ("missing-edge-case: invalid key start", "not (key[0].isalpha() or key[0] == \"_\") or ", ""),
    ],
    weak=14,
))
