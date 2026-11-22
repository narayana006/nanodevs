"""Write-from-spec tasks, part 2 (data structures, graphs, DP, parsers, multi-file)."""
from common import task


def W(id, diff, topic, stub, instruction, visible, hidden, ref, files=None, name="solution.py"):
    files = files or {name: stub}
    return task(id, "write", diff, topic, files, instruction, visible, hidden, ref if isinstance(ref, dict) else {name: ref})


TASKS_WRITE2 = [
    W("py_write_min_stack", "medium", "data-structures",
      "class MinStack:\n    pass\n",
      "Implement class `MinStack` with `push(x)`, `pop()`, `top()`, `min()` (all O(1)) and `__len__`. pop/top/min on an empty stack raise IndexError.",
      "from solution import MinStack\ns = MinStack(); s.push(2); s.push(1)\nassert s.min() == 1\n",
      r'''
from solution import MinStack
s = MinStack()
for x in (5, 3, 7, 3, 1):
    s.push(x)
assert len(s) == 5 and s.min() == 1 and s.top() == 1
assert s.pop() == 1 and s.min() == 3
assert s.pop() == 3 and s.min() == 3
assert s.pop() == 7 and s.min() == 3 and s.top() == 3
assert s.pop() == 3 and s.min() == 5
assert s.pop() == 5 and len(s) == 0
for f in (s.pop, s.top, s.min):
    try:
        f()
        assert False
    except IndexError:
        pass
''',
      "class MinStack:\n    def __init__(self):\n        self.a = []\n        self.m = []\n\n    def push(self, x):\n        self.a.append(x)\n        self.m.append(x if not self.m else min(x, self.m[-1]))\n\n    def pop(self):\n        if not self.a:\n            raise IndexError('empty')\n        self.m.pop()\n        return self.a.pop()\n\n    def top(self):\n        if not self.a:\n            raise IndexError('empty')\n        return self.a[-1]\n\n    def min(self):\n        if not self.a:\n            raise IndexError('empty')\n        return self.m[-1]\n\n    def __len__(self):\n        return len(self.a)\n"),
    W("py_write_queue_two_stacks", "medium", "data-structures", "class Queue:\n    pass\n",
      "Implement class `Queue` using only two Python lists as stacks (append/pop from the end only; never pop(0) or use deque): "
      "`enqueue(x)`, `dequeue()`, `peek()`, `__len__`. dequeue/peek on an empty queue raise IndexError. Operations must be amortised O(1) "
      "(100000 operations must finish quickly).",
      "from solution import Queue\nq = Queue(); q.enqueue(1); q.enqueue(2)\nassert q.dequeue() == 1\n",
      r'''
from solution import Queue
q = Queue()
for i in range(5):
    q.enqueue(i)
assert q.peek() == 0 and len(q) == 5
assert q.dequeue() == 0 and q.dequeue() == 1
q.enqueue(9)
assert [q.dequeue() for _ in range(4)] == [2, 3, 4, 9]
assert len(q) == 0
for f in (q.dequeue, q.peek):
    try:
        f()
        assert False
    except IndexError:
        pass
for i in range(100000):
    q.enqueue(i)
assert all(q.dequeue() == i for i in range(100000))
''',
      "class Queue:\n    def __init__(self):\n        self.inp = []\n        self.out = []\n\n    def enqueue(self, x):\n        self.inp.append(x)\n\n    def _shift(self):\n        if not self.out:\n            while self.inp:\n                self.out.append(self.inp.pop())\n        if not self.out:\n            raise IndexError('empty')\n\n    def dequeue(self):\n        self._shift()\n        return self.out.pop()\n\n    def peek(self):\n        self._shift()\n        return self.out[-1]\n\n    def __len__(self):\n        return len(self.inp) + len(self.out)\n"),
    W("py_write_ring_buffer", "medium", "data-structures", "class RingBuffer:\n    pass\n",
      "Implement `RingBuffer(capacity)`: `append(x)` adds an item and, when full, silently overwrites the oldest; `to_list()` returns items oldest first; "
      "`__len__`; `is_full()`; `pop_oldest()` removes and returns the oldest (IndexError if empty). capacity < 1 raises ValueError.",
      "from solution import RingBuffer\nr = RingBuffer(2); r.append(1); r.append(2); r.append(3)\nassert r.to_list() == [2, 3]\n",
      r'''
from solution import RingBuffer
r = RingBuffer(3)
assert len(r) == 0 and r.to_list() == [] and not r.is_full()
for i in range(1, 5):
    r.append(i)
assert r.to_list() == [2, 3, 4] and r.is_full() and len(r) == 3
assert r.pop_oldest() == 2
assert r.to_list() == [3, 4] and not r.is_full()
r.append(5); r.append(6)
assert r.to_list() == [4, 5, 6]
for _ in range(3):
    r.pop_oldest()
try:
    r.pop_oldest()
    assert False
except IndexError:
    pass
r.append(1)
assert r.to_list() == [1]
try:
    RingBuffer(0)
    assert False
except ValueError:
    pass
''',
      "class RingBuffer:\n    def __init__(self, capacity):\n        if capacity < 1:\n            raise ValueError('capacity')\n        self.cap = capacity\n        self.buf = [None] * capacity\n        self.start = 0\n        self.n = 0\n\n    def append(self, x):\n        if self.n < self.cap:\n            self.buf[(self.start + self.n) % self.cap] = x\n            self.n += 1\n        else:\n            self.buf[self.start] = x\n            self.start = (self.start + 1) % self.cap\n\n    def to_list(self):\n        return [self.buf[(self.start + i) % self.cap] for i in range(self.n)]\n\n    def __len__(self):\n        return self.n\n\n    def is_full(self):\n        return self.n == self.cap\n\n    def pop_oldest(self):\n        if not self.n:\n            raise IndexError('empty')\n        x = self.buf[self.start]\n        self.buf[self.start] = None\n        self.start = (self.start + 1) % self.cap\n        self.n -= 1\n        return x\n"),
    W("py_write_unique_paths", "medium", "dp", "def count_paths(grid):\n    raise NotImplementedError\n",
      "Implement `count_paths(grid)`: grid is a list of lists of 0 (free) and 1 (blocked). Count the paths from top-left to bottom-right moving only "
      "right or down through free cells. If the start or end is blocked, or the grid is empty, the answer is 0.",
      "from solution import count_paths\nassert count_paths([[0, 0], [0, 0]]) == 2\n",
      "from solution import count_paths\nassert count_paths([[0, 0], [0, 0]]) == 2\nassert count_paths([[0, 0, 0], [0, 1, 0], [0, 0, 0]]) == 2\nassert count_paths([[1]]) == 0\nassert count_paths([[0]]) == 1\nassert count_paths([[0, 1]]) == 0\nassert count_paths([]) == 0\nassert count_paths([[0] * 12 for _ in range(12)]) == 705432\nassert count_paths([[0, 0], [1, 1]]) == 0\n",
      "def count_paths(grid):\n    if not grid or not grid[0] or grid[0][0] or grid[-1][-1]:\n        return 0\n    R, C = len(grid), len(grid[0])\n    dp = [[0] * C for _ in range(R)]\n    dp[0][0] = 1\n    for r in range(R):\n        for c in range(C):\n            if grid[r][c]:\n                dp[r][c] = 0\n            elif r or c:\n                dp[r][c] = (dp[r - 1][c] if r else 0) + (dp[r][c - 1] if c else 0)\n    return dp[-1][-1]\n"),
    W("py_write_can_partition", "medium", "dp", "def can_partition(nums):\n    raise NotImplementedError\n",
      "Implement `can_partition(nums)` for a list of positive ints: True iff the list can be split into two groups with equal sums (empty list: True).",
      "from solution import can_partition\nassert can_partition([1, 5, 11, 5])\n",
      "from solution import can_partition\nassert can_partition([1, 5, 11, 5])\nassert not can_partition([1, 2, 3, 5])\nassert can_partition([])\nassert not can_partition([1])\nassert can_partition([3, 3])\nassert not can_partition([1, 2, 5])\nassert not can_partition([2] * 99 + [1])\nassert can_partition([7] * 40)\n",
      "def can_partition(nums):\n    t = sum(nums)\n    if t % 2:\n        return False\n    t //= 2\n    reach = {0}\n    for n in nums:\n        reach |= {x + n for x in reach if x + n <= t}\n    return t in reach\n"),
    W("py_write_rpn_convert", "medium", "parsing", "def to_rpn(tokens):\n    raise NotImplementedError\n",
      "Implement `to_rpn(tokens)`: convert an infix token list (e.g. ['3','+','4','*','2']) to a reverse Polish token list using the shunting-yard method. "
      "Operators: + - * / (left-associative; * and / bind tighter) and ^ (right-associative, tightest), plus parentheses '(' ')'. Any other token is an "
      "operand and passes through. Mismatched parentheses raise ValueError.",
      "from solution import to_rpn\nassert to_rpn(['3', '+', '4', '*', '2']) == ['3', '4', '2', '*', '+']\n",
      r'''
from solution import to_rpn
assert to_rpn(["3", "+", "4", "*", "2"]) == ["3", "4", "2", "*", "+"]
assert to_rpn(["(", "3", "+", "4", ")", "*", "2"]) == ["3", "4", "+", "2", "*"]
assert to_rpn(["2", "^", "3", "^", "2"]) == ["2", "3", "2", "^", "^"]
assert to_rpn(["8", "-", "3", "-", "2"]) == ["8", "3", "-", "2", "-"]
assert to_rpn(["a", "*", "b", "^", "c", "+", "d"]) == ["a", "b", "c", "^", "*", "d", "+"]
assert to_rpn([]) == []
assert to_rpn(["x"]) == ["x"]
assert to_rpn(["1", "-", "(", "2", "-", "3", ")"]) == ["1", "2", "3", "-", "-"]
assert to_rpn(["6", "/", "3", "*", "2"]) == ["6", "3", "/", "2", "*"]
for bad in (["(", "1"], ["1", ")"], [")", "(" ]):
    try:
        to_rpn(bad)
        assert False, bad
    except ValueError:
        pass
''',
      "PREC = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}\n\n\ndef to_rpn(tokens):\n    out, st = [], []\n    for t in tokens:\n        if t in PREC:\n            while st and st[-1] in PREC and (PREC[st[-1]] > PREC[t] or (PREC[st[-1]] == PREC[t] and t != '^')):\n                out.append(st.pop())\n            st.append(t)\n        elif t == '(':\n            st.append(t)\n        elif t == ')':\n            while st and st[-1] != '(':\n                out.append(st.pop())\n            if not st:\n                raise ValueError('mismatched')\n            st.pop()\n        else:\n            out.append(t)\n    while st:\n        if st[-1] == '(':\n            raise ValueError('mismatched')\n        out.append(st.pop())\n    return out\n"),
    W("py_write_ttl_cache", "medium", "caching",
      "class TTLCache:\n    pass\n",
      "Implement `TTLCache(ttl, clock)` in solution.py. `clock` has a `now()` method (see clock.py). `set(key, value, ttl=None)` stores a value that expires "
      "when `clock.now() >= set_time + ttl` (per-entry `ttl` overrides the default). `get(key, default=None)` returns the value or default if missing/expired "
      "(expired entries are removed). `__len__` counts only live entries. `purge()` removes all expired entries and returns how many were removed. "
      "Setting an existing key restarts its expiry.",
      "from clock import FakeClock\nfrom solution import TTLCache\nc = FakeClock(); t = TTLCache(10, c); t.set('a', 1)\nassert t.get('a') == 1\n",
      r'''
from clock import FakeClock
from solution import TTLCache
c = FakeClock(100)
t = TTLCache(10, c)
t.set("a", 1)
t.set("b", 2, ttl=5)
assert t.get("a") == 1 and t.get("b") == 2 and len(t) == 2
c.advance(4.9)
assert t.get("b") == 2
c.advance(0.1)
assert t.get("b") is None and t.get("b", "gone") == "gone"
assert len(t) == 1
c.advance(4.9)
assert t.get("a") == 1
t.set("a", 11)
c.advance(9.9)
assert t.get("a") == 11
c.advance(0.1)
assert t.get("a") is None
t.set("x", 1); t.set("y", 2, ttl=1); t.set("z", 3)
c.advance(1)
assert t.purge() == 1
assert len(t) == 2
assert t.purge() == 0
assert t.get("x") == 1
''',
      "class TTLCache:\n    def __init__(self, ttl, clock):\n        self.ttl = ttl\n        self.clock = clock\n        self.d = {}\n\n    def set(self, key, value, ttl=None):\n        self.d[key] = (value, self.clock.now() + (self.ttl if ttl is None else ttl))\n\n    def _live(self, key):\n        e = self.d.get(key)\n        if e is None:\n            return None\n        if self.clock.now() >= e[1]:\n            del self.d[key]\n            return None\n        return e\n\n    def get(self, key, default=None):\n        e = self._live(key)\n        return default if e is None else e[0]\n\n    def __len__(self):\n        return sum(1 for k in list(self.d) if self._live(k) is not None)\n\n    def purge(self):\n        n = len(self.d)\n        for k in list(self.d):\n            self._live(k)\n        return n - len(self.d)\n",
      files={"clock.py": "class FakeClock:\n    def __init__(self, start=0.0):\n        self.t = start\n\n    def now(self):\n        return self.t\n\n    def advance(self, dt):\n        self.t += dt\n",
             "solution.py": "class TTLCache:\n    pass\n"}),
    W("py_write_inventory_report", "easy", "multi-file",
      "def report(items, low=5):\n    raise NotImplementedError\n",
      "Implement `report(items, low=5)` in solution.py. `items` is a list of `models.Item`. Return a dict with: `total_value` (sum of qty*unit_cost, rounded to 2), "
      "`by_category` (dict category -> {'units': total qty, 'value': rounded 2}; keys in alphabetical order) and `low_stock` (sorted list of skus with qty < low).",
      "from models import Item\nfrom solution import report\nr = report([Item('a', 'A', 2, 1.5, 'x')])\nassert r['total_value'] == 3.0\n",
      r'''
from models import Item
from solution import report
items = [Item("s1", "Pen", 10, 1.25, "office"), Item("s2", "Mug", 3, 4.0, "kitchen"), Item("s3", "Ink", 4, 7.5, "office"), Item("s4", "Pan", 5, 20.0, "kitchen")]
r = report(items)
assert r["total_value"] == 154.5
assert list(r["by_category"]) == ["kitchen", "office"]
assert r["by_category"]["kitchen"] == {"units": 8, "value": 112.0}
assert r["by_category"]["office"] == {"units": 14, "value": 42.5}
assert r["low_stock"] == ["s2", "s3"]
assert report(items, low=3)["low_stock"] == []
assert report(items, low=100)["low_stock"] == ["s1", "s2", "s3", "s4"]
assert report([]) == {"total_value": 0, "by_category": {}, "low_stock": []}
assert report([Item("q", "Q", 3, 0.1, "c")])["total_value"] == 0.3
''',
      "def report(items, low=5):\n    cats = {}\n    total = 0.0\n    for it in items:\n        c = cats.setdefault(it.category, [0, 0.0])\n        c[0] += it.qty\n        c[1] += it.qty * it.unit_cost\n        total += it.qty * it.unit_cost\n    return {'total_value': round(total, 2),\n            'by_category': {k: {'units': v[0], 'value': round(v[1], 2)} for k, v in sorted(cats.items())},\n            'low_stock': sorted(it.sku for it in items if it.qty < low)}\n",
      files={"models.py": "from dataclasses import dataclass\n\n\n@dataclass\nclass Item:\n    sku: str\n    name: str\n    qty: int\n    unit_cost: float\n    category: str\n",
             "solution.py": "from models import Item\n\n\ndef report(items, low=5):\n    raise NotImplementedError\n"}),
    W("py_write_graph_paths", "medium", "graphs", "def all_paths(graph, src, dst):\n    raise NotImplementedError\n",
      "Implement `all_paths(graph, src, dst)` in paths.py using the `Graph` class from graph.py (directed edges, `neighbors(u)` is sorted). Return every simple "
      "path (no repeated node) from src to dst as a list of node lists, ordered lexicographically by node sequence. If src == dst return [[src]]. Unknown "
      "nodes give [].",
      "from graph import Graph\nfrom paths import all_paths\ng = Graph(); g.add_edge('a', 'b')\nassert all_paths(g, 'a', 'b') == [['a', 'b']]\n",
      r'''
from graph import Graph
from paths import all_paths
g = Graph()
for u, v in [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d"), ("b", "c"), ("d", "a"), ("c", "b")]:
    g.add_edge(u, v)
assert all_paths(g, "a", "d") == [["a", "b", "c", "d"], ["a", "b", "d"], ["a", "c", "b", "d"], ["a", "c", "d"]]
assert all_paths(g, "a", "a") == [["a"]]
assert all_paths(g, "a", "zz") == []
assert all_paths(g, "zz", "a") == []
h = Graph()
h.add_edge(1, 2); h.add_edge(3, 4)
assert all_paths(h, 1, 4) == []
assert all_paths(h, 1, 2) == [[1, 2]]
''',
      "def all_paths(graph, src, dst):\n    nodes = set(graph.nodes())\n    if src not in nodes or dst not in nodes:\n        return []\n    out = []\n\n    def go(path):\n        u = path[-1]\n        if u == dst:\n            out.append(list(path))\n            return\n        for v in graph.neighbors(u):\n            if v not in path:\n                path.append(v)\n                go(path)\n                path.pop()\n    go([src])\n    return out\n",
      files={"graph.py": "class Graph:\n    def __init__(self):\n        self._adj = {}\n\n    def add_edge(self, u, v):\n        self._adj.setdefault(u, set()).add(v)\n        self._adj.setdefault(v, set())\n\n    def nodes(self):\n        return sorted(self._adj)\n\n    def neighbors(self, u):\n        return sorted(self._adj.get(u, ()))\n",
             "paths.py": "from graph import Graph\n\n\ndef all_paths(graph, src, dst):\n    raise NotImplementedError\n"}, name="paths.py"),
    W("py_write_csv_summary", "medium", "multi-file", "def summarize(text, group_col, value_col):\n    raise NotImplementedError\n",
      "Implement `summarize(text, group_col, value_col)` in report.py using `read_rows(text)` from csvlite.py (a list of dicts keyed by header). Group rows by "
      "`group_col`; for each group compute count, total and mean of `value_col` (float). Rows whose value is not a valid number are skipped and counted. "
      "Return `{'groups': [(group, count, total, mean), ...], 'skipped': n}` with groups sorted by total descending then group name; total and mean rounded "
      "to 2. Unknown column names raise KeyError.",
      "from report import summarize\nr = summarize('k,v\\na,1\\na,3', 'k', 'v')\nassert r['groups'] == [('a', 2, 4.0, 2.0)]\n",
      r'''
from report import summarize
text = "city,sales,note\nA,10,x\nB,5.5,y\nA,2.5,z\nC,oops,q\nB,4.5,r\nD,,s\n"
r = summarize(text, "city", "sales")
assert r["groups"] == [("A", 2, 12.5, 6.25), ("B", 2, 10.0, 5.0)], r
assert r["skipped"] == 2
t2 = "g,v\nx,1\ny,1\nz,2\n"
assert summarize(t2, "g", "v")["groups"] == [("z", 1, 2.0, 2.0), ("x", 1, 1.0, 1.0), ("y", 1, 1.0, 1.0)]
assert summarize("g,v\n", "g", "v") == {"groups": [], "skipped": 0}
for gc, vc in [("nope", "v"), ("g", "nope")]:
    try:
        summarize(t2, gc, vc)
        assert False
    except KeyError:
        pass
assert summarize("g,v\na,1\na,2\na,2\n", "g", "v")["groups"] == [("a", 3, 5.0, 1.67)]
''',
      "from csvlite import read_rows\n\n\ndef summarize(text, group_col, value_col):\n    rows = read_rows(text)\n    if rows and (group_col not in rows[0] or value_col not in rows[0]):\n        raise KeyError(group_col if group_col not in rows[0] else value_col)\n    g = {}\n    skipped = 0\n    for r in rows:\n        try:\n            v = float(r[value_col])\n        except ValueError:\n            skipped += 1\n            continue\n        e = g.setdefault(r[group_col], [0, 0.0])\n        e[0] += 1\n        e[1] += v\n    res = [(k, c, round(t, 2), round(t / c, 2)) for k, (c, t) in g.items()]\n    res.sort(key=lambda x: (-x[2], x[0]))\n    return {'groups': res, 'skipped': skipped}\n",
      files={"csvlite.py": "def read_rows(text):\n    lines = [l for l in text.splitlines() if l.strip()]\n    if not lines:\n        return []\n    head = lines[0].split(',')\n    return [dict(zip(head, l.split(','))) for l in lines[1:]]\n",
             "report.py": "from csvlite import read_rows\n\n\ndef summarize(text, group_col, value_col):\n    raise NotImplementedError\n"}, name="report.py"),
    W("py_write_validator", "easy", "multi-file", "def validate(schema, data):\n    raise NotImplementedError\n",
      "Implement `validate(schema, data)` in solution.py using the rule classes from rules.py. `schema` maps field -> list of rules; `data` is a dict. "
      "Return a dict field -> list of error messages (in rule order) containing only the fields that have errors. A missing field is treated as None; "
      "rules other than Required are skipped for None values. Fields in data but not in the schema get the error list ['unknown field'].",
      "from rules import Required\nfrom solution import validate\nassert validate({'a': [Required()]}, {}) == {'a': ['required']}\n",
      r'''
from rules import Required, MinLen, Range
from solution import validate
schema = {"name": [Required(), MinLen(3)], "age": [Range(0, 120)], "tag": [MinLen(2)]}
assert validate(schema, {"name": "Bob", "age": 30}) == {}
assert validate(schema, {}) == {"name": ["required"]}
assert validate(schema, {"name": "Al", "age": 200, "tag": "x"}) == {"name": ["too short"], "age": ["out of range"], "tag": ["too short"]}
assert validate(schema, {"name": "Bobby", "extra": 1}) == {"extra": ["unknown field"]}
assert validate({"x": [Required(), MinLen(5)]}, {"x": None}) == {"x": ["required"]}
assert validate({}, {}) == {}
''',
      "def validate(schema, data):\n    errors = {}\n    for field, rules in schema.items():\n        v = data.get(field)\n        msgs = []\n        for r in rules:\n            if v is None and not r.applies_to_none:\n                continue\n            m = r.check(v)\n            if m:\n                msgs.append(m)\n        if msgs:\n            errors[field] = msgs\n    for field in data:\n        if field not in schema:\n            errors[field] = ['unknown field']\n    return errors\n",
      files={"rules.py": "class Rule:\n    applies_to_none = False\n\n    def check(self, value):\n        \"\"\"Return an error message, or None when the value is fine.\"\"\"\n        raise NotImplementedError\n\n\nclass Required(Rule):\n    applies_to_none = True\n\n    def check(self, value):\n        return 'required' if value is None else None\n\n\nclass MinLen(Rule):\n    def __init__(self, n):\n        self.n = n\n\n    def check(self, value):\n        return 'too short' if len(value) < self.n else None\n\n\nclass Range(Rule):\n    def __init__(self, lo, hi):\n        self.lo, self.hi = lo, hi\n\n    def check(self, value):\n        return None if self.lo <= value <= self.hi else 'out of range'\n",
             "solution.py": "from rules import Required, MinLen, Range\n\n\ndef validate(schema, data):\n    raise NotImplementedError\n"}),
    W("py_write_task_planner", "hard", "graphs", "def plan(tasks):\n    raise NotImplementedError\n",
      "Implement `plan(tasks)` in planner.py. `tasks` is a list of `task.Task(name, duration, deps)`. Schedule with unlimited parallelism: each task starts as soon as "
      "all deps finish (start 0 with no deps). Return `(schedule, critical_path)`: `schedule` maps name -> (start, finish); `critical_path` is the list of task "
      "names forming a longest chain: begin at the task with the greatest finish (ties: smallest name), then repeatedly step to the dependency whose finish "
      "equals the current task's start (ties: smallest name) until a task without deps; return it in execution order. Empty input gives ({}, []). "
      "Raise ValueError for an unknown dependency or a cycle.",
      "from task import Task\nfrom planner import plan\ns, cp = plan([Task('a', 2, [])])\nassert s == {'a': (0, 2)} and cp == ['a']\n",
      r'''
from task import Task
from planner import plan
ts = [Task("build", 4, ["fetch", "gen"]), Task("fetch", 2, []), Task("gen", 3, ["fetch"]), Task("lint", 1, ["fetch"]), Task("ship", 1, ["build", "lint"])]
s, cp = plan(ts)
assert s == {"fetch": (0, 2), "gen": (2, 5), "lint": (2, 3), "build": (5, 9), "ship": (9, 10)}, s
assert cp == ["fetch", "gen", "build", "ship"]
assert plan([]) == ({}, [])
s, cp = plan([Task("b", 2, []), Task("a", 2, [])])
assert s == {"a": (0, 2), "b": (0, 2)} and cp == ["a"]
s, cp = plan([Task("z", 5, []), Task("y", 5, []), Task("w", 1, ["y", "z"])])
assert cp == ["y", "w"] and s["w"] == (5, 6)
for bad in ([Task("a", 1, ["nope"])], [Task("a", 1, ["b"]), Task("b", 1, ["a"])], [Task("a", 1, ["a"])]):
    try:
        plan(bad)
        assert False
    except ValueError:
        pass
''',
      "def plan(tasks):\n    by = {t.name: t for t in tasks}\n    for t in tasks:\n        for d in t.deps:\n            if d not in by:\n                raise ValueError('unknown dep ' + d)\n    sched = {}\n    state = {}\n\n    def visit(name):\n        if name in sched:\n            return\n        if state.get(name) == 1:\n            raise ValueError('cycle')\n        state[name] = 1\n        t = by[name]\n        for d in t.deps:\n            visit(d)\n        start = max((sched[d][1] for d in t.deps), default=0)\n        sched[name] = (start, start + t.duration)\n        state[name] = 2\n    for n in sorted(by):\n        visit(n)\n    if not sched:\n        return {}, []\n    cur = min(sched, key=lambda n: (-sched[n][1], n))\n    path = [cur]\n    while by[cur].deps:\n        cur = min((d for d in by[cur].deps if sched[d][1] == sched[cur][0]), key=lambda n: n)\n        path.append(cur)\n    return sched, path[::-1]\n",
      files={"task.py": "from dataclasses import dataclass, field\n\n\n@dataclass\nclass Task:\n    name: str\n    duration: int\n    deps: list = field(default_factory=list)\n",
             "planner.py": "from task import Task\n\n\ndef plan(tasks):\n    raise NotImplementedError\n"}, name="planner.py"),
    # ---------------- hard
    W("py_write_regex_match", "hard", "dp", "def is_match(s, pattern):\n    raise NotImplementedError\n",
      "Implement `is_match(s, pattern)`: full-string match supporting '.' (any single char) and '*' (zero or more of the PRECEDING element). Do not use the re "
      "module. A pattern that starts with '*' or has '*' after '*' raises ValueError.",
      "from solution import is_match\nassert is_match('aa', 'a*')\n",
      r'''
from solution import is_match as m
assert m("aa", "a*") and not m("aa", "a") and m("ab", ".*") and m("aab", "c*a*b")
assert not m("mississippi", "mis*is*p*.")
assert m("mississippi", "mis*is*ip*.")
assert m("", "") and m("", "a*") and not m("", "a") and not m("a", "")
assert m("aaa", "a*a") and m("aaa", "ab*a*c*a")
assert not m("ab", ".*c") and m("abcd", "a.*d")
assert not m("aaa", "aaaa") and m("a", "ab*")
assert m("a" * 30, "a*" * 15 + "b*")
for bad in ("*a", "a**"):
    try:
        m("a", bad)
        assert False, bad
    except ValueError:
        pass
''',
      "def is_match(s, pattern):\n    for i, ch in enumerate(pattern):\n        if ch == '*' and (i == 0 or pattern[i - 1] == '*'):\n            raise ValueError('bad pattern')\n    n, m = len(s), len(pattern)\n    dp = [[False] * (m + 1) for _ in range(n + 1)]\n    dp[n][m] = True\n    for i in range(n, -1, -1):\n        for j in range(m - 1, -1, -1):\n            first = i < n and pattern[j] in (s[i], '.')\n            if j + 1 < m and pattern[j + 1] == '*':\n                dp[i][j] = dp[i][j + 2] or (first and dp[i + 1][j])\n            else:\n                dp[i][j] = first and dp[i + 1][j + 1]\n    return dp[0][0]\n"),
    W("py_write_json_parse", "hard", "parsing", "def parse_json(text):\n    raise NotImplementedError\n",
      "Implement `parse_json(text)`, a strict JSON parser WITHOUT the json module: objects, arrays, strings (escapes \\\" \\\\ \\/ \\b \\f \\n \\r \\t \\uXXXX), numbers "
      "(int when there is no fraction/exponent, else float; no leading zeros, no '+', no bare '.'), true/false/null (-> True/False/None), insignificant "
      "whitespace. Any syntax error, trailing garbage, trailing comma or single-quoted string raises ValueError.",
      "from solution import parse_json\nassert parse_json('[1, {\"a\": null}]') == [1, {'a': None}]\n",
      r'''
from solution import parse_json as p
assert p('[1, {"a": null}]') == [1, {"a": None}]
assert p(' {"k": [true, false, 1.5e2, -0, "x"]} ') == {"k": [True, False, 150.0, 0, "x"]}
assert p("12") == 12 and isinstance(p("12"), int) and isinstance(p("1e2"), float) and isinstance(p("1.0"), float)
assert p('"a\\n\\u0041\\"\\\\"') == 'a\nA"\\'
assert p('"\\/"') == "/"
assert p("[]") == [] and p("{}") == {} and p('{"a":{}}') == {"a": {}}
assert p('{"a":1,"a":2}') == {"a": 2}
assert p('[[[[1]]]]') == [[[[1]]]]
for bad in ["", "[1,]", "{'a':1}", "01", "1.", "-", "[1 2]", '{"a" 1}', '{"a":1,}', "tru", "[1] x", '"abc', '"\\x"', "+1", ".5", '{1:2}', "[", "nul", '"\\u12"', '"a\nb"']:
    try:
        p(bad)
        assert False, repr(bad)
    except ValueError:
        pass
''',
      "import re\n\nNUM = re.compile(r'-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?')\nESC = {'\"': '\"', '\\\\': '\\\\', '/': '/', 'b': '\\b', 'f': '\\f', 'n': '\\n', 'r': '\\r', 't': '\\t'}\n\n\nclass _P:\n    def __init__(self, s):\n        self.s = s\n        self.i = 0\n\n    def ws(self):\n        while self.i < len(self.s) and self.s[self.i] in ' \\t\\n\\r':\n            self.i += 1\n\n    def value(self):\n        self.ws()\n        if self.i >= len(self.s):\n            raise ValueError('eof')\n        c = self.s[self.i]\n        if c == '{':\n            return self.obj()\n        if c == '[':\n            return self.arr()\n        if c == '\"':\n            return self.string()\n        for lit, val in (('true', True), ('false', False), ('null', None)):\n            if self.s.startswith(lit, self.i):\n                self.i += len(lit)\n                return val\n        m = NUM.match(self.s, self.i)\n        if not m:\n            raise ValueError('bad value')\n        self.i = m.end()\n        return float(m.group()) if (m.group(2) or m.group(3)) else int(m.group())\n\n    def string(self):\n        self.i += 1\n        out = []\n        while True:\n            if self.i >= len(self.s):\n                raise ValueError('unterminated')\n            c = self.s[self.i]\n            if c == '\"':\n                self.i += 1\n                return ''.join(out)\n            if c < ' ':\n                raise ValueError('control char')\n            if c == '\\\\':\n                self.i += 1\n                if self.i >= len(self.s):\n                    raise ValueError('bad escape')\n                e = self.s[self.i]\n                if e in ESC:\n                    out.append(ESC[e])\n                    self.i += 1\n                elif e == 'u':\n                    h = self.s[self.i + 1:self.i + 5]\n                    if len(h) != 4 or any(x not in '0123456789abcdefABCDEF' for x in h):\n                        raise ValueError('bad unicode escape')\n                    out.append(chr(int(h, 16)))\n                    self.i += 5\n                else:\n                    raise ValueError('bad escape')\n            else:\n                out.append(c)\n                self.i += 1\n\n    def arr(self):\n        self.i += 1\n        res = []\n        self.ws()\n        if self.s[self.i:self.i + 1] == ']':\n            self.i += 1\n            return res\n        while True:\n            res.append(self.value())\n            self.ws()\n            c = self.s[self.i:self.i + 1]\n            self.i += 1\n            if c == ']':\n                return res\n            if c != ',':\n                raise ValueError('expected , or ]')\n\n    def obj(self):\n        self.i += 1\n        res = {}\n        self.ws()\n        if self.s[self.i:self.i + 1] == '}':\n            self.i += 1\n            return res\n        while True:\n            self.ws()\n            if self.s[self.i:self.i + 1] != '\"':\n                raise ValueError('expected key')\n            k = self.string()\n            self.ws()\n            if self.s[self.i:self.i + 1] != ':':\n                raise ValueError('expected :')\n            self.i += 1\n            res[k] = self.value()\n            self.ws()\n            c = self.s[self.i:self.i + 1]\n            self.i += 1\n            if c == '}':\n                return res\n            if c != ',':\n                raise ValueError('expected , or }')\n\n\ndef parse_json(text):\n    p = _P(text)\n    v = p.value()\n    p.ws()\n    if p.i != len(text):\n        raise ValueError('trailing data')\n    return v\n"),
    W("py_write_multiply_strings", "medium", "math", "def multiply(a, b):\n    raise NotImplementedError\n",
      "Implement `multiply(a, b)`: a and b are non-negative decimal integers given as digit strings (any length, may have leading zeros). Return their product "
      "as a digit string without leading zeros ('0' for zero). Do the schoolbook algorithm digit by digit; do not convert whole strings with int(). "
      "Non-digit or empty input raises ValueError.",
      "from solution import multiply\nassert multiply('12', '12') == '144'\n",
      r'''
from solution import multiply
assert multiply("12", "12") == "144"
assert multiply("0", "999") == "0"
assert multiply("000", "5") == "0"
assert multiply("007", "03") == "21"
assert multiply("123456789012345678901234567890", "987654321098765432109876543210") == str(123456789012345678901234567890 * 987654321098765432109876543210)
assert multiply("99", "99") == "9801"
assert multiply("1" + "0" * 40, "1" + "0" * 40) == "1" + "0" * 80
for bad in ("", "1a", "-3"):
    for args in ((bad, "1"), ("1", bad)):
        try:
            multiply(*args)
            assert False, args
        except ValueError:
            pass
''',
      "def multiply(a, b):\n    for s in (a, b):\n        if not s or not all('0' <= c <= '9' for c in s):\n            raise ValueError(s)\n    res = [0] * (len(a) + len(b))\n    for i in range(len(a) - 1, -1, -1):\n        for j in range(len(b) - 1, -1, -1):\n            s = (ord(a[i]) - 48) * (ord(b[j]) - 48) + res[i + j + 1]\n            res[i + j + 1] = s % 10\n            res[i + j] += s // 10\n    out = ''.join(map(str, res)).lstrip('0')\n    return out or '0'\n"),
    W("py_write_lfu_cache", "hard", "caching", "class LFUCache:\n    pass\n",
      "Implement `LFUCache(capacity)`: `get(key)` returns the value or None and bumps the key's use count; `put(key, value)` inserts or updates (an update also "
      "counts as a use). When inserting a new key into a full cache, first evict the key with the lowest use count; ties go to the least recently used among "
      "them. A new key starts with count 1. `__len__`, `__contains__`. capacity < 1 raises ValueError.",
      "from solution import LFUCache\nc = LFUCache(1); c.put('a', 1)\nassert c.get('a') == 1\n",
      r'''
from solution import LFUCache
c = LFUCache(2)
c.put(1, 1); c.put(2, 2)
assert c.get(1) == 1
c.put(3, 3)
assert c.get(2) is None and c.get(3) == 3
c.put(4, 4)
assert c.get(1) is None and c.get(3) == 3 and c.get(4) == 4
assert len(c) == 2 and 3 in c and 1 not in c
d = LFUCache(2)
d.put("a", 1); d.put("b", 2)
d.put("a", 10)
d.put("c", 3)
assert "b" not in d and d.get("a") == 10
e = LFUCache(3)
for k in "abc":
    e.put(k, k)
e.get("a"); e.get("b")
e.put("d", "d")
assert "c" not in e
e.put("e", "e")
assert "d" not in e and "a" in e and "b" in e
try:
    LFUCache(0)
    assert False
except ValueError:
    pass
''',
      "from collections import OrderedDict\n\n\nclass LFUCache:\n    def __init__(self, capacity):\n        if capacity < 1:\n            raise ValueError('capacity')\n        self.cap = capacity\n        self.vals = {}\n        self.freq = {}\n        self.buckets = {}\n        self.min = 0\n\n    def _touch(self, key):\n        f = self.freq[key]\n        del self.buckets[f][key]\n        if not self.buckets[f]:\n            del self.buckets[f]\n            if self.min == f:\n                self.min = f + 1\n        self.freq[key] = f + 1\n        self.buckets.setdefault(f + 1, OrderedDict())[key] = None\n\n    def get(self, key):\n        if key not in self.vals:\n            return None\n        self._touch(key)\n        return self.vals[key]\n\n    def put(self, key, value):\n        if key in self.vals:\n            self.vals[key] = value\n            self._touch(key)\n            return\n        if len(self.vals) >= self.cap:\n            old, _ = self.buckets[self.min].popitem(last=False)\n            if not self.buckets[self.min]:\n                del self.buckets[self.min]\n            del self.vals[old]\n            del self.freq[old]\n        self.vals[key] = value\n        self.freq[key] = 1\n        self.buckets.setdefault(1, OrderedDict())[key] = None\n        self.min = 1\n\n    def __len__(self):\n        return len(self.vals)\n\n    def __contains__(self, key):\n        return key in self.vals\n"),
    W("py_write_kruskal", "hard", "graphs", "def mst(n, edges):\n    raise NotImplementedError\n",
      "Implement `mst(n, edges)`: minimum spanning tree of an undirected weighted graph with nodes 0..n-1 and edges (u, v, w), using Kruskal with union-find. "
      "Consider edges sorted by (w, min(u,v), max(u,v)); return `(total_weight, chosen)` where chosen lists the picked edges as (min(u,v), max(u,v), w) in the "
      "order picked. Self-loops are never picked. If the graph is not connected raise ValueError. n == 1 gives (0, []); n == 0 gives (0, []).",
      "from solution import mst\nassert mst(2, [(0, 1, 5)]) == (5, [(0, 1, 5)])\n",
      r'''
from solution import mst
edges = [(0, 1, 4), (0, 2, 3), (1, 2, 1), (1, 3, 2), (2, 3, 4), (3, 4, 2), (4, 5, 6), (3, 5, 7)]
assert mst(6, edges) == (14, [(1, 2, 1), (1, 3, 2), (3, 4, 2), (0, 2, 3), (4, 5, 6)])
assert mst(1, []) == (0, []) and mst(0, []) == (0, [])
assert mst(3, [(0, 0, 1), (1, 0, 5), (2, 1, 5), (0, 2, 5)]) == (10, [(0, 1, 5), (0, 2, 5)])
assert mst(2, [(1, 0, 3), (0, 1, 2)]) == (2, [(0, 1, 2)])
for bad in (lambda: mst(3, [(0, 1, 1)]), lambda: mst(2, [])):
    try:
        bad()
        assert False
    except ValueError:
        pass
''',
      "def mst(n, edges):\n    parent = list(range(n))\n\n    def find(x):\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n    norm = sorted((w, min(u, v), max(u, v)) for u, v, w in edges)\n    total, chosen = 0, []\n    for w, a, b in norm:\n        ra, rb = find(a), find(b)\n        if ra != rb:\n            parent[ra] = rb\n            total += w\n            chosen.append((a, b, w))\n    if n and len(chosen) != n - 1:\n        raise ValueError('disconnected')\n    return total, chosen\n"),
    W("py_write_scc", "hard", "graphs", "def scc(graph):\n    raise NotImplementedError\n",
      "Implement `scc(graph)`: strongly connected components of a directed graph given as dict node -> list of successors (successor nodes may be absent as keys; "
      "nodes are sortable). Return a list of components, each a sorted list, with the components sorted by their smallest node. Must not use recursion "
      "(a 5000-node chain and a 5000-node cycle must work).",
      "from solution import scc\nassert scc({'a': ['b'], 'b': ['a']}) == [['a', 'b']]\n",
      r'''
from solution import scc
assert scc({"a": ["b"], "b": ["a"]}) == [["a", "b"]]
assert scc({}) == []
g = {1: [2], 2: [3], 3: [1, 4], 4: [5], 5: [6], 6: [4], 7: [6, 8], 8: []}
assert scc(g) == [[1, 2, 3], [4, 5, 6], [7], [8]]
assert scc({"x": ["x"], "y": []}) == [["x"], ["y"]]
assert scc({"a": ["z"]}) == [["a"], ["z"]]
chain = {i: [i + 1] for i in range(5000)}
r = scc(chain)
assert len(r) == 5001 and r[0] == [0]
cyc = {i: [(i + 1) % 5000] for i in range(5000)}
assert scc(cyc) == [list(range(5000))]
''',
      "def scc(graph):\n    nodes = set(graph)\n    for vs in graph.values():\n        nodes.update(vs)\n    seen, order = set(), []\n    for s in sorted(nodes):\n        if s in seen:\n            continue\n        seen.add(s)\n        st = [(s, iter(graph.get(s, ())))]\n        while st:\n            u, it = st[-1]\n            for v in it:\n                if v not in seen:\n                    seen.add(v)\n                    st.append((v, iter(graph.get(v, ()))))\n                    break\n            else:\n                order.append(u)\n                st.pop()\n    rev = {}\n    for u in nodes:\n        for v in graph.get(u, ()):\n            rev.setdefault(v, []).append(u)\n    comp_seen, comps = set(), []\n    for s in reversed(order):\n        if s in comp_seen:\n            continue\n        comp_seen.add(s)\n        comp, st = [], [s]\n        while st:\n            u = st.pop()\n            comp.append(u)\n            for v in rev.get(u, ()):\n                if v not in comp_seen:\n                    comp_seen.add(v)\n                    st.append(v)\n        comps.append(sorted(comp))\n    return sorted(comps, key=lambda c: c[0])\n"),
    W("py_write_bellman_ford", "hard", "graphs", "def shortest(n, edges, src):\n    raise NotImplementedError\n",
      "Implement `shortest(n, edges, src)` (Bellman-Ford): directed edges (u, v, w) with possibly negative weights, nodes 0..n-1. Return a list of n distances from "
      "src (float('inf') when unreachable). If a negative-weight cycle is reachable from src raise ValueError (negative cycles that are unreachable from src "
      "are ignored).",
      "from solution import shortest\nassert shortest(2, [(0, 1, 3)], 0) == [0, 3]\n",
      r'''
from solution import shortest
INF = float("inf")
assert shortest(2, [(0, 1, 3)], 0) == [0, 3]
assert shortest(3, [(0, 1, 4), (0, 2, 5), (2, 1, -3)], 0) == [0, 2, 5]
assert shortest(3, [(0, 1, 1)], 0) == [0, 1, INF]
assert shortest(3, [(1, 2, -5), (2, 1, 2)], 0) == [0, INF, INF]
for edges in ([(0, 1, 1), (1, 2, -2), (2, 1, 1)], [(0, 0, -1)]):
    try:
        shortest(3, edges, 0)
        assert False
    except ValueError:
        pass
assert shortest(1, [], 0) == [0]
assert shortest(4, [(0, 1, 2), (1, 2, 2), (0, 2, 5), (2, 3, -1)], 0) == [0, 2, 4, 3]
''',
      "def shortest(n, edges, src):\n    INF = float('inf')\n    d = [INF] * n\n    d[src] = 0\n    for _ in range(n - 1):\n        ch = False\n        for u, v, w in edges:\n            if d[u] != INF and d[u] + w < d[v]:\n                d[v] = d[u] + w\n                ch = True\n        if not ch:\n            break\n    for u, v, w in edges:\n        if d[u] != INF and d[u] + w < d[v]:\n            raise ValueError('negative cycle')\n    return d\n"),
    W("py_write_autocomplete", "medium", "tries", "class Autocomplete:\n    pass\n",
      "Implement `Autocomplete`: `add(word, weight=1)` (weights accumulate when the same word is added again) and `suggest(prefix, k=3)` returning up to k stored "
      "words that start with prefix, ordered by total weight descending then alphabetically. Matching is case-sensitive; an empty prefix matches everything; "
      "k <= 0 returns [].",
      "from solution import Autocomplete\na = Autocomplete(); a.add('cat')\nassert a.suggest('c') == ['cat']\n",
      r'''
from solution import Autocomplete
a = Autocomplete()
for w, wt in [("car", 5), ("card", 2), ("care", 2), ("cat", 9), ("dog", 1), ("Car", 100)]:
    a.add(w, wt)
assert a.suggest("ca") == ["cat", "car", "card"]
assert a.suggest("ca", 10) == ["cat", "car", "card", "care"]
assert a.suggest("car", 2) == ["car", "card"]
assert a.suggest("x") == []
assert a.suggest("", 2) == ["Car", "cat"]
assert a.suggest("ca", 0) == []
a.add("care", 10)
assert a.suggest("car", 1) == ["care"]
a.add("dog")
assert a.suggest("d") == ["dog"]
''',
      "class Autocomplete:\n    def __init__(self):\n        self.w = {}\n\n    def add(self, word, weight=1):\n        self.w[word] = self.w.get(word, 0) + weight\n\n    def suggest(self, prefix, k=3):\n        if k <= 0:\n            return []\n        c = [w for w in self.w if w.startswith(prefix)]\n        c.sort(key=lambda w: (-self.w[w], w))\n        return c[:k]\n"),
    W("py_write_segment_tree", "hard", "data-structures", "class SegmentTree:\n    pass\n",
      "Implement `SegmentTree(values, op='sum')` supporting `update(i, value)` (point assignment), `query(l, r)` over the half-open range [l, r) and `__len__`. "
      "`op` is 'sum', 'min' or 'max'. An empty range (l == r) returns the identity (0, inf, -inf). Invalid ranges (l > r or out of bounds) raise IndexError. "
      "Unknown op raises ValueError. Queries and updates must be O(log n) (a 50000-element tree with 50000 operations must be fast).",
      "from solution import SegmentTree\nassert SegmentTree([1, 2, 3]).query(0, 3) == 6\n",
      r'''
from solution import SegmentTree
import random
t = SegmentTree([5, 3, 8, 6, 2, 7])
assert t.query(0, 6) == 31 and t.query(1, 4) == 17 and t.query(2, 3) == 8 and t.query(3, 3) == 0
t.update(2, 0)
assert t.query(0, 6) == 23 and t.query(2, 3) == 0
m = SegmentTree([5, 3, 8, 6, 2, 7], "min")
assert m.query(0, 6) == 2 and m.query(0, 4) == 3 and m.query(2, 2) == float("inf")
m.update(4, 10)
assert m.query(0, 6) == 3
x = SegmentTree([5, 3, 8], "max")
assert x.query(0, 3) == 8 and x.query(1, 1) == float("-inf") and len(x) == 3
for bad in [(3, 1), (0, 7), (-1, 2)]:
    try:
        t.query(*bad)
        assert False, bad
    except IndexError:
        pass
try:
    SegmentTree([1], "avg")
    assert False
except ValueError:
    pass
random.seed(5)
vals = [random.randint(-50, 50) for _ in range(50000)]
for op, f in (("sum", sum), ("min", min), ("max", max)):
    t = SegmentTree(vals, op)
    ref = list(vals)
    for _ in range(50000):
        if random.random() < 0.5:
            i = random.randrange(50000); v = random.randint(-50, 50)
            t.update(i, v); ref[i] = v
        else:
            l = random.randrange(50000); r = random.randrange(l + 1, 50001)
            if random.random() < 0.002:
                assert t.query(l, r) == f(ref[l:r])
    assert t.query(0, 50000) == f(ref)
''',
      "class SegmentTree:\n    def __init__(self, values, op='sum'):\n        ops = {'sum': (lambda a, b: a + b, 0), 'min': (min, float('inf')), 'max': (max, float('-inf'))}\n        if op not in ops:\n            raise ValueError(op)\n        self.f, self.id = ops[op]\n        self.n = len(values)\n        self.t = [self.id] * (2 * self.n) if self.n else []\n        for i, v in enumerate(values):\n            self.t[self.n + i] = v\n        for i in range(self.n - 1, 0, -1):\n            self.t[i] = self.f(self.t[2 * i], self.t[2 * i + 1])\n\n    def __len__(self):\n        return self.n\n\n    def update(self, i, value):\n        if not 0 <= i < self.n:\n            raise IndexError(i)\n        i += self.n\n        self.t[i] = value\n        while i > 1:\n            i //= 2\n            self.t[i] = self.f(self.t[2 * i], self.t[2 * i + 1])\n\n    def query(self, l, r):\n        if not 0 <= l <= r <= self.n:\n            raise IndexError((l, r))\n        res_l = res_r = self.id\n        l += self.n\n        r += self.n\n        while l < r:\n            if l & 1:\n                res_l = self.f(res_l, self.t[l])\n                l += 1\n            if r & 1:\n                r -= 1\n                res_r = self.f(self.t[r], res_r)\n            l //= 2\n            r //= 2\n        return self.f(res_l, res_r)\n"),
    W("py_write_inversions", "medium", "data-structures", "def count_inversions(nums):\n    raise NotImplementedError\n",
      "Implement `count_inversions(nums)`: the number of pairs i < j with nums[i] > nums[j]. Must run in O(n log n) (50000 elements must finish quickly).",
      "from solution import count_inversions\nassert count_inversions([2, 1]) == 1\n",
      r'''
from solution import count_inversions as ci
import random
assert ci([]) == 0 and ci([1]) == 0 and ci([1, 2, 3]) == 0 and ci([3, 2, 1]) == 3
assert ci([2, 4, 1, 3, 5]) == 3
assert ci([1, 1, 1]) == 0
assert ci([2, 1, 2, 1]) == 3
random.seed(2)
xs = [random.randint(0, 30) for _ in range(300)]
assert ci(xs) == sum(1 for i in range(300) for j in range(i + 1, 300) if xs[i] > xs[j])
n = 50000
assert ci(list(range(n, 0, -1))) == n * (n - 1) // 2
assert ci(list(range(n))) == 0
''',
      "def count_inversions(nums):\n    a = list(nums)\n    tmp = [0] * len(a)\n\n    def sort(lo, hi):\n        if hi - lo < 2:\n            return 0\n        mid = (lo + hi) // 2\n        c = sort(lo, mid) + sort(mid, hi)\n        i, j, k = lo, mid, lo\n        while i < mid and j < hi:\n            if a[i] <= a[j]:\n                tmp[k] = a[i]\n                i += 1\n            else:\n                tmp[k] = a[j]\n                j += 1\n                c += mid - i\n            k += 1\n        while i < mid:\n            tmp[k] = a[i]\n            i += 1\n            k += 1\n        while j < hi:\n            tmp[k] = a[j]\n            j += 1\n            k += 1\n        a[lo:hi] = tmp[lo:hi]\n        return c\n    return sort(0, len(a))\n"),
    W("py_write_n_queens", "medium", "backtracking", "def count_queens(n):\n    raise NotImplementedError\n",
      "Implement `count_queens(n)`: the number of ways to place n non-attacking queens on an n x n board. n == 0 gives 1; negative n raises ValueError.",
      "from solution import count_queens\nassert count_queens(4) == 2\n",
      "from solution import count_queens\nassert [count_queens(n) for n in range(0, 9)] == [1, 1, 0, 0, 2, 10, 4, 40, 92]\nassert count_queens(9) == 352\ntry:\n    count_queens(-1)\n    assert False\nexcept ValueError:\n    pass\n",
      "def count_queens(n):\n    if n < 0:\n        raise ValueError(n)\n\n    def go(row, cols, d1, d2):\n        if row == n:\n            return 1\n        t = 0\n        for c in range(n):\n            if c in cols or row - c in d1 or row + c in d2:\n                continue\n            t += go(row + 1, cols | {c}, d1 | {row - c}, d2 | {row + c})\n        return t\n    return go(0, frozenset(), frozenset(), frozenset())\n"),
    W("py_write_skyline", "hard", "heaps", "def skyline(buildings):\n    raise NotImplementedError\n",
      "Implement `skyline(buildings)`: buildings are (left, right, height) with left < right, height > 0, in any order. Return the skyline as a list of [x, height] "
      "key points (a point where the height changes) sorted by x; the last point has height 0; no two consecutive points have the same height.",
      "from solution import skyline\nassert skyline([(0, 2, 3)]) == [[0, 3], [2, 0]]\n",
      r'''
from solution import skyline
assert skyline([(0, 2, 3)]) == [[0, 3], [2, 0]]
assert skyline([(2, 9, 10), (3, 7, 15), (5, 12, 12), (15, 20, 10), (19, 24, 8)]) == [[2, 10], [3, 15], [7, 12], [12, 0], [15, 10], [20, 8], [24, 0]]
assert skyline([(0, 2, 3), (2, 5, 3)]) == [[0, 3], [5, 0]]
assert skyline([]) == []
assert skyline([(1, 5, 3), (1, 5, 4)]) == [[1, 4], [5, 0]]
assert skyline([(1, 3, 2), (2, 4, 2)]) == [[1, 2], [4, 0]]
assert skyline([(1, 10, 1), (2, 3, 5), (4, 5, 5)]) == [[1, 1], [2, 5], [3, 1], [4, 5], [5, 1], [10, 0]]
''',
      "import heapq\n\n\ndef skyline(buildings):\n    ev = []\n    for l, r, h in buildings:\n        ev.append((l, -h, r))\n        ev.append((r, 0, 0))\n    ev.sort()\n    res = []\n    heap = [(0, float('inf'))]\n    for x, nh, r in ev:\n        while heap[0][1] <= x:\n            heapq.heappop(heap)\n        if nh:\n            heapq.heappush(heap, (nh, r))\n        h = -heap[0][0]\n        if not res or res[-1][1] != h:\n            res.append([x, h])\n    return res\n"),
    W("py_write_text_justify", "hard", "strings", "def justify(words, width):\n    raise NotImplementedError\n",
      "Implement `justify(words, width)`: pack words greedily into lines of exactly `width` characters (each word fits; at least one space between words). In every "
      "line except the last and lines with a single word, distribute extra spaces between words as evenly as possible with the leftmost gaps getting more. "
      "The last line and single-word lines are left-justified and padded with trailing spaces. Return the list of lines.",
      "from solution import justify\nassert justify(['a', 'b'], 3) == ['a b']\n",
      r'''
from solution import justify
w = ["This", "is", "an", "example", "of", "text", "justification."]
assert justify(w, 16) == ["This    is    an", "example  of text", "justification.  "]
assert justify(["What", "must", "be", "acknowledgment", "shall", "be"], 16) == ["What   must   be", "acknowledgment  ", "shall be        "]
assert justify(["a"], 3) == ["a  "]
assert justify([], 5) == []
assert justify(["a", "b", "c", "d", "e"], 3) == ["a b", "c d", "e  "]
assert justify(["ab", "cd"], 5) == ["ab cd"]
assert all(len(l) == 10 for l in justify("one two three four five six seven eight nine ten".split(), 10))
''',
      "def justify(words, width):\n    lines, cur, n = [], [], 0\n    for w in words:\n        if cur and n + len(w) + len(cur) > width:\n            lines.append(cur)\n            cur, n = [], 0\n        cur.append(w)\n        n += len(w)\n    if cur:\n        lines.append(cur)\n    out = []\n    for i, ws in enumerate(lines):\n        if i == len(lines) - 1 or len(ws) == 1:\n            out.append((' '.join(ws)).ljust(width))\n        else:\n            gaps = len(ws) - 1\n            spaces = width - sum(map(len, ws))\n            q, r = divmod(spaces, gaps)\n            s = ''\n            for j, x in enumerate(ws[:-1]):\n                s += x + ' ' * (q + (1 if j < r else 0))\n            out.append(s + ws[-1])\n    return out\n"),
    W("py_write_cron_match", "hard", "parsing", "def matches(expr, minute, hour, dom, month, dow):\n    raise NotImplementedError\n",
      "Implement `matches(expr, minute, hour, dom, month, dow)`: does a 5-field cron expression `minute hour day-of-month month day-of-week` match the given time "
      "values? Fields support `*`, single numbers, ranges `a-b`, lists `a,b,c`, steps `*/n` and `a-b/n` (and `a/n` meaning a..max step n). Ranges: minute 0-59, "
      "hour 0-23, dom 1-31, month 1-12, dow 0-6 (0 = Sunday). Standard rule: if BOTH dom and dow fields are restricted (not exactly '*'), the day matches when "
      "EITHER matches; otherwise both must match. Wrong field count, bad numbers, out-of-range values, a>b, or step < 1 raise ValueError (even if the time "
      "would not match).",
      "from solution import matches\nassert matches('* * * * *', 5, 5, 5, 5, 5)\n",
      r'''
from solution import matches as m
assert m("* * * * *", 0, 0, 1, 1, 0)
assert m("*/15 * * * *", 45, 3, 9, 2, 4) and not m("*/15 * * * *", 44, 3, 9, 2, 4)
assert m("0 9-17 * * 1-5", 0, 9, 14, 6, 3) and not m("0 9-17 * * 1-5", 0, 18, 14, 6, 3)
assert not m("0 9-17 * * 1-5", 0, 10, 14, 6, 0)
assert m("30 2 1,15 * *", 30, 2, 15, 7, 2) and not m("30 2 1,15 * *", 30, 2, 16, 7, 2)
assert m("0 0 13 * 5", 0, 0, 13, 3, 2) and m("0 0 13 * 5", 0, 0, 20, 3, 5) and not m("0 0 13 * 5", 0, 0, 20, 3, 4)
assert m("0 0 * * 0", 0, 0, 20, 3, 0) and not m("0 0 * * 0", 0, 0, 20, 3, 1)
assert m("10-30/10 * * * *", 20, 1, 1, 1, 1) and not m("10-30/10 * * * *", 25, 1, 1, 1, 1)
assert m("5/20 * * * *", 45, 1, 1, 1, 1) and not m("5/20 * * * *", 40, 1, 1, 1, 1)
assert m("0 0 1 1,6 *", 0, 0, 1, 6, 3) and not m("0 0 1 1,6 *", 0, 0, 1, 7, 3)
assert m("0,30 * * * *", 30, 0, 1, 1, 1)
for bad in ["* * * *", "* * * * * *", "60 * * * *", "* 24 * * *", "* * 0 * *", "* * * 13 *", "* * * * 7", "5-1 * * * *", "*/0 * * * *", "a * * * *", ", * * * *", "1- * * * *"]:
    try:
        m(bad, 0, 0, 1, 1, 1)
        assert False, bad
    except ValueError:
        pass
''',
      "RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]\n\n\ndef _field(f, lo, hi):\n    vals = set()\n    for part in f.split(','):\n        step, has_step = 1, False\n        if '/' in part:\n            part, s = part.split('/', 1)\n            step, has_step = int(s), True\n            if step < 1:\n                raise ValueError('step')\n        if part == '*':\n            a, b = lo, hi\n        elif '-' in part:\n            x, y = part.split('-', 1)\n            a, b = int(x), int(y)\n        else:\n            a = int(part)\n            b = hi if has_step else a\n        if a < lo or b > hi or a > b:\n            raise ValueError('range')\n        vals.update(range(a, b + 1, step))\n    return vals\n\n\ndef matches(expr, minute, hour, dom, month, dow):\n    f = expr.split()\n    if len(f) != 5:\n        raise ValueError('fields')\n    sets = [_field(x, lo, hi) for x, (lo, hi) in zip(f, RANGES)]\n    if minute not in sets[0] or hour not in sets[1] or month not in sets[3]:\n        return False\n    d_ok, w_ok = dom in sets[2], dow in sets[4]\n    if f[2] != '*' and f[4] != '*':\n        return d_ok or w_ok\n    return d_ok and w_ok\n"),
    W("py_write_line_diff", "medium", "dp", "def diff(a, b):\n    raise NotImplementedError\n",
      "Implement `diff(a, b)` for two lists of lines: return a list of (op, line) with op ' ' (kept), '-' (only in a) or '+' (only in b), such that the kept lines form a "
      "longest common subsequence of a and b, the '-' and ' ' entries in order reproduce `a`, and the '+' and ' ' entries in order reproduce `b`. When a line "
      "must be removed and another added at the same place, put '-' entries before '+' entries.",
      "from solution import diff\nassert diff(['x'], ['x']) == [(' ', 'x')]\n",
      r'''
from solution import diff
assert diff(["x"], ["x"]) == [(" ", "x")]
assert diff([], []) == []
assert diff(["a"], []) == [("-", "a")]
assert diff([], ["a"]) == [("+", "a")]
assert diff(["a", "b", "c"], ["a", "c"]) == [(" ", "a"), ("-", "b"), (" ", "c")]
assert diff(["a", "b"], ["a", "x"]) == [(" ", "a"), ("-", "b"), ("+", "x")]


def lcs_len(a, b):
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a)):
        for j in range(len(b)):
            dp[i + 1][j + 1] = dp[i][j] + 1 if a[i] == b[j] else max(dp[i][j + 1], dp[i + 1][j])
    return dp[-1][-1]


import random
random.seed(9)
for _ in range(60):
    a = [random.choice("abcd") for _ in range(random.randint(0, 12))]
    b = [random.choice("abcd") for _ in range(random.randint(0, 12))]
    d = diff(a, b)
    assert [l for o, l in d if o in " -"] == a
    assert [l for o, l in d if o in " +"] == b
    assert sum(1 for o, _ in d if o == " ") == lcs_len(a, b)
    for k in range(1, len(d)):
        assert not (d[k - 1][0] == "+" and d[k][0] == "-"), d
''',
      "def diff(a, b):\n    n, m = len(a), len(b)\n    dp = [[0] * (m + 1) for _ in range(n + 1)]\n    for i in range(n - 1, -1, -1):\n        for j in range(m - 1, -1, -1):\n            dp[i][j] = dp[i + 1][j + 1] + 1 if a[i] == b[j] else max(dp[i + 1][j], dp[i][j + 1])\n    out = []\n    i = j = 0\n    while i < n or j < m:\n        if i < n and j < m and a[i] == b[j]:\n            out.append((' ', a[i]))\n            i += 1\n            j += 1\n        elif i < n and (j == m or dp[i + 1][j] >= dp[i][j + 1]):\n            out.append(('-', a[i]))\n            i += 1\n        else:\n            out.append(('+', b[j]))\n            j += 1\n    return out\n"),
    W("py_write_sudoku_solve", "hard", "backtracking", "def solve(board):\n    raise NotImplementedError\n",
      "Implement `solve(board)`: board is 9 strings of 9 chars ('1'-'9' or '.'). Return the solved board as 9 strings, or None if the given clues already "
      "conflict or no solution exists. Do not mutate the input.",
      "from solution import solve\nassert solve(['534678912', '672195348', '198342567', '859761423', '426853791', '713924856', '961537284', '287419635', '34528617.']) [8] == '345286179'\n",
      r'''
from solution import solve
puzzle = ["53..7....", "6..195...", ".98....6.", "8...6...3", "4..8.3..1", "7...2...6", ".6....28.", "...419..5", "....8..79"]
want = ["534678912", "672195348", "198342567", "859761423", "426853791", "713924856", "961537284", "287419635", "345286179"]
before = list(puzzle)
assert solve(puzzle) == want
assert puzzle == before
assert solve(want) == want
bad = list(puzzle); bad[0] = "55..7...."
assert solve(bad) is None
dead = list(puzzle); dead[0] = "53..7...."; dead[1] = "6..195..." ; dead[2] = ".98....6."
dead[4] = "4..8.3..1"; dead[8] = "....8..79"
dead[0] = "534.7...."; dead[1] = "6..195..."
dead[7] = "...419..5"
dead = ["1234567..", "........9"] + ["........."] * 7
assert solve(dead) is None
assert solve(["........."] * 9) is not None
''',
      "def solve(board):\n    g = [[0 if c == '.' else int(c) for c in row] for row in board]\n    rows = [set() for _ in range(9)]\n    cols = [set() for _ in range(9)]\n    box = [set() for _ in range(9)]\n    for r in range(9):\n        for c in range(9):\n            d = g[r][c]\n            if d:\n                b = r // 3 * 3 + c // 3\n                if d in rows[r] or d in cols[c] or d in box[b]:\n                    return None\n                rows[r].add(d); cols[c].add(d); box[b].add(d)\n    empties = [(r, c) for r in range(9) for c in range(9) if not g[r][c]]\n\n    def go():\n        best, bo = None, None\n        for r, c in empties:\n            if g[r][c]:\n                continue\n            opts = [d for d in range(1, 10) if d not in rows[r] and d not in cols[c] and d not in box[r // 3 * 3 + c // 3]]\n            if best is None or len(opts) < len(bo):\n                best, bo = (r, c), opts\n                if not opts:\n                    return False\n        if best is None:\n            return True\n        r, c = best\n        b = r // 3 * 3 + c // 3\n        for d in bo:\n            g[r][c] = d\n            rows[r].add(d); cols[c].add(d); box[b].add(d)\n            if go():\n                return True\n            g[r][c] = 0\n            rows[r].discard(d); cols[c].discard(d); box[b].discard(d)\n        return False\n    if not go():\n        return None\n    return [''.join(map(str, row)) for row in g]\n"),
]
