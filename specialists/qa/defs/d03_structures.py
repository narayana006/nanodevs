TASKS = []

TASKS.append(dict(
    id="qa_lru_cache", diff="hard",
    spec="Write tests for the `LRUCache` class in lru.py.",
    files={"lru.py": r'''
from collections import OrderedDict


class LRUCache:
    """Least-recently-used cache with a fixed capacity (>= 1, else ValueError).
    get(key, default=None) returns the value and marks the key as most recently used.
    put(key, value) inserts or updates (updating also marks as most recent); when the size would exceed
    capacity, the least recently used key is evicted. `in` and len() do not affect recency."""

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._d = OrderedDict()

    def get(self, key, default=None):
        if key not in self._d:
            return default
        self._d.move_to_end(key)
        return self._d[key]

    def put(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) > self.capacity:
            self._d.popitem(last=False)

    def __contains__(self, key):
        return key in self._d

    def __len__(self):
        return len(self._d)

    def keys(self):
        """Keys from least to most recently used."""
        return list(self._d)
'''},
    tests=r'''
from lru import LRUCache

c = LRUCache(2)
assert len(c) == 0
assert c.get("a") is None
assert c.get("a", 5) == 5
c.put("a", 1)
c.put("b", 2)
assert c.get("a") == 1
c.put("c", 3)
assert "b" not in c
assert "a" in c and "c" in c
assert len(c) == 2
assert c.keys() == ["a", "c"]

c = LRUCache(2)
c.put("a", 1)
c.put("b", 2)
c.put("a", 10)
c.put("c", 3)
assert "b" not in c
assert c.get("a") == 10

c = LRUCache(2)
c.put("a", 1)
c.put("b", 2)
assert "a" in c
assert len(c) == 2
c.put("c", 3)
assert "a" not in c

c = LRUCache(3)
for k in "abc":
    c.put(k, k)
c.get("a")
assert c.keys() == ["b", "c", "a"]
c.put("d", "d")
assert c.keys() == ["c", "a", "d"]
c.put("c", "C")
assert c.keys() == ["a", "d", "c"]
assert c.get("zzz") is None

c = LRUCache(1)
c.put("a", 1)
c.put("b", 2)
assert "a" not in c and c.get("b") == 2 and len(c) == 1
c.put("b", 3)
assert len(c) == 1 and c.get("b") == 3
for bad in (0, -1):
    try:
        LRUCache(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("logic: get does not refresh", "        self._d.move_to_end(key)\n        return self._d[key]", "        return self._d[key]"),
        ("logic: update does not refresh", "        if key in self._d:\n            self._d.move_to_end(key)\n        self._d[key] = value", "        self._d[key] = value"),
        ("ordering: evicts most recent", "popitem(last=False)", "popitem(last=True)"),
        ("off-by-one: capacity", "len(self._d) > self.capacity", "len(self._d) >= self.capacity"),
        ("off-by-one: evicts late", "len(self._d) > self.capacity", "len(self._d) > self.capacity + 1"),
        ("logic: contains refreshes", "    def __contains__(self, key):\n        return key in self._d", "    def __contains__(self, key):\n        if key in self._d:\n            self._d.move_to_end(key)\n        return key in self._d"),
        ("wrong-default: default ignored", "            return default", "            return None"),
        ("boundary: capacity 1 rejected", "if capacity < 1:", "if capacity < 2:"),
    ],
    weak=14,
    regress=[dict(mut=1, report="Reading a key with get() does not protect it from eviction. With capacity 2: put a, put b, get a, put c -> 'a' gets evicted but 'b' should be.", test="from lru import LRUCache\nc = LRUCache(2)\nc.put('a', 1)\nc.put('b', 2)\nc.get('a')\nc.put('c', 3)\nassert 'a' in c\nassert 'b' not in c\n")],
))

TASKS.append(dict(
    id="qa_ring_buffer", diff="medium",
    spec="Write tests for the `RingBuffer` class in ring.py.",
    files={"ring.py": r'''
class RingBuffer:
    """Fixed-capacity FIFO. append(x) when full overwrites the oldest item. pop_oldest() removes and returns
    the oldest item (IndexError if empty). to_list() returns items oldest to newest. len() is the item count.
    capacity < 1 -> ValueError. is_full() is True when len == capacity."""

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._buf = [None] * capacity
        self._start = 0
        self._size = 0

    def append(self, x):
        end = (self._start + self._size) % self.capacity
        self._buf[end] = x
        if self._size == self.capacity:
            self._start = (self._start + 1) % self.capacity
        else:
            self._size += 1

    def pop_oldest(self):
        if self._size == 0:
            raise IndexError("empty")
        x = self._buf[self._start]
        self._buf[self._start] = None
        self._start = (self._start + 1) % self.capacity
        self._size -= 1
        return x

    def to_list(self):
        return [self._buf[(self._start + i) % self.capacity] for i in range(self._size)]

    def is_full(self):
        return self._size == self.capacity

    def __len__(self):
        return self._size
'''},
    tests=r'''
from ring import RingBuffer

r = RingBuffer(3)
assert len(r) == 0 and r.to_list() == [] and not r.is_full()
r.append(1)
r.append(2)
assert r.to_list() == [1, 2] and len(r) == 2 and not r.is_full()
r.append(3)
assert r.is_full() and r.to_list() == [1, 2, 3]
r.append(4)
assert r.to_list() == [2, 3, 4] and len(r) == 3
r.append(5)
r.append(6)
r.append(7)
assert r.to_list() == [5, 6, 7]
assert r.pop_oldest() == 5
assert r.to_list() == [6, 7] and len(r) == 2 and not r.is_full()
r.append(8)
assert r.to_list() == [6, 7, 8]
assert r.pop_oldest() == 6
assert r.pop_oldest() == 7
assert r.pop_oldest() == 8
try:
    r.pop_oldest()
except IndexError:
    pass
else:
    raise AssertionError("expected IndexError")
r.append(9)
assert r.to_list() == [9]
r1 = RingBuffer(1)
r1.append("a")
r1.append("b")
assert r1.to_list() == ["b"] and r1.is_full()
assert r1.pop_oldest() == "b"
r = RingBuffer(2)
r.append(None)
assert len(r) == 1 and r.to_list() == [None]
try:
    RingBuffer(0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("logic: overwrite does not advance start", "            self._start = (self._start + 1) % self.capacity\n        else:", "            pass\n        else:"),
        ("off-by-one: full detection", "if self._size == self.capacity:\n            self._start", "if self._size == self.capacity - 1:\n            self._start"),
        ("missing-edge-case: pop on empty", 'if self._size == 0:\n            raise IndexError("empty")', "if self._size == 0:\n            return None"),
        ("logic: pop does not advance", "        self._start = (self._start + 1) % self.capacity\n        self._size -= 1", "        self._size -= 1"),
        ("logic: pop newest", "x = self._buf[self._start]\n        self._buf[self._start] = None", "x = self._buf[(self._start + self._size - 1) % self.capacity]\n        self._buf[(self._start + self._size - 1) % self.capacity] = None"),
        ("ordering: to_list order", "for i in range(self._size)]", "for i in reversed(range(self._size))]"),
        ("logic: is_full", "return self._size == self.capacity\n\n    def __len__", "return self._size >= self.capacity - 1\n\n    def __len__"),
        ("boundary: capacity 1 rejected", "if capacity < 1:", "if capacity < 2:"),
    ],
    weak=14,
))

