"""Write-from-spec tasks: the model sees the spec and a few examples, grading uses hidden tests."""

TASKS_WRITE = [
    dict(
        id="write_evaluate", kind="write",
        files={"solution.py": "def evaluate(expr):\n    raise NotImplementedError\n"},
        instruction=("Implement `evaluate(expr: str) -> float` in solution.py. Support + - * / with the usual precedence "
                     "and left associativity, parentheses, unary minus, decimals and spaces. Division by zero raises "
                     "ZeroDivisionError. Any other invalid input (empty string, dangling operator, unbalanced "
                     "parentheses, two numbers in a row, unknown characters) raises ValueError."),
        visible=r'''
from solution import evaluate
assert evaluate("2+3*4") == 14
assert evaluate("10-3-2") == 5
''',
        hidden=r'''
from solution import evaluate

assert evaluate("2+3*4") == 14
assert evaluate("10-3-2") == 5
assert evaluate("-(2+3)*2") == -10
assert evaluate("1.5*4") == 6
assert evaluate("10/4") == 2.5
assert evaluate("2*(3+4)-5") == 9
assert evaluate(" 7 - 2 - 1 ") == 4
assert evaluate("((2))") == 2
assert evaluate("8/4/2") == 1
assert evaluate("--3") == 3


def raises(exc, s):
    try:
        evaluate(s)
    except exc:
        return True
    except Exception:
        return False
    return False


assert raises(ValueError, "2+")
assert raises(ValueError, "")
assert raises(ZeroDivisionError, "1/0")
assert raises(ValueError, "2 3")
assert raises(ValueError, "(1+2")
assert raises(ValueError, "1+*2")
assert raises(ValueError, "2 $ 3")
''',
        reference={"solution.py": r'''
import re


def evaluate(expr):
    tokens = re.findall(r"\d+\.?\d*|\.\d+|[()+\-*/]|\S", expr)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def eat():
        nonlocal pos
        t = peek()
        if t is None:
            raise ValueError("unexpected end")
        pos += 1
        return t

    def parse_expr():
        v = parse_term()
        while peek() in ("+", "-"):
            op = eat()
            r = parse_term()
            v = v + r if op == "+" else v - r
        return v

    def parse_term():
        v = parse_factor()
        while peek() in ("*", "/"):
            op = eat()
            r = parse_factor()
            if op == "*":
                v = v * r
            else:
                if r == 0:
                    raise ZeroDivisionError
                v = v / r
        return v

    def parse_factor():
        t = eat()
        if t == "(":
            v = parse_expr()
            if eat() != ")":
                raise ValueError("expected )")
            return v
        if t == "-":
            return -parse_factor()
        if t == "+":
            return parse_factor()
        try:
            return float(t)
        except ValueError:
            raise ValueError("bad token " + t)

    v = parse_expr()
    if pos != len(tokens):
        raise ValueError("trailing input")
    return v
'''},
    ),
    dict(
        id="write_topo_sort", kind="write",
        files={"solution.py": "def topo_sort(graph):\n    raise NotImplementedError\n"},
        instruction=("Implement `topo_sort(graph)` in solution.py. `graph` maps each node to the list of nodes it depends on "
                     "(its prerequisites). Return a list of ALL nodes (including nodes that only appear as prerequisites) so that "
                     "every node comes after its prerequisites. Whenever several nodes are available, pick the alphabetically "
                     "smallest first, so the result is deterministic. Raise ValueError if the dependencies contain a cycle "
                     "(including a node depending on itself)."),
        visible=r'''
from solution import topo_sort
assert topo_sort({"b": ["a"], "a": []}) == ["a", "b"]
''',
        hidden=r'''
from solution import topo_sort

assert topo_sort({"b": ["a"], "a": []}) == ["a", "b"]
assert topo_sort({"app": ["lib", "util"], "lib": ["core"], "util": ["core"], "core": []}) == ["core", "lib", "util", "app"]
assert topo_sort({}) == []
assert topo_sort({"x": ["y"]}) == ["y", "x"]
assert topo_sort({"d": [], "c": [], "b": [], "a": []}) == ["a", "b", "c", "d"]
assert topo_sort({"c": ["a", "b"], "b": ["a"]}) == ["a", "b", "c"]
for bad in ({"a": ["b"], "b": ["c"], "c": ["a"]}, {"a": ["a"]}, {"a": [], "b": ["c"], "c": ["b"]}):
    try:
        topo_sort(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for " + repr(bad))
''',
        reference={"solution.py": r'''
import heapq


def topo_sort(graph):
    deps = {n: set(d) for n, d in graph.items()}
    for ds in list(deps.values()):
        for d in ds:
            deps.setdefault(d, set())
    dependents = {n: [] for n in deps}
    for n, ds in deps.items():
        for d in ds:
            dependents[d].append(n)
    indeg = {n: len(ds) for n, ds in deps.items()}
    heap = [n for n, k in indeg.items() if k == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        n = heapq.heappop(heap)
        out.append(n)
        for m in dependents[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                heapq.heappush(heap, m)
    if len(out) != len(deps):
        raise ValueError("cycle")
    return out
'''},
    ),
    dict(
        id="write_lru_cache", kind="write",
        files={"solution.py": "class LRUCache:\n    pass\n"},
        instruction=("Implement class `LRUCache(capacity)` in solution.py with: `get(key)` (returns the value or None; a hit makes "
                     "the key most recently used), `put(key, value)` (inserts or updates, makes the key most recently used, and "
                     "evicts the least recently used key when the size exceeds capacity), `__len__`, `__contains__` (does NOT "
                     "change recency) and `keys()` returning the keys from least to most recently used. A capacity below 1 "
                     "raises ValueError."),
        visible=r'''
from solution import LRUCache
c = LRUCache(1)
c.put("a", 1)
assert c.get("a") == 1
''',
        hidden=r'''
from solution import LRUCache

c = LRUCache(2)
c.put("a", 1)
c.put("b", 2)
assert c.keys() == ["a", "b"]
assert c.get("a") == 1
assert c.keys() == ["b", "a"]
c.put("c", 3)
assert "b" not in c and "a" in c and "c" in c
assert len(c) == 2
assert c.get("missing") is None
assert c.keys() == ["a", "c"]
assert "a" in c
assert c.keys() == ["a", "c"]
c.put("a", 99)
assert c.keys() == ["c", "a"] and c.get("a") == 99
for bad in (0, -1):
    try:
        LRUCache(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
c1 = LRUCache(1)
c1.put("x", 1)
c1.put("y", 2)
assert c1.keys() == ["y"] and c1.get("x") is None
''',
        reference={"solution.py": r'''
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._d = OrderedDict()

    def get(self, key):
        if key in self._d:
            self._d.move_to_end(key)
            return self._d[key]
        return None

    def put(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) > self.capacity:
            self._d.popitem(last=False)

    def __len__(self):
        return len(self._d)

    def __contains__(self, key):
        return key in self._d

    def keys(self):
        return list(self._d.keys())
'''},
    ),
    dict(
        id="write_dijkstra", kind="write",
        files={"solution.py": "def dijkstra(graph, start):\n    raise NotImplementedError\n"},
        instruction=("Implement `dijkstra(graph, start)` in solution.py. `graph` maps each node to a list of (neighbor, weight) "
                     "pairs. Return a dict with the shortest distance from `start` to every node reachable from it (including "
                     "`start` itself with distance 0); unreachable nodes are left out. Raise ValueError if ANY edge in the graph "
                     "has a negative weight. Nodes that appear only as neighbors may be missing from the graph keys."),
        visible=r'''
from solution import dijkstra
assert dijkstra({"a": [("b", 1)], "b": []}, "a") == {"a": 0, "b": 1}
''',
        hidden=r'''
from solution import dijkstra

g = {
    "a": [("b", 7), ("c", 9), ("f", 14)],
    "b": [("a", 7), ("c", 10), ("d", 15)],
    "c": [("a", 9), ("b", 10), ("d", 11), ("f", 2)],
    "d": [("b", 15), ("c", 11), ("e", 6)],
    "e": [("d", 6), ("f", 9)],
    "f": [("a", 14), ("c", 2), ("e", 9)],
}
assert dijkstra(g, "a") == {"a": 0, "b": 7, "c": 9, "d": 20, "e": 20, "f": 11}
assert dijkstra({"a": [("b", 1)], "b": [], "z": []}, "a") == {"a": 0, "b": 1}
assert dijkstra({"a": []}, "a") == {"a": 0}
assert dijkstra({"a": [("b", 2)]}, "a") == {"a": 0, "b": 2}
assert dijkstra({"a": [("b", 5), ("c", 1)], "c": [("b", 1)]}, "a") == {"a": 0, "b": 2, "c": 1}
assert dijkstra({"a": [("a", 3), ("b", 0)], "b": []}, "a") == {"a": 0, "b": 0}
try:
    dijkstra({"a": [("b", -1)], "b": []}, "a")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
try:
    dijkstra({"a": [("b", 1)], "x": [("y", -2)]}, "a")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError for unreachable negative edge")
''',
        reference={"solution.py": r'''
import heapq


def dijkstra(graph, start):
    for edges in graph.values():
        for _, w in edges:
            if w < 0:
                raise ValueError("negative weight")
    dist = {}
    heap = [(0, start)]
    while heap:
        d, n = heapq.heappop(heap)
        if n in dist:
            continue
        dist[n] = d
        for m, w in graph.get(n, ()):
            if m not in dist:
                heapq.heappush(heap, (d + w, m))
    return dist
'''},
    ),
    dict(
        id="write_parse_duration", kind="write",
        files={"solution.py": "def parse_duration(s):\n    raise NotImplementedError\n"},
        instruction=("Implement `parse_duration(s: str) -> int` in solution.py returning the total number of seconds. The string "
                     "is one or more parts, each a whole number followed by a unit: d (day), h (hour), m (minute), s (second), "
                     "in any order, optionally separated by spaces, case-insensitive: '1h30m', '2d 4h', '45s', '1H 1M 1S'. "
                     "Raise ValueError for: an empty or blank string, a number without a unit ('10', '1h 30'), an unknown unit "
                     "('5x'), a unit used twice ('1h2h'), a unit without a number ('h'), or a negative number ('-5s')."),
        visible=r'''
from solution import parse_duration
assert parse_duration("1h30m") == 5400
''',
        hidden=r'''
from solution import parse_duration

assert parse_duration("1h30m") == 5400
assert parse_duration("2d 4h") == 2 * 86400 + 4 * 3600
assert parse_duration("45s") == 45
assert parse_duration("1H 1M 1S") == 3661
assert parse_duration("90m") == 5400
assert parse_duration("0s") == 0
assert parse_duration("  3m  ") == 180
assert parse_duration("30s 1m") == 90
for bad in ("", "   ", "10", "5x", "1h2h", "h", "1h 30", "-5s", "1h-5s"):
    try:
        parse_duration(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for " + repr(bad))
''',
        reference={"solution.py": r'''
import re

_PART = re.compile(r"\s*(\d+)([a-z])")


def parse_duration(s):
    s = s.strip().lower()
    if not s:
        raise ValueError("empty")
    mult = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total, seen, pos = 0, set(), 0
    while pos < len(s):
        m = _PART.match(s, pos)
        if not m:
            raise ValueError("bad duration")
        n, u = m.groups()
        if u not in mult or u in seen:
            raise ValueError("bad unit")
        seen.add(u)
        total += int(n) * mult[u]
        pos = m.end()
    return total
'''},
    ),
    dict(
        id="write_sliding_window", kind="write",
        files={"solution.py": "class SlidingWindowLimiter:\n    pass\n"},
        instruction=("Implement class `SlidingWindowLimiter(max_calls, period)` in solution.py with `allow(now) -> bool`. "
                     "`allow` returns True when fewer than `max_calls` calls were ALLOWED in the half-open window "
                     "(now - period, now], and then records the call; rejected calls are not recorded. `now` values never "
                     "decrease. max_calls < 1 or period <= 0 raises ValueError."),
        visible=r'''
from solution import SlidingWindowLimiter
l = SlidingWindowLimiter(1, 5)
assert l.allow(0) is True and l.allow(1) is False
''',
        hidden=r'''
from solution import SlidingWindowLimiter

l = SlidingWindowLimiter(2, 10)
assert l.allow(0) is True
assert l.allow(1) is True
assert l.allow(2) is False
assert l.allow(9.9) is False
assert l.allow(10) is True
assert l.allow(10.5) is False
assert l.allow(11) is True
assert l.allow(11) is False
for args in ((0, 5), (2, 0), (2, -1)):
    try:
        SlidingWindowLimiter(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
l2 = SlidingWindowLimiter(1, 3)
assert l2.allow(0) and not l2.allow(2.99) and l2.allow(3)
''',
        reference={"solution.py": r'''
from collections import deque


class SlidingWindowLimiter:
    def __init__(self, max_calls, period):
        if max_calls < 1 or period <= 0:
            raise ValueError("bad limits")
        self.max_calls = max_calls
        self.period = period
        self._q = deque()

    def allow(self, now):
        while self._q and self._q[0] <= now - self.period:
            self._q.popleft()
        if len(self._q) < self.max_calls:
            self._q.append(now)
            return True
        return False
'''},
    ),
    dict(
        id="write_trie", kind="write",
        files={"solution.py": "class Trie:\n    pass\n"},
        instruction=("Implement class `Trie` in solution.py with `insert(word)`, `search(word)` (exact match only), "
                     "`starts_with(prefix)` (True if any inserted word starts with the prefix; the empty prefix is True only "
                     "if at least one word was inserted) and `words_with_prefix(prefix)` returning a sorted list of all inserted "
                     "words that start with the prefix, including the prefix itself if it was inserted. The empty prefix "
                     "returns all words. Inserting the same word twice must not duplicate it."),
        visible=r'''
from solution import Trie
t = Trie()
t.insert("car")
assert t.search("car") and not t.search("ca")
''',
        hidden=r'''
from solution import Trie

t = Trie()
assert t.starts_with("") is False
assert t.words_with_prefix("") == []
for w in ("car", "card", "care", "cat", "dog", "car"):
    t.insert(w)
assert t.search("car") and t.search("dog")
assert not t.search("ca") and not t.search("cars") and not t.search("")
assert t.starts_with("ca") and t.starts_with("") and not t.starts_with("cb")
assert t.words_with_prefix("car") == ["car", "card", "care"]
assert t.words_with_prefix("ca") == ["car", "card", "care", "cat"]
assert t.words_with_prefix("") == ["car", "card", "care", "cat", "dog"]
assert t.words_with_prefix("x") == []
assert t.words_with_prefix("dogs") == []
''',
        reference={"solution.py": r'''
class Trie:
    def __init__(self):
        self._root = {}

    def insert(self, word):
        node = self._root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True

    def _find(self, prefix):
        node = self._root
        for ch in prefix:
            if ch not in node:
                return None
            node = node[ch]
        return node

    def search(self, word):
        node = self._find(word)
        return bool(node and node.get("$"))

    def starts_with(self, prefix):
        node = self._find(prefix)
        return node is not None and bool(node)

    def words_with_prefix(self, prefix):
        node = self._find(prefix)
        if node is None:
            return []
        out = []

        def walk(n, acc):
            if n.get("$"):
                out.append("".join(acc))
            for ch, child in n.items():
                if ch != "$":
                    acc.append(ch)
                    walk(child, acc)
                    acc.pop()

        walk(node, list(prefix))
        return sorted(out)
'''},
    ),
    dict(
        id="write_get_path", kind="write",
        files={"solution.py": "def get_path(obj, path, default=None):\n    raise NotImplementedError\n"},
        instruction=("Implement `get_path(obj, path, default=None)` in solution.py. It reads a value from nested dicts and lists. "
                     "Path syntax: dict keys separated by dots, list indexes in brackets, e.g. 'a.b[2].c', '[0].x', 'items[1][0]'. "
                     "Negative indexes count from the end. A missing key, an out-of-range index, or a step that does not fit the "
                     "current type (a key on a list, an index on a dict) returns `default`. If the path exists and the stored "
                     "value is None, return None (not the default). An empty path returns `obj` itself."),
        visible=r'''
from solution import get_path
assert get_path({"a": {"b": [10, 20]}}, "a.b[1]") == 20
''',
        hidden=r'''
from solution import get_path

data = {"a": {"b": [{"c": 1}, {"c": 2}, {"c": 3}]}, "x": [[10, 20], [30]], "n": None}
assert get_path(data, "a.b[2].c") == 3
assert get_path(data, "x[0][1]") == 20
assert get_path(data, "a.z", default="d") == "d"
assert get_path(data, "a.b[5].c") is None
assert get_path(data, "") is data
assert get_path([{"q": 1}], "[0].q") == 1
assert get_path(data, "a.b.c", default=7) == 7
assert get_path(data, "x[-1][0]") == 30
assert get_path(data, "n", default=1) is None
assert get_path(data, "x.y", default="k") == "k"
assert get_path(data, "a[0]", default="k") == "k"
assert get_path(data, "x[2]", default="k") == "k"
''',
        reference={"solution.py": r'''
import re

_TOKEN = re.compile(r"\[(-?\d+)\]|([^.\[\]]+)")


def get_path(obj, path, default=None):
    cur = obj
    for m in _TOKEN.finditer(path):
        idx, key = m.groups()
        if idx is not None:
            if not isinstance(cur, list):
                return default
            i = int(idx)
            if not -len(cur) <= i < len(cur):
                return default
            cur = cur[i]
        else:
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
    return cur
'''},
    ),
]