TASKS.append(dict(
    id="qa_min_stack", diff="medium",
    spec="Write tests for the `MinStack` class in minstack.py.",
    files={"minstack.py": r'''
class MinStack:
    """Stack that also reports its minimum in O(1). push(x), pop() -> x, top() -> x, min() -> smallest item.
    pop/top/min on an empty stack -> IndexError. Duplicates of the minimum are handled correctly."""

    def __init__(self):
        self._items = []
        self._mins = []

    def push(self, x):
        self._items.append(x)
        if not self._mins or x <= self._mins[-1]:
            self._mins.append(x)

    def pop(self):
        if not self._items:
            raise IndexError("empty")
        x = self._items.pop()
        if x == self._mins[-1]:
            self._mins.pop()
        return x

    def top(self):
        if not self._items:
            raise IndexError("empty")
        return self._items[-1]

    def min(self):
        if not self._items:
            raise IndexError("empty")
        return self._mins[-1]

    def __len__(self):
        return len(self._items)
'''},
    tests=r'''
from minstack import MinStack

s = MinStack()
assert len(s) == 0
for f in (s.pop, s.top, s.min):
    try:
        f()
    except IndexError:
        pass
    else:
        raise AssertionError("expected IndexError")
s.push(5)
assert s.min() == 5 and s.top() == 5
s.push(3)
assert s.min() == 3 and s.top() == 3
s.push(7)
assert s.min() == 3 and s.top() == 7
assert s.pop() == 7
assert s.min() == 3
assert s.pop() == 3
assert s.min() == 5

s = MinStack()
s.push(2)
s.push(2)
s.push(4)
assert s.pop() == 4
assert s.min() == 2
assert s.pop() == 2
assert s.min() == 2
assert s.pop() == 2
assert len(s) == 0
try:
    s.min()
except IndexError:
    pass
else:
    raise AssertionError("expected IndexError")

s = MinStack()
s.push(1)
s.push(0)
s.push(-1)
assert s.min() == -1
s.pop()
assert s.min() == 0
s.pop()
assert s.min() == 1
assert len(s) == 1
s.push(10)
s.push(9)
assert s.min() == 1 and len(s) == 3
''',
    muts=[
        ("comparison: duplicates of min not tracked", "x <= self._mins[-1]", "x < self._mins[-1]"),
        ("logic: min popped always", "if x == self._mins[-1]:\n            self._mins.pop()", "self._mins.pop() if self._mins else None"),
        ("logic: min never popped", "        if x == self._mins[-1]:\n            self._mins.pop()\n", ""),
        ("logic: top returns bottom", "return self._items[-1]", "return self._items[0]"),
        ("missing-edge-case: empty pop", 'if not self._items:\n            raise IndexError("empty")\n        x = self._items.pop()', "if not self._items:\n            return None\n        x = self._items.pop()"),
        ("missing-edge-case: empty min", 'if not self._items:\n            raise IndexError("empty")\n        return self._mins[-1]', "if not self._items:\n            return None\n        return self._mins[-1]"),
        ("comparison: tracks max", "x <= self._mins[-1]", "x >= self._mins[-1]"),
    ],
    weak=8,
))

TASKS.append(dict(
    id="qa_trie", diff="medium",
    spec="Write tests for the `Trie` class in trie.py.",
    files={"trie.py": r'''
class Trie:
    """Prefix tree of strings. insert(word); contains(word) is True only for inserted whole words;
    starts_with(prefix) is True if any inserted word begins with prefix (the empty prefix matches iff the trie is
    non-empty); words_with_prefix(prefix) returns the inserted words that start with prefix, sorted;
    remove(word) deletes an inserted word and returns True, or returns False if it was not inserted.
    Removing a word must not affect other words that share a prefix with it. The empty string is a valid word."""

    def __init__(self):
        self._root = {}

    def insert(self, word):
        node = self._root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True

    def _find(self, s):
        node = self._root
        for ch in s:
            if ch not in node:
                return None
            node = node[ch]
        return node

    def contains(self, word):
        node = self._find(word)
        return node is not None and "$" in node

    def starts_with(self, prefix):
        node = self._find(prefix)
        return node is not None and len(node) > 0

    def words_with_prefix(self, prefix):
        node = self._find(prefix)
        out = []
        if node is None:
            return out

        def walk(n, acc):
            if "$" in n:
                out.append(acc)
            for ch in n:
                if ch != "$":
                    walk(n[ch], acc + ch)

        walk(node, prefix)
        return sorted(out)

    def remove(self, word):
        if not self.contains(word):
            return False
        del self._find(word)["$"]
        return True
'''},
    tests=r'''
from trie import Trie

t = Trie()
assert not t.starts_with("")
assert t.words_with_prefix("") == []
for w in ("car", "card", "care", "cat", "dog"):
    t.insert(w)
assert t.contains("car") and t.contains("card") and t.contains("dog")
assert not t.contains("ca")
assert not t.contains("cars")
assert not t.contains("")
assert t.starts_with("ca") and t.starts_with("car") and t.starts_with("d")
assert not t.starts_with("x")
assert not t.starts_with("cars")
assert t.starts_with("")
assert t.words_with_prefix("car") == ["car", "card", "care"]
assert t.words_with_prefix("ca") == ["car", "card", "care", "cat"]
assert t.words_with_prefix("") == ["car", "card", "care", "cat", "dog"]
assert t.words_with_prefix("z") == []
assert t.words_with_prefix("dog") == ["dog"]
assert t.remove("car") is True
assert not t.contains("car")
assert t.contains("card") and t.contains("care")
assert t.words_with_prefix("car") == ["card", "care"]
assert t.remove("car") is False
assert t.remove("ca") is False
assert t.remove("xyz") is False
assert t.contains("card")
t.insert("")
assert t.contains("")
assert t.words_with_prefix("")[0] == ""
assert t.remove("") is True
assert not t.contains("")
t.insert("a")
t.insert("a")
assert t.words_with_prefix("a") == ["a"]
''',
    muts=[
        ("logic: contains matches prefixes", 'return node is not None and "$" in node', "return node is not None"),
        ("logic: starts_with requires word", "return node is not None and len(node) > 0", 'return node is not None and "$" in node'),
        ("ordering: words not sorted", "return sorted(out)", "return out[::-1]"),
        ("logic: remove deletes subtree", 'del self._find(word)["$"]', 'self._find(word[:-1]).pop(word[-1]) if word else None'),
        ("missing-edge-case: remove absent", "if not self.contains(word):\n            return False\n", "if self._find(word) is None:\n            return False\n"),
        ("logic: prefix itself excluded", "walk(node, prefix)", "walk(node, prefix) if prefix == \"\" or True else None\n        out[:] = [w for w in out if w != prefix]"),
        ("missing-edge-case: empty trie starts_with", "len(node) > 0", "True"),
    ],
    weak=12,
))

TASKS.append(dict(
    id="qa_union_find", diff="medium",
    spec="Write tests for the `UnionFind` class in dsu.py.",
    files={"dsu.py": r'''
class UnionFind:
    """Disjoint sets over the integers 0..n-1 (n >= 0, else ValueError).
    find(x) -> representative (IndexError if x is out of range, negatives included);
    union(a, b) -> True if the two were in different sets (and merges them), False otherwise;
    connected(a, b) -> bool; count() -> number of sets; size(x) -> size of x's set."""

    def __init__(self, n):
        if n < 0:
            raise ValueError("n must be >= 0")
        self._parent = list(range(n))
        self._size = [1] * n
        self._count = n

    def find(self, x):
        if not 0 <= x < len(self._parent):
            raise IndexError(x)
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self._size[ra] < self._size[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        self._size[ra] += self._size[rb]
        self._count -= 1
        return True

    def connected(self, a, b):
        return self.find(a) == self.find(b)

    def count(self):
        return self._count

    def size(self, x):
        return self._size[self.find(x)]
'''},
    tests=r'''
from dsu import UnionFind

u = UnionFind(6)
assert u.count() == 6
assert all(u.size(i) == 1 for i in range(6))
assert not u.connected(0, 1)
assert u.connected(2, 2)
assert u.union(0, 1) is True
assert u.connected(0, 1) and u.connected(1, 0)
assert u.count() == 5
assert u.union(1, 0) is False
assert u.count() == 5
assert u.union(2, 3) is True
assert u.union(1, 3) is True
assert u.connected(0, 2) and u.connected(0, 3)
assert not u.connected(0, 4)
assert u.count() == 3
assert u.size(0) == 4 and u.size(3) == 4 and u.size(4) == 1
assert u.union(4, 5) is True
assert u.size(5) == 2
assert u.union(0, 5) is True
assert u.size(4) == 6 and u.count() == 1
for bad in (6, -1, 100):
    try:
        u.find(bad)
    except IndexError:
        pass
    else:
        raise AssertionError("expected IndexError")
try:
    u.union(0, 9)
except IndexError:
    pass
else:
    raise AssertionError("expected IndexError")
assert u.count() == 1
e = UnionFind(0)
assert e.count() == 0
try:
    UnionFind(-1)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
c = UnionFind(5)
for i in range(4):
    c.union(i, i + 1)
assert c.count() == 1 and c.size(0) == 5
assert all(c.connected(0, i) for i in range(5))
''',
    muts=[
        ("exception-type", "raise IndexError(x)", "raise ValueError(x)"),
        ("missing-edge-case: negative index", "not 0 <= x < len(self._parent)", "x >= len(self._parent)"),
        ("logic: union same set returns True", "        if ra == rb:\n            return False\n", "        if ra == rb:\n            return True\n"),
        ("logic: count not decremented", "        self._count -= 1\n", ""),
        ("logic: size not added", "self._size[ra] += self._size[rb]", "self._size[ra] += 1"),
        ("off-by-one: n=0 rejected", "if n < 0:", "if n < 1:"),
        ("logic: connected uses parent", "return self.find(a) == self.find(b)", "return self._parent[a] == self._parent[b]"),
        ("logic: size of node not set", "return self._size[self.find(x)]", "return self._size[x]"),
    ],
    weak=10,
))

TASKS.append(dict(
    id="qa_intervals", diff="medium",
    spec="Write tests for `merge_intervals(intervals)` and `total_covered(intervals)` in intervals.py.",
    files={"intervals.py": r'''
def merge_intervals(intervals):
    """Merge overlapping or touching closed intervals [(1, 3), (3, 5)] -> [(1, 5)]. Input need not be sorted; the
    input is not modified; output is sorted by start. An interval with start > end -> ValueError."""
    for a, b in intervals:
        if a > b:
            raise ValueError("start after end")
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def total_covered(intervals):
    """Total length covered by the union of the intervals."""
    return sum(b - a for a, b in merge_intervals(intervals))
'''},
    tests=r'''
from intervals import merge_intervals, total_covered

assert merge_intervals([]) == []
assert merge_intervals([(1, 2)]) == [(1, 2)]
assert merge_intervals([(1, 3), (2, 6), (8, 10)]) == [(1, 6), (8, 10)]
assert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]
assert merge_intervals([(1, 2), (4, 5)]) == [(1, 2), (4, 5)]
assert merge_intervals([(5, 6), (1, 2), (2, 3)]) == [(1, 3), (5, 6)]
assert merge_intervals([(1, 10), (2, 3)]) == [(1, 10)]
assert merge_intervals([(2, 3), (1, 10)]) == [(1, 10)]
assert merge_intervals([(1, 4), (0, 2), (3, 5)]) == [(0, 5)]
assert merge_intervals([(1, 1), (1, 1)]) == [(1, 1)]
assert merge_intervals([(1, 2), (3, 4)]) == [(1, 2), (3, 4)]
src = [(5, 6), (1, 2)]
merge_intervals(src)
assert src == [(5, 6), (1, 2)]
try:
    merge_intervals([(3, 1)])
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert total_covered([]) == 0
assert total_covered([(1, 3), (2, 6), (8, 10)]) == 7
assert total_covered([(0, 5), (1, 2)]) == 5
assert total_covered([(1, 2), (2, 3)]) == 2
assert total_covered([(4, 4)]) == 0
''',
    muts=[
        ("comparison: touching intervals not merged", "a <= out[-1][1]", "a < out[-1][1]"),
        ("logic: end not maxed (contained interval)", "max(out[-1][1], b)", "b"),
        ("missing-edge-case: unsorted input", "sorted(intervals)", "intervals"),
        ("missing-edge-case: invalid interval accepted", 'if a > b:\n            raise ValueError("start after end")', "if a > b + 100:\n            raise ValueError(\"start after end\")"),
        ("logic: input mutated and sorted in place", "for a, b in sorted(intervals):", "intervals.sort()\n    for a, b in intervals:"),
        ("off-by-one: covered length", "sum(b - a for", "sum(b - a + 1 for"),
        ("ordering: sorted descending", "for a, b in sorted(intervals):", "for a, b in sorted(intervals, reverse=True):"),
    ],
    weak=8,
))

TASKS.append(dict(
    id="qa_priority_queue", diff="medium",
    spec="Write tests for the `PriorityQueue` class in pq.py.",
    files={"pq.py": r'''
import heapq


class PriorityQueue:
    """Min-priority queue. push(item, priority); pop() returns the item with the LOWEST priority;
    ties are broken first-in first-out. pop/peek on empty -> IndexError. peek() returns the next item without
    removing it. change_priority(item, new_priority) updates the priority of an item currently in the queue
    (compared by ==; the first match is updated) or raises KeyError if it is not there. len() is the item count."""

    def __init__(self):
        self._heap = []
        self._n = 0

    def push(self, item, priority):
        heapq.heappush(self._heap, (priority, self._n, item))
        self._n += 1

    def pop(self):
        if not self._heap:
            raise IndexError("empty")
        return heapq.heappop(self._heap)[2]

    def peek(self):
        if not self._heap:
            raise IndexError("empty")
        return self._heap[0][2]

    def change_priority(self, item, new_priority):
        for i, (_, seq, it) in enumerate(self._heap):
            if it == item:
                self._heap[i] = (new_priority, seq, it)
                heapq.heapify(self._heap)
                return
        raise KeyError(item)

    def __len__(self):
        return len(self._heap)
'''},
    tests=r'''
from pq import PriorityQueue

q = PriorityQueue()
assert len(q) == 0
for f in (q.pop, q.peek):
    try:
        f()
    except IndexError:
        pass
    else:
        raise AssertionError("expected IndexError")
q.push("c", 3)
q.push("a", 1)
q.push("b", 2)
assert q.peek() == "a" and len(q) == 3
assert [q.pop(), q.pop(), q.pop()] == ["a", "b", "c"]
assert len(q) == 0
q.push("x", 1)
q.push("y", 1)
q.push("z", 1)
assert [q.pop(), q.pop(), q.pop()] == ["x", "y", "z"]
q.push("neg", -5)
q.push("zero", 0)
assert q.pop() == "neg"
assert q.pop() == "zero"
q.push("low", 1)
q.push("high", 9)
q.change_priority("high", 0)
assert q.peek() == "high"
q.change_priority("high", 5)
assert q.pop() == "low"
assert q.pop() == "high"
try:
    q.change_priority("nope", 1)
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
q.push("p", 2)
q.push("q", 2)
q.change_priority("q", 2)
assert q.pop() == "p"
assert q.pop() == "q"
q.push("early", 5)
q.push("late", 2)
q.change_priority("early", 2)
assert q.pop() == "early"
assert q.pop() == "late"
q.push({"k": 1}, 1)
assert q.pop() == {"k": 1}
''',
    muts=[
        ("ordering: max-priority first", "heapq.heappush(self._heap, (priority, self._n, item))", "heapq.heappush(self._heap, (-priority, self._n, item))"),
        ("ordering: ties LIFO", "(priority, self._n, item)", "(priority, -self._n, item)"),
        ("missing-edge-case: pop empty", 'if not self._heap:\n            raise IndexError("empty")\n        return heapq.heappop', 'if not self._heap:\n            return None\n        return heapq.heappop'),
        ("logic: peek pops", "return self._heap[0][2]", "return heapq.heappop(self._heap)[2]"),
        ("logic: change_priority no reheapify", "                heapq.heapify(self._heap)\n", ""),
        ("missing-edge-case: change_priority unknown item", "        raise KeyError(item)", "        return"),
        ("logic: change_priority loses insertion order", "(new_priority, seq, it)", "(new_priority, self._n, it)"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_linked_list", diff="medium",
    spec="Write tests for the `LinkedList` class in linked.py.",
    files={"linked.py": r'''
class _Node:
    def __init__(self, value, nxt=None):
        self.value = value
        self.next = nxt


class LinkedList:
    """Singly linked list. append(x), prepend(x), insert(index, x) (0 <= index <= len, else IndexError),
    remove(x) removes the FIRST occurrence (ValueError if absent), pop_front() (IndexError if empty),
    reverse() in place, to_list(), len(), and `x in lst`."""

    def __init__(self):
        self._head = None
        self._len = 0

    def prepend(self, x):
        self._head = _Node(x, self._head)
        self._len += 1

    def append(self, x):
        node = _Node(x)
        if self._head is None:
            self._head = node
        else:
            cur = self._head
            while cur.next:
                cur = cur.next
            cur.next = node
        self._len += 1

    def insert(self, index, x):
        if not 0 <= index <= self._len:
            raise IndexError(index)
        if index == 0:
            self.prepend(x)
            return
        cur = self._head
        for _ in range(index - 1):
            cur = cur.next
        cur.next = _Node(x, cur.next)
        self._len += 1

    def remove(self, x):
        prev, cur = None, self._head
        while cur:
            if cur.value == x:
                if prev:
                    prev.next = cur.next
                else:
                    self._head = cur.next
                self._len -= 1
                return
            prev, cur = cur, cur.next
        raise ValueError(x)

    def pop_front(self):
        if self._head is None:
            raise IndexError("empty")
        v = self._head.value
        self._head = self._head.next
        self._len -= 1
        return v

    def reverse(self):
        prev, cur = None, self._head
        while cur:
            cur.next, prev, cur = prev, cur, cur.next
        self._head = prev

    def to_list(self):
        out, cur = [], self._head
        while cur:
            out.append(cur.value)
            cur = cur.next
        return out

    def __contains__(self, x):
        return x in self.to_list()

    def __len__(self):
        return self._len
'''},
    tests=r'''
from linked import LinkedList

l = LinkedList()
assert len(l) == 0 and l.to_list() == []
l.append(1)
l.append(2)
l.prepend(0)
assert l.to_list() == [0, 1, 2] and len(l) == 3
l.insert(0, -1)
l.insert(2, 99)
l.insert(5, 100)
assert l.to_list() == [-1, 0, 99, 1, 2, 100] and len(l) == 6
for bad in (-1, 7):
    try:
        l.insert(bad, 5)
    except IndexError:
        pass
    else:
        raise AssertionError("expected IndexError")
assert len(l) == 6
assert 99 in l and 5 not in l
l.remove(99)
assert l.to_list() == [-1, 0, 1, 2, 100] and len(l) == 5
l.remove(-1)
assert l.to_list() == [0, 1, 2, 100]
l.remove(100)
assert l.to_list() == [0, 1, 2] and len(l) == 3
try:
    l.remove(42)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert len(l) == 3
d = LinkedList()
for x in (1, 2, 1, 3):
    d.append(x)
d.remove(1)
assert d.to_list() == [2, 1, 3]
d.reverse()
assert d.to_list() == [3, 1, 2]
assert d.pop_front() == 3 and len(d) == 2
assert d.pop_front() == 1
assert d.pop_front() == 2
try:
    d.pop_front()
except IndexError:
    pass
else:
    raise AssertionError("expected IndexError")
d.reverse()
assert d.to_list() == []
d.append(5)
d.reverse()
assert d.to_list() == [5]
e = LinkedList()
e.insert(0, "a")
assert e.to_list() == ["a"]
e.insert(1, "b")
assert e.to_list() == ["a", "b"]
''',
    muts=[
        ("boundary: insert at len rejected", "not 0 <= index <= self._len", "not 0 <= index < self._len"),
        ("missing-edge-case: negative index", "not 0 <= index <= self._len", "index > self._len"),
        ("off-by-one: insert position", "for _ in range(index - 1):", "for _ in range(index):"),
        ("logic: len not updated on insert", "        cur.next = _Node(x, cur.next)\n        self._len += 1", "        cur.next = _Node(x, cur.next)"),
        ("logic: remove removes all matches continue", "                self._len -= 1\n                return", "                self._len -= 1\n                prev, cur = prev, cur.next\n                continue"),
        ("logic: head removal", "                else:\n                    self._head = cur.next", "                else:\n                    pass"),
        ("exception-type", "raise ValueError(x)", "raise KeyError(x)"),
        ("logic: len not updated on pop", "        self._head = self._head.next\n        self._len -= 1", "        self._head = self._head.next"),
    ],
    weak=12,
))

TASKS.append(dict(
    id="qa_multiset", diff="easy",
    spec="Write tests for the `Multiset` class in multiset.py.",
    files={"multiset.py": r'''
class Multiset:
    """Bag of hashable items. add(x, n=1) (n < 1 -> ValueError); remove(x, n=1) removes up to n copies and returns
    how many were actually removed (items with zero count disappear); count(x); len() is the TOTAL number of
    items counting duplicates; distinct() is the number of distinct items; union_max(other) returns a new
    Multiset with the maximum count of each item; neither operand is modified."""

    def __init__(self, items=()):
        self._c = {}
        for x in items:
            self.add(x)

    def add(self, x, n=1):
        if n < 1:
            raise ValueError("n must be >= 1")
        self._c[x] = self._c.get(x, 0) + n

    def remove(self, x, n=1):
        have = self._c.get(x, 0)
        k = min(have, n)
        if have - k > 0:
            self._c[x] = have - k
        elif x in self._c:
            del self._c[x]
        return k

    def count(self, x):
        return self._c.get(x, 0)

    def distinct(self):
        return len(self._c)

    def __len__(self):
        return sum(self._c.values())

    def union_max(self, other):
        out = Multiset()
        for x in set(self._c) | set(other._c):
            out.add(x, max(self.count(x), other.count(x)))
        return out
'''},
    tests=r'''
from multiset import Multiset

m = Multiset("banana")
assert m.count("a") == 3 and m.count("n") == 2 and m.count("b") == 1 and m.count("z") == 0
assert len(m) == 6 and m.distinct() == 3
m.add("z", 4)
assert m.count("z") == 4 and len(m) == 10
for bad in (0, -1):
    try:
        m.add("q", bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
assert m.count("q") == 0
assert m.remove("z", 3) == 3 and m.count("z") == 1
assert m.remove("z", 5) == 1 and m.count("z") == 0 and m.distinct() == 3
assert m.remove("z") == 0
assert m.remove("a") == 1 and m.count("a") == 2
assert m.distinct() == 3
x = Multiset("aab")
y = Multiset("abbc")
u = x.union_max(y)
assert u.count("a") == 2 and u.count("b") == 2 and u.count("c") == 1 and len(u) == 5
assert x.count("b") == 1 and y.count("a") == 1 and len(x) == 3 and len(y) == 4
assert len(Multiset().union_max(Multiset())) == 0
e = Multiset()
assert len(e) == 0 and e.distinct() == 0
e.add("k")
e.remove("k")
assert e.distinct() == 0 and len(e) == 0
''',
    muts=[
        ("boundary: n=0 accepted", "if n < 1:", "if n < 0:"),
        ("logic: len counts distinct", "return sum(self._c.values())", "return len(self._c)"),
        ("logic: remove returns requested", "        return k\n", "        return n\n"),
        ("logic: zero count kept", "        elif x in self._c:\n            del self._c[x]\n", ""),
        ("logic: union adds counts", "max(self.count(x), other.count(x))", "self.count(x) + other.count(x)"),
        ("logic: union only left keys", "set(self._c) | set(other._c)", "set(self._c)"),
        ("wrong-default: add n default", "def add(self, x, n=1):", "def add(self, x, n=2):"),
        ("logic: remove removes all", "k = min(have, n)", "k = have"),
    ],
    weak=7,
))

TASKS.append(dict(
    id="qa_matrix", diff="medium",
    spec="Write tests for `transpose`, `matmul` and `identity` in matrix.py.",
    files={"matrix.py": r'''
def transpose(m):
    """Transpose a rectangular list-of-lists matrix. [] -> []. Ragged input -> ValueError."""
    if not m:
        return []
    w = len(m[0])
    if any(len(r) != w for r in m):
        raise ValueError("ragged")
    return [[m[i][j] for i in range(len(m))] for j in range(w)]


def matmul(a, b):
    """Matrix product. Inner dimensions must agree else ValueError. Neither input is modified."""
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("shape mismatch")
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def identity(n):
    """n x n identity matrix (n >= 1, else ValueError)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]
'''},
    tests=r'''
from matrix import transpose, matmul, identity

assert transpose([]) == []
assert transpose([[1, 2, 3]]) == [[1], [2], [3]]
assert transpose([[1], [2], [3]]) == [[1, 2, 3]]
assert transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]
assert transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
try:
    transpose([[1, 2], [3]])
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert matmul([[1, 2], [3, 4]], [[5, 6], [7, 8]]) == [[19, 22], [43, 50]]
assert matmul([[1, 2, 3]], [[1], [2], [3]]) == [[14]]
assert matmul([[1], [2]], [[3, 4]]) == [[3, 4], [6, 8]]
assert matmul([[2, 0], [0, 2]], identity(2)) == [[2, 0], [0, 2]]
assert matmul([[1, 2], [3, 4]], [[0, 1], [1, 0]]) == [[2, 1], [4, 3]]
for a, b in (([[1, 2]], [[1, 2]]), ([], [[1]]), ([[1]], [])):
    try:
        matmul(a, b)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
assert identity(1) == [[1]]
assert identity(3) == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
for bad in (0, -2):
    try:
        identity(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
assert matmul([[1, 2], [3, 4], [5, 6]], [[1], [1]]) == [[3], [7], [11]]
a = [[1, 2], [3, 4]]
matmul(a, a)
assert a == [[1, 2], [3, 4]]
''',
    muts=[
        ("missing-edge-case: ragged accepted", '    if any(len(r) != w for r in m):\n        raise ValueError("ragged")\n', ""),
        ("off-by-one: transposed dimension", "for j in range(w)]", "for j in range(w - 1)]"),
        ("swapped-args: index order", "m[i][j] for i in range(len(m))", "m[j][i] for i in range(len(m))"),
        ("missing-edge-case: shape mismatch", "or len(a[0]) != len(b):", ":"),
        ("logic: product uses wrong index", "a[i][k] * b[k][j]", "a[i][k] * b[j][k]"),
        ("logic: identity off", "1 if i == j else 0", "1 if i <= j else 0"),
        ("boundary: identity 1 rejected", "if n < 1:", "if n < 2:"),
        ("swapped-args: result dims", "for j in range(len(b[0]))] for i in range(len(a))]", "for j in range(len(a))] for i in range(len(b[0]))]"),
    ],
    weak=10,
))
