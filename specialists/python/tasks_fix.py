"""Fix-bug tasks. `files` are buggy; reference = patches applied to them."""
from common import fix

TASKS_FIX = [
    fix("py_fix_moving_average", "easy", "lists",
        {"stats.py": r'''
def moving_average(xs, k):
    """Averages of every window of k consecutive items."""
    return [sum(xs[i:i + k]) / k for i in range(len(xs) - k)]
'''},
        [("stats.py", "range(len(xs) - k)", "range(len(xs) - k + 1)")],
        "moving_average drops the last window.",
        "from stats import moving_average\nassert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]\n",
        r'''
from stats import moving_average
assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]
assert moving_average([2, 4, 6], 3) == [4.0]
assert moving_average([5], 1) == [5.0]
assert moving_average([1, 2], 3) == []
assert moving_average([1, 2, 3, 4, 5], 1) == [1.0, 2.0, 3.0, 4.0, 5.0]
'''),
    fix("py_fix_chunk_tail", "easy", "lists",
        {"chunks.py": r'''
def chunk(items, n):
    """Split items into consecutive lists of length n; the last may be shorter."""
    if n <= 0:
        raise ValueError("n must be positive")
    return [items[i:i + n] for i in range(0, len(items) - len(items) % n, n)]
'''},
        [("chunks.py", "len(items) - len(items) % n", "len(items)")],
        "chunk loses the final short chunk.",
        "from chunks import chunk\nassert chunk([1, 2, 3], 2) == [[1, 2], [3]]\n",
        r'''
from chunks import chunk
assert chunk([1, 2, 3], 2) == [[1, 2], [3]]
assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
assert chunk([], 3) == []
assert chunk([1], 5) == [[1]]
assert chunk("abcde", 2) == ["ab", "cd", "e"]
try:
    chunk([1], 0)
    assert False
except ValueError:
    pass
'''),
    fix("py_fix_word_count_case", "easy", "strings",
        {"words.py": r'''
def word_count(text):
    """Case-insensitive word frequencies, ignoring surrounding punctuation."""
    counts = {}
    for w in text.split():
        w = w.strip(".,!?;:")
        if not w:
            continue
        counts[w] = counts.get(w, 0) + 1
    return counts
'''},
        [("words.py", 'w = w.strip(".,!?;:")', 'w = w.strip(".,!?;:").lower()')],
        "Words that differ only by case are counted separately.",
        'from words import word_count\nassert word_count("Hi hi") == {"hi": 2}\n',
        r'''
from words import word_count
assert word_count("Hi hi") == {"hi": 2}
assert word_count("The cat. the DOG! A cat?") == {"the": 2, "cat": 2, "dog": 1, "a": 1}
assert word_count("") == {}
assert word_count("... !!") == {}
'''),
    fix("py_fix_palindrome_filter", "easy", "strings",
        {"pal.py": r'''
def is_palindrome(s):
    """True if s reads the same backwards, ignoring case and any non-alphanumeric characters."""
    t = s.lower()
    return t == t[::-1]
'''},
        [("pal.py", "t = s.lower()", "t = [c for c in s.lower() if c.isalnum()]")],
        "Phrases with spaces or punctuation are rejected.",
        'from pal import is_palindrome\nassert is_palindrome("A man, a plan, a canal: Panama")\n',
        r'''
from pal import is_palindrome
assert is_palindrome("A man, a plan, a canal: Panama")
assert is_palindrome("racecar")
assert not is_palindrome("hello")
assert is_palindrome("")
assert is_palindrome("!!")
assert is_palindrome("No 'x' in Nixon")
assert not is_palindrome("ab")
'''),
    fix("py_fix_roman_subtractive", "easy", "parsing",
        {"roman.py": r'''
VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(s):
    total = 0
    for i, c in enumerate(s):
        if i + 1 < len(s) and VALUES[c] < VALUES[s[i + 1]]:
            total += VALUES[c]
        else:
            total += VALUES[c]
    return total
'''},
        [("roman.py", "            total += VALUES[c]\n        else:", "            total -= VALUES[c]\n        else:")],
        "Numerals such as IV or XC give the wrong value.",
        'from roman import roman_to_int\nassert roman_to_int("IV") == 4\n',
        r'''
from roman import roman_to_int
assert roman_to_int("IV") == 4
assert roman_to_int("XIX") == 19
assert roman_to_int("MCMXCIV") == 1994
assert roman_to_int("III") == 3
assert roman_to_int("") == 0
assert roman_to_int("CDXLIV") == 444
'''),
    fix("py_fix_bracket_empty_stack", "easy", "parsing",
        {"brackets.py": r'''
PAIRS = {")": "(", "]": "[", "}": "{"}


def balanced(s):
    """True if all (), [], {} in s are properly nested; other characters are ignored."""
    stack = []
    for c in s:
        if c in "([{":
            stack.append(c)
        elif c in PAIRS:
            if stack.pop() != PAIRS[c]:
                return False
    return not stack
'''},
        [("brackets.py", "            if stack.pop() != PAIRS[c]:", "            if not stack or stack.pop() != PAIRS[c]:")],
        "balanced(')') crashes with IndexError instead of returning False.",
        'from brackets import balanced\nassert balanced(")") is False\n',
        r'''
from brackets import balanced
assert balanced(")") is False
assert balanced("") is True
assert balanced("a(b[c]{d})e") is True
assert balanced("(]") is False
assert balanced("((") is False
assert balanced("]()") is False
assert balanced("{[()]}") is True
'''),
    fix("py_fix_rpn_operand_order", "easy", "parsing",
        {"rpn.py": r'''
def eval_rpn(tokens):
    """Evaluate a reverse Polish expression given as a list of strings."""
    st = []
    for t in tokens:
        if t in ("+", "-", "*", "/"):
            b = st.pop()
            a = st.pop()
            if t == "+":
                st.append(a + b)
            elif t == "-":
                st.append(b - a)
            elif t == "*":
                st.append(a * b)
            else:
                st.append(b / a)
        else:
            st.append(float(t))
    if len(st) != 1:
        raise ValueError("bad expression")
    return st[0]
'''},
        [("rpn.py", "st.append(b - a)", "st.append(a - b)"), ("rpn.py", "st.append(b / a)", "st.append(a / b)")],
        "Subtraction and division use the operands in the wrong order.",
        'from rpn import eval_rpn\nassert eval_rpn(["5", "3", "-"]) == 2.0\n',
        r'''
from rpn import eval_rpn
assert eval_rpn(["5", "3", "-"]) == 2.0
assert eval_rpn(["8", "2", "/"]) == 4.0
assert eval_rpn(["2", "3", "4", "*", "+"]) == 14.0
assert eval_rpn(["10", "2", "8", "*", "+", "3", "-"]) == 23.0
assert eval_rpn(["7"]) == 7.0
try:
    eval_rpn(["1", "2"])
    assert False
except ValueError:
    pass
'''),
    fix("py_fix_sieve_inclusive", "easy", "algorithms",
        {"primes.py": r'''
def primes_upto(n):
    """All primes p with p <= n, ascending."""
    if n < 2:
        return []
    sieve = [True] * n
    sieve[0] = sieve[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n, i):
                sieve[j] = False
    return [i for i, ok in enumerate(sieve) if ok]
'''},
        [("primes.py", "sieve = [True] * n", "sieve = [True] * (n + 1)"), ("primes.py", "range(i * i, n, i)", "range(i * i, n + 1, i)")],
        "primes_upto excludes n itself when n is prime.",
        "from primes import primes_upto\nassert primes_upto(7) == [2, 3, 5, 7]\n",
        r'''
from primes import primes_upto
assert primes_upto(7) == [2, 3, 5, 7]
assert primes_upto(2) == [2]
assert primes_upto(1) == []
assert primes_upto(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
assert primes_upto(25) == [2, 3, 5, 7, 11, 13, 17, 19, 23]
assert len(primes_upto(1000)) == 168
'''),
    fix("py_fix_dedupe_order", "easy", "lists",
        {"dedupe.py": r'''
def dedupe(items):
    """Remove duplicates, keeping the first occurrence of each item in original order."""
    return list(set(items))
'''},
        [("dedupe.py", "return list(set(items))", "return list(dict.fromkeys(items))")],
        "dedupe scrambles the order.",
        "from dedupe import dedupe\nassert dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]\n",
        r'''
from dedupe import dedupe
assert dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]
assert dedupe([]) == []
assert dedupe(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]
assert dedupe([9, 8, 7, 6, 5, 4]) == [9, 8, 7, 6, 5, 4]
'''),
    fix("py_fix_rotate_matrix", "easy", "matrices",
        {"rot.py": r'''
def rotate_cw(m):
    """Rotate a rectangular matrix (list of rows) 90 degrees clockwise; returns a new matrix."""
    return [list(row) for row in zip(*m)][::-1]
'''},
        [("rot.py", "return [list(row) for row in zip(*m)][::-1]", "return [list(row) for row in zip(*m[::-1])]")],
        "The matrix is rotated counter-clockwise.",
        "from rot import rotate_cw\nassert rotate_cw([[1, 2], [3, 4]]) == [[3, 1], [4, 2]]\n",
        r'''
from rot import rotate_cw
assert rotate_cw([[1, 2], [3, 4]]) == [[3, 1], [4, 2]]
assert rotate_cw([[1, 2, 3]]) == [[1], [2], [3]]
assert rotate_cw([[1], [2], [3]]) == [[3, 2, 1]]
assert rotate_cw([[1, 2, 3], [4, 5, 6]]) == [[4, 1], [5, 2], [6, 3]]
m = [[1, 2], [3, 4]]
rotate_cw(m)
assert m == [[1, 2], [3, 4]]
'''),
    fix("py_fix_merge_intervals", "medium", "intervals",
        {"intervals.py": r'''
def merge_intervals(intervals):
    """Merge overlapping or touching closed intervals; input may be unsorted. Returns a list of [start, end]."""
    out = []
    for s, e in intervals:
        if out and s <= out[-1][1]:
            out[-1][1] = e
        else:
            out.append([s, e])
    return out
'''},
        [("intervals.py", "for s, e in intervals:", "for s, e in sorted(intervals):"),
         ("intervals.py", "out[-1][1] = e", "out[-1][1] = max(out[-1][1], e)")],
        "Unsorted input is merged wrongly and a contained interval shrinks the result.",
        "from intervals import merge_intervals\nassert merge_intervals([(8, 10), (1, 3), (2, 6)]) == [[1, 6], [8, 10]]\n",
        r'''
from intervals import merge_intervals
assert merge_intervals([(8, 10), (1, 3), (2, 6)]) == [[1, 6], [8, 10]]
assert merge_intervals([(1, 10), (2, 3)]) == [[1, 10]]
assert merge_intervals([(1, 2), (2, 3)]) == [[1, 3]]
assert merge_intervals([]) == []
assert merge_intervals([(5, 6)]) == [[5, 6]]
assert merge_intervals([(1, 4), (5, 6)]) == [[1, 4], [5, 6]]
assert merge_intervals([(1, 5), (2, 3), (4, 8), (10, 11)]) == [[1, 8], [10, 11]]
'''),
    fix("py_fix_grid_bfs_bounds", "medium", "graphs",
        {"grid.py": r'''
from collections import deque


def shortest_path(grid, start, goal):
    """Fewest steps from start to goal moving up/down/left/right through cells equal to '.'; -1 if unreachable."""
    rows, cols = len(grid), len(grid[0])
    if grid[start[0]][start[1]] != "." or grid[goal[0]][goal[1]] != ".":
        return -1
    seen = {start}
    q = deque([(start, 0)])
    while q:
        (r, c), d = q.popleft()
        if (r, c) == goal:
            return d
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr <= rows and 0 <= nc <= cols and (nr, nc) not in seen and grid[nr][nc] == ".":
                seen.add((nr, nc))
                q.append(((nr, nc), d + 1))
    return -1
'''},
        [("grid.py", "0 <= nr <= rows and 0 <= nc <= cols", "0 <= nr < rows and 0 <= nc < cols")],
        "shortest_path raises IndexError on grids where a path runs along the border.",
        'from grid import shortest_path\nassert shortest_path(["..", ".."], (0, 0), (1, 1)) == 2\n',
        r'''
from grid import shortest_path
assert shortest_path(["..", ".."], (0, 0), (1, 1)) == 2
g = ["...", ".#.", "..."]
assert shortest_path(g, (0, 0), (2, 2)) == 4
assert shortest_path(["..#", "###", "..."], (0, 0), (2, 2)) == -1
assert shortest_path(["."], (0, 0), (0, 0)) == 0
assert shortest_path(["...", "#.#", "..."], (0, 0), (2, 0)) == 4
assert shortest_path(["..", ".#"], (0, 0), (1, 1)) == -1
'''),
    fix("py_fix_flatten_strings", "medium", "recursion",
        {"flat.py": r'''
def flatten(x):
    """Flatten arbitrarily nested lists/tuples into one list. Strings are leaves."""
    out = []
    for item in x:
        if hasattr(item, "__iter__"):
            out.extend(flatten(item))
        else:
            out.append(item)
    return out
'''},
        [("flat.py", 'hasattr(item, "__iter__")', "isinstance(item, (list, tuple))")],
        "flatten hits RecursionError when a string is inside the structure.",
        'from flat import flatten\nassert flatten([1, ["ab", [2]]]) == [1, "ab", 2]\n',
        r'''
from flat import flatten
assert flatten([1, ["ab", [2]]]) == [1, "ab", 2]
assert flatten([]) == []
assert flatten([[], [[]], ()]) == []
assert flatten((1, (2, (3, [4])))) == [1, 2, 3, 4]
assert flatten(["x", ["y", ["z"]]]) == ["x", "y", "z"]
assert flatten([{"a": 1}, [2]]) == [{"a": 1}, 2]
'''),
    fix("py_fix_group_by_shared", "medium", "dicts",
        {"grouping.py": r'''
def group_by(items, key):
    """Group items by key(item); each group keeps input order; groups appear in first-seen order."""
    groups = dict.fromkeys([key(i) for i in items], [])
    for i in items:
        groups[key(i)].append(i)
    return groups
'''},
        [("grouping.py", "groups = dict.fromkeys([key(i) for i in items], [])", "groups = {}"),
         ("grouping.py", "groups[key(i)].append(i)", "groups.setdefault(key(i), []).append(i)")],
        "Every group contains all the items.",
        "from grouping import group_by\nassert group_by([1, 2, 3, 4], lambda x: x % 2) == {1: [1, 3], 0: [2, 4]}\n",
        r'''
from grouping import group_by
assert group_by([1, 2, 3, 4], lambda x: x % 2) == {1: [1, 3], 0: [2, 4]}
assert list(group_by([1, 2, 3, 4], lambda x: x % 2)) == [1, 0]
assert group_by([], len) == {}
assert group_by(["a", "bb", "c", "dd", "eee"], len) == {1: ["a", "c"], 2: ["bb", "dd"], 3: ["eee"]}
'''),
    fix("py_fix_registry_default_list", "medium", "classes",
        {"registry.py": r'''
class Registry:
    def __init__(self, names=[]):
        self.names = names

    def add(self, name):
        if name not in self.names:
            self.names.append(name)
        return self

    def __len__(self):
        return len(self.names)
'''},
        [("registry.py", "def __init__(self, names=[]):\n        self.names = names", "def __init__(self, names=None):\n        self.names = list(names) if names is not None else []")],
        "Separate Registry objects share their contents.",
        'from registry import Registry\na = Registry(); b = Registry(); a.add("x")\nassert len(b) == 0\n',
        r'''
from registry import Registry
a = Registry()
b = Registry()
a.add("x").add("y")
assert len(a) == 2 and len(b) == 0
src = ["p"]
c = Registry(src)
c.add("q")
assert src == ["p"] and c.names == ["p", "q"]
c.add("q")
assert len(c) == 2
'''),
    fix("py_fix_kth_largest_stream", "medium", "heaps",
        {"kth.py": r'''
import heapq


class KthLargest:
    """Track the k-th largest value in a stream using a min-heap of the k largest values."""

    def __init__(self, k, nums=()):
        self.k = k
        self.heap = []
        for n in nums:
            self.add(n)

    def add(self, val):
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]
'''},
        [("kth.py", "        return self.heap[0]", "        return self.heap[0] if len(self.heap) == self.k else None")],
        "add() should return None until k values have been seen, but returns the minimum so far.",
        "from kth import KthLargest\nk = KthLargest(2)\nassert k.add(5) is None\n",
        r'''
from kth import KthLargest
k = KthLargest(2)
assert k.add(5) is None
assert k.add(3) == 3
assert k.add(10) == 5
assert k.add(1) == 5
assert k.add(11) == 10
k3 = KthLargest(3, [4, 5, 8, 2])
assert k3.add(3) == 4
assert k3.add(9) == 5
assert k3.add(4) == 5
k1 = KthLargest(1)
assert k1.add(2) == 2 and k1.add(1) == 2 and k1.add(7) == 7
'''),
    fix("py_fix_trie_count_delete", "hard", "tries",
        {"trie.py": r'''
class Trie:
    def __init__(self):
        self.root = {"children": {}, "count": 0, "end": False}

    def insert(self, word):
        if self.contains(word):
            return False
        node = self.root
        for ch in word:
            node = node["children"].setdefault(ch, {"children": {}, "count": 0, "end": False})
            node["count"] += 1
        node["end"] = True
        return True

    def contains(self, word):
        node = self._walk(word)
        return node is not None and node["end"]

    def count_prefix(self, prefix):
        """Number of stored words starting with prefix."""
        node = self._walk(prefix)
        return node["count"] if node is not None else 0

    def delete(self, word):
        if not self.contains(word):
            return False
        node = self.root
        for ch in word:
            node = node["children"][ch]
        node["end"] = False
        return True

    def _walk(self, s):
        node = self.root
        for ch in s:
            node = node["children"].get(ch)
            if node is None:
                return None
        return node
'''},
        [("trie.py", "        node = self.root\n        for ch in word:\n            node = node[\"children\"][ch]\n        node[\"end\"] = False",
          "        node = self.root\n        for ch in word:\n            node = node[\"children\"][ch]\n            node[\"count\"] -= 1\n        node[\"end\"] = False")],
        "count_prefix keeps counting words after they were deleted.",
        'from trie import Trie\nt = Trie(); t.insert("cat"); t.delete("cat")\nassert t.count_prefix("c") == 0\n',
        r'''
from trie import Trie
t = Trie()
for w in ["car", "cart", "care", "dog"]:
    assert t.insert(w) is True
assert t.insert("car") is False
assert t.count_prefix("car") == 3 and t.count_prefix("c") == 3
assert t.delete("cart") is True
assert t.count_prefix("car") == 2 and not t.contains("cart") and t.contains("car")
assert t.delete("cart") is False
assert t.delete("ca") is False
assert t.count_prefix("car") == 2
assert t.delete("car") is True
assert t.count_prefix("car") == 1 and t.count_prefix("ca") == 1
assert t.delete("care") and t.count_prefix("c") == 0
assert t.insert("cart") is True and t.count_prefix("c") == 1
'''),
    fix("py_fix_union_find_size", "medium", "union-find",
        {"dsu.py": r'''
class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        return True

    def component_size(self, x):
        return self.size[self.find(x)]
'''},
        [("dsu.py", "        self.parent[rb] = ra\n", "        self.parent[rb] = ra\n        self.size[ra] += self.size[rb]\n")],
        "component_size never grows after union.",
        "from dsu import DSU\nd = DSU(3); d.union(0, 1)\nassert d.component_size(1) == 2\n",
        r'''
from dsu import DSU
d = DSU(6)
assert d.component_size(0) == 1
assert d.union(0, 1) and d.union(2, 3) and d.union(1, 3)
assert not d.union(0, 2)
assert d.component_size(3) == 4 and d.component_size(0) == 4
assert d.component_size(4) == 1
d.union(4, 5)
d.union(5, 0)
assert d.component_size(4) == 6
'''),
    fix("py_fix_lcs_shared_rows", "medium", "dp",
        {"lcs.py": r'''
def lcs(a, b):
    """Longest common subsequence of a and b (one of the longest; ties resolved by preferring a's earlier chars)."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1)] * (n + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    out = []
    i, j = n, m
    while i and j:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(out))
'''},
        [("lcs.py", "dp = [[0] * (m + 1)] * (n + 1)", "dp = [[0] * (m + 1) for _ in range(n + 1)]")],
        "lcs returns garbage because the DP table rows alias each other.",
        'from lcs import lcs\nassert lcs("ABCBDAB", "BDCABA") in ("BCBA", "BDAB", "BCAB")\n',
        r'''
from lcs import lcs
def is_sub(s, t):
    it = iter(t)
    return all(c in it for c in s)


for a, b, n in [("ABCBDAB", "BDCABA", 4), ("AGGTAB", "GXTXAYB", 4), ("abc", "abc", 3), ("abc", "def", 0), ("", "abc", 0)]:
    r = lcs(a, b)
    assert len(r) == n and is_sub(r, a) and is_sub(r, b), (a, b, r)
assert len(lcs("a" * 20 + "b" * 20, "b" * 20 + "a" * 20)) == 20
'''),
    fix("py_fix_knapsack_reuse", "medium", "dp",
        {"knap.py": r'''
def knapsack(items, capacity):
    """0/1 knapsack. items = [(weight, value)]. Returns the maximum total value with total weight <= capacity."""
    best = [0] * (capacity + 1)
    for w, v in items:
        for c in range(w, capacity + 1):
            best[c] = max(best[c], best[c - w] + v)
    return best[capacity]
'''},
        [("knap.py", "for c in range(w, capacity + 1):", "for c in range(capacity, w - 1, -1):")],
        "Items get used more than once.",
        "from knap import knapsack\nassert knapsack([(2, 3)], 6) == 3\n",
        r'''
from knap import knapsack
assert knapsack([(2, 3)], 6) == 3
assert knapsack([(1, 1), (3, 4), (4, 5), (5, 7)], 7) == 9
assert knapsack([], 10) == 0
assert knapsack([(5, 10)], 4) == 0
assert knapsack([(1, 2), (1, 2), (1, 2)], 2) == 4
assert knapsack([(10, 60), (20, 100), (30, 120)], 50) == 220
'''),
    fix("py_fix_edit_distance_base", "medium", "dp",
        {"edit.py": r'''
def edit_distance(a, b):
    """Levenshtein distance (insert, delete, substitute each cost 1)."""
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[len(b)]
'''},
        [("edit.py", "prev = [0] * (len(b) + 1)", "prev = list(range(len(b) + 1))")],
        "Distance to or from an empty string, and some other pairs, are wrong.",
        'from edit import edit_distance\nassert edit_distance("", "abc") == 3\n',
        r'''
from edit import edit_distance
assert edit_distance("", "abc") == 3
assert edit_distance("abc", "") == 3
assert edit_distance("kitten", "sitting") == 3
assert edit_distance("same", "same") == 0
assert edit_distance("", "") == 0
assert edit_distance("flaw", "lawn") == 2
assert edit_distance("intention", "execution") == 5
'''),
    fix("py_fix_sliding_log_limiter", "hard", "rate-limiting",
        {"limiter.py": r'''
from collections import deque


class SlidingLogLimiter:
    """Allow at most `limit` events in any window of `window` seconds. A event at time t counts for
    times t <= now < t + window (it has expired exactly `window` seconds later)."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.events = deque()

    def allow(self, now):
        while self.events and self.events[0] < now - self.window:
            self.events.popleft()
        if len(self.events) >= self.limit:
            return False
        self.events.append(now)
        return True
'''},
        [("limiter.py", "self.events[0] < now - self.window", "self.events[0] <= now - self.window")],
        "An event is still counted exactly `window` seconds after it happened.",
        "from limiter import SlidingLogLimiter\nl = SlidingLogLimiter(1, 10)\nassert l.allow(0)\nassert l.allow(10)\n",
        r'''
from limiter import SlidingLogLimiter
l = SlidingLogLimiter(2, 10)
assert l.allow(0) and l.allow(5)
assert not l.allow(9.9)
assert l.allow(10)
assert not l.allow(14.9)
assert l.allow(15)
assert not l.allow(15.5)
l2 = SlidingLogLimiter(1, 1)
assert l2.allow(0) and not l2.allow(0.5) and l2.allow(1) and l2.allow(2)
'''),
    fix("py_fix_heap_sift_down", "hard", "heaps",
        {"minheap.py": r'''
class MinHeap:
    def __init__(self):
        self.a = []

    def push(self, x):
        a = self.a
        a.append(x)
        i = len(a) - 1
        while i > 0 and a[(i - 1) // 2] > a[i]:
            a[(i - 1) // 2], a[i] = a[i], a[(i - 1) // 2]
            i = (i - 1) // 2

    def pop(self):
        a = self.a
        if not a:
            raise IndexError("pop from empty heap")
        top = a[0]
        last = a.pop()
        if a:
            a[0] = last
            i = 0
            n = len(a)
            while True:
                l, r = 2 * i + 1, 2 * i + 2
                if l < n and a[l] < a[i]:
                    a[l], a[i] = a[i], a[l]
                    i = l
                else:
                    break
        return top

    def __len__(self):
        return len(self.a)
'''},
        [("minheap.py", "                if l < n and a[l] < a[i]:\n                    a[l], a[i] = a[i], a[l]\n                    i = l\n                else:\n                    break",
          "                m = i\n                if l < n and a[l] < a[m]:\n                    m = l\n                if r < n and a[r] < a[m]:\n                    m = r\n                if m == i:\n                    break\n                a[m], a[i] = a[i], a[m]\n                i = m")],
        "Popping repeatedly does not return sorted order.",
        "from minheap import MinHeap\nh = MinHeap()\nfor x in [1, 3, 2, 4]:\n    h.push(x)\nassert [h.pop() for _ in range(4)] == [1, 2, 3, 4]\n",
        r'''
from minheap import MinHeap
import random
h = MinHeap()
for x in [5, 1, 4, 2, 3]:
    h.push(x)
assert [h.pop() for _ in range(5)] == [1, 2, 3, 4, 5]
random.seed(7)
xs = [random.randint(0, 50) for _ in range(200)]
h = MinHeap()
for x in xs:
    h.push(x)
assert len(h) == 200
assert [h.pop() for _ in range(200)] == sorted(xs)
try:
    h.pop()
    assert False
except IndexError:
    pass
h.push(3); h.push(1); h.push(2)
assert h.pop() == 1
h.push(0)
assert h.pop() == 0 and h.pop() == 2 and h.pop() == 3
'''),
    fix("py_fix_max_nonoverlap", "medium", "intervals",
        {"sched.py": r'''
def max_meetings(meetings):
    """Max number of non-overlapping meetings (start, end); a meeting may start exactly when another ends."""
    count = 0
    last_end = None
    for s, e in sorted(meetings):
        if last_end is None or s >= last_end:
            count += 1
            last_end = e
    return count
'''},
        [("sched.py", "for s, e in sorted(meetings):", "for s, e in sorted(meetings, key=lambda m: (m[1], m[0])):")],
        "Greedy choice is wrong: a long early meeting blocks many short ones.",
        "from sched import max_meetings\nassert max_meetings([(1, 10), (2, 3), (4, 5)]) == 2\n",
        r'''
from sched import max_meetings
assert max_meetings([(1, 10), (2, 3), (4, 5)]) == 2
assert max_meetings([]) == 0
assert max_meetings([(1, 2), (2, 3), (3, 4)]) == 3
assert max_meetings([(1, 5), (2, 6), (3, 7)]) == 1
assert max_meetings([(0, 6), (1, 4), (3, 5), (3, 8), (4, 7), (5, 9), (5, 9), (6, 10), (8, 11)]) == 3
'''),
    fix("py_fix_parse_bool_setting", "medium", "config",
        {"conf.py": r'''
def parse_value(raw, kind):
    """Convert a raw string setting to int, float, bool or str."""
    if kind == "int":
        return int(raw)
    if kind == "float":
        return float(raw)
    if kind == "bool":
        return bool(raw)
    return raw
''', "settings.py": r'''
from conf import parse_value

SCHEMA = {"port": "int", "debug": "bool", "ratio": "float", "name": "str"}


def load(raw):
    """raw: dict of str -> str. Returns typed settings for the keys in SCHEMA; unknown keys raise KeyError."""
    return {k: parse_value(v, SCHEMA[k]) for k, v in raw.items()}
'''},
        [("conf.py", "        return bool(raw)", '        low = raw.strip().lower()\n        if low in ("1", "true", "yes", "on"):\n            return True\n        if low in ("0", "false", "no", "off", ""):\n            return False\n        raise ValueError(raw)')],
        'The string "false" is loaded as True.',
        'from settings import load\nassert load({"debug": "false"}) == {"debug": False}\n',
        r'''
from settings import load
assert load({"debug": "false"}) == {"debug": False}
assert load({"debug": "True", "port": "80"}) == {"debug": True, "port": 80}
assert load({"debug": " ON "})["debug"] is True
assert load({"debug": "0"})["debug"] is False
assert load({"ratio": "0.5", "name": "x"}) == {"ratio": 0.5, "name": "x"}
for bad in [{"debug": "maybe"}, {"port": "x"}]:
    try:
        load(bad)
        assert False
    except ValueError:
        pass
try:
    load({"nope": "1"})
    assert False
except KeyError:
    pass
'''),
    fix("py_fix_version_compare", "medium", "strings",
        {"version.py": r'''
def compare_versions(a, b):
    """Compare dotted numeric versions. Returns -1, 0 or 1. Missing parts count as 0 ("1.0" == "1")."""
    pa, pb = a.split("."), b.split(".")
    n = max(len(pa), len(pb))
    pa += ["0"] * (n - len(pa))
    pb += ["0"] * (n - len(pb))
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0
'''},
        [("version.py", "    pa, pb = a.split(\".\"), b.split(\".\")", "    pa, pb = [int(x) for x in a.split(\".\")], [int(x) for x in b.split(\".\")]"),
         ("version.py", 'pa += ["0"] * (n - len(pa))', "pa += [0] * (n - len(pa))"),
         ("version.py", 'pb += ["0"] * (n - len(pb))', "pb += [0] * (n - len(pb))")],
        '"1.10" compares lower than "1.9".',
        'from version import compare_versions\nassert compare_versions("1.10", "1.9") == 1\n',
        r'''
from version import compare_versions as c
assert c("1.10", "1.9") == 1
assert c("1.0", "1") == 0
assert c("2.0.1", "2.0.10") == -1
assert c("0.9", "0.9.0.0") == 0
assert c("3", "2.99.99") == 1
assert c("1.2.3", "1.2.3") == 0
'''),
    fix("py_fix_lower_bound_loop", "medium", "binary-search",
        {"bs.py": r'''
def lower_bound(a, x):
    """Index of the first element >= x in sorted list a (len(a) if none)."""
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid
        else:
            hi = mid
    return lo
'''},
        [("bs.py", "            lo = mid\n", "            lo = mid + 1\n")],
        "lower_bound loops forever on some inputs.",
        "from bs import lower_bound\nassert lower_bound([1, 3, 5], 4) == 2\n",
        r'''
from bs import lower_bound
assert lower_bound([1, 3, 5], 4) == 2
assert lower_bound([1, 3, 5], 0) == 0
assert lower_bound([1, 3, 5], 6) == 3
assert lower_bound([], 1) == 0
assert lower_bound([1, 2, 2, 2, 3], 2) == 1
assert lower_bound([1, 2, 2, 2, 3], 3) == 4
'''),
    fix("py_fix_stock_oversell", "medium", "state",
        {"stock.py": r'''
class Stock:
    def __init__(self, levels):
        self.levels = dict(levels)

    def available(self, sku):
        return self.levels.get(sku, 0)
''', "orders.py": r'''
from stock import Stock


def place_order(stock, lines):
    """lines: list of (sku, qty). All-or-nothing: if any sku lacks stock (counting repeated skus together),
    raise ValueError and change nothing. Otherwise decrement stock. Returns total units ordered."""
    for sku, qty in lines:
        if stock.available(sku) < qty:
            raise ValueError("insufficient stock for " + sku)
    for sku, qty in lines:
        stock.levels[sku] = stock.available(sku) - qty
    return sum(q for _, q in lines)
'''},
        [("orders.py", "    for sku, qty in lines:\n        if stock.available(sku) < qty:\n            raise ValueError(\"insufficient stock for \" + sku)\n",
          "    need = {}\n    for sku, qty in lines:\n        need[sku] = need.get(sku, 0) + qty\n    for sku, qty in need.items():\n        if stock.available(sku) < qty:\n            raise ValueError(\"insufficient stock for \" + sku)\n")],
        "An order with the same sku on two lines can drive stock negative.",
        'from stock import Stock\nfrom orders import place_order\ns = Stock({"a": 3})\ntry:\n    place_order(s, [("a", 2), ("a", 2)])\n    assert False\nexcept ValueError:\n    assert s.available("a") == 3\n',
        r'''
from stock import Stock
from orders import place_order
s = Stock({"a": 3, "b": 1})
try:
    place_order(s, [("a", 2), ("a", 2)])
    assert False
except ValueError:
    assert s.available("a") == 3
assert place_order(s, [("a", 1), ("a", 2), ("b", 1)]) == 4
assert s.available("a") == 0 and s.available("b") == 0
try:
    place_order(s, [("zzz", 1)])
    assert False
except ValueError:
    pass
assert place_order(s, []) == 0
'''),
    fix("py_fix_rle_multidigit", "medium", "parsing",
        {"rle.py": r'''
def rle_decode(s):
    """Decode run-length text like '3a2b' -> 'aaabb'. Counts may have several digits ('12x'). A letter without a count appears once."""
    out = []
    i = 0
    while i < len(s):
        if s[i].isdigit():
            n = int(s[i])
            i += 1
        else:
            n = 1
        out.append(s[i] * n)
        i += 1
    return "".join(out)
'''},
        [("rle.py", "        if s[i].isdigit():\n            n = int(s[i])\n            i += 1\n",
          "        if s[i].isdigit():\n            j = i\n            while s[j].isdigit():\n                j += 1\n            n = int(s[i:j])\n            i = j\n")],
        "'12x' decodes to the wrong output.",
        'from rle import rle_decode\nassert rle_decode("12x") == "x" * 12\n',
        r'''
from rle import rle_decode
assert rle_decode("12x") == "x" * 12
assert rle_decode("3a2b") == "aaabb"
assert rle_decode("a") == "a"
assert rle_decode("") == ""
assert rle_decode("ab3c") == "abccc"
assert rle_decode("10a1b") == "aaaaaaaaaab"
'''),
    fix("py_fix_min_path_sum_edges", "medium", "dp",
        {"pathsum.py": r'''
def min_path_sum(grid):
    """Minimum sum path from top-left to bottom-right moving only right or down."""
    rows, cols = len(grid), len(grid[0])
    dp = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            best = min(dp[r - 1][c] if r else 0, dp[r][c - 1] if c else 0)
            dp[r][c] = grid[r][c] + best
    return dp[-1][-1]
'''},
        [("pathsum.py", "            best = min(dp[r - 1][c] if r else 0, dp[r][c - 1] if c else 0)",
          "            options = []\n            if r:\n                options.append(dp[r - 1][c])\n            if c:\n                options.append(dp[r][c - 1])\n            best = min(options) if options else 0")],
        "First row and first column are treated as free to enter from nowhere, giving too small sums.",
        "from pathsum import min_path_sum\nassert min_path_sum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7\n",
        r'''
from pathsum import min_path_sum
assert min_path_sum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
assert min_path_sum([[5]]) == 5
assert min_path_sum([[1, 2, 3]]) == 6
assert min_path_sum([[1], [2], [3]]) == 6
assert min_path_sum([[9, 1, 1], [9, 9, 1], [9, 9, 1]]) == 13
assert min_path_sum([[1, 2], [1, 1]]) == 3
'''),
    fix("py_fix_event_order", "medium", "scheduling",
        {"event.py": r'''
class Event:
    def __init__(self, time, priority, name):
        self.time, self.priority, self.name = time, priority, name
''', "equeue.py": r'''
import heapq
import itertools


class EventQueue:
    """Pop events by earliest time; ties by LOWER priority number first; remaining ties in insertion order."""

    def __init__(self):
        self._h = []
        self._n = itertools.count()

    def push(self, ev):
        heapq.heappush(self._h, (ev.time, -ev.priority, next(self._n), ev))

    def pop(self):
        return heapq.heappop(self._h)[-1]

    def __len__(self):
        return len(self._h)
'''},
        [("equeue.py", "(ev.time, -ev.priority, next(self._n), ev)", "(ev.time, ev.priority, next(self._n), ev)")],
        "Among events at the same time, the higher priority number runs first.",
        'from event import Event\nfrom equeue import EventQueue\nq = EventQueue(); q.push(Event(1, 5, "b")); q.push(Event(1, 1, "a"))\nassert q.pop().name == "a"\n',
        r'''
from event import Event
from equeue import EventQueue
q = EventQueue()
for t, p, n in [(2, 1, "x"), (1, 5, "b"), (1, 1, "a"), (1, 1, "a2"), (3, 0, "z")]:
    q.push(Event(t, p, n))
assert len(q) == 5
assert [q.pop().name for _ in range(5)] == ["a", "a2", "b", "x", "z"]
'''),
    fix("py_fix_normalize_path", "medium", "strings",
        {"paths.py": r'''
def normalize(path):
    """Normalize an absolute POSIX path: collapse //, resolve . and .. ('..' at root stays at root). No trailing slash except root."""
    parts = []
    for p in path.split("/"):
        if p in ("", "."):
            continue
        if p == "..":
            parts.pop()
        else:
            parts.append(p)
    return "/" + "/".join(parts)
'''},
        [("paths.py", "            parts.pop()", "            if parts:\n                parts.pop()")],
        "normalize('/..') raises IndexError.",
        'from paths import normalize\nassert normalize("/../a") == "/a"\n',
        r'''
from paths import normalize
assert normalize("/../a") == "/a"
assert normalize("/a/./b/../c/") == "/a/c"
assert normalize("//a///b") == "/a/b"
assert normalize("/") == "/"
assert normalize("/a/b/../../..") == "/"
assert normalize("/a/../../b") == "/b"
'''),
    fix("py_fix_next_permutation", "hard", "algorithms",
        {"perm.py": r'''
def next_permutation(a):
    """Rearrange list a in place into the next lexicographically greater permutation.
    Returns True on success; if a is the last permutation, reverse it to the first and return False."""
    i = len(a) - 2
    while i >= 0 and a[i] > a[i + 1]:
        i -= 1
    if i < 0:
        a.reverse()
        return False
    j = len(a) - 1
    while a[j] <= a[i]:
        j -= 1
    a[i], a[j] = a[j], a[i]
    a[i + 1:] = a[i + 1:][::-1]
    return True
'''},
        [("perm.py", "a[i] > a[i + 1]", "a[i] >= a[i + 1]")],
        "Lists with repeated values are not advanced correctly.",
        "from perm import next_permutation\na = [1, 2, 2]\nnext_permutation(a)\nassert a == [2, 1, 2]\n",
        r'''
from perm import next_permutation
a = [1, 2, 3]
assert next_permutation(a) and a == [1, 3, 2]
a = [3, 2, 1]
assert next_permutation(a) is False and a == [1, 2, 3]
a = [1, 1, 5]
assert next_permutation(a) and a == [1, 5, 1]
a = [1, 3, 2, 2]
assert next_permutation(a) and a == [2, 1, 2, 3]
a = []
assert next_permutation(a) is False
seen = [1, 2, 2, 3]
n = 1
while next_permutation(seen):
    n += 1
assert n == 12 and seen == [1, 2, 2, 3]
'''),
    fix("py_fix_running_median", "hard", "heaps",
        {"median.py": r'''
import heapq


class RunningMedian:
    """lo is a max-heap (stored negated) with the smaller half; hi is a min-heap with the larger half.
    len(lo) is either len(hi) or len(hi) + 1."""

    def __init__(self):
        self.lo = []
        self.hi = []

    def add(self, x):
        if self.lo and x > -self.lo[0]:
            heapq.heappush(self.hi, x)
        else:
            heapq.heappush(self.lo, -x)
        if len(self.lo) > len(self.hi) + 1:
            heapq.heappush(self.hi, -heapq.heappop(self.lo))

    def median(self):
        if not self.lo:
            raise ValueError("empty")
        if len(self.lo) > len(self.hi):
            return float(-self.lo[0])
        return (-self.lo[0] + self.hi[0]) / 2
'''},
        [("median.py", "            heapq.heappush(self.hi, -heapq.heappop(self.lo))\n",
          "            heapq.heappush(self.hi, -heapq.heappop(self.lo))\n        elif len(self.hi) > len(self.lo):\n            heapq.heappush(self.lo, -heapq.heappop(self.hi))\n")],
        "median() is wrong after a run of large values.",
        "from median import RunningMedian\nm = RunningMedian()\nfor x in [1, 2, 3]:\n    m.add(x)\nassert m.median() == 2.0\n",
        r'''
from median import RunningMedian
m = RunningMedian()
try:
    m.median()
    assert False
except ValueError:
    pass
for x, want in [(1, 1.0), (2, 1.5), (3, 2.0), (4, 2.5), (5, 3.0), (6, 3.5)]:
    m.add(x)
    assert m.median() == want, (x, m.median())
m = RunningMedian()
for x, want in [(5, 5.0), (1, 3.0), (9, 5.0), (0, 3.0), (-4, 1.0)]:
    m.add(x)
    assert m.median() == want, (x, m.median())
import random
random.seed(3)
m = RunningMedian()
xs = []
for _ in range(100):
    v = random.randint(-20, 20)
    xs.append(v)
    m.add(v)
    s = sorted(xs)
    n = len(s)
    want = float(s[n // 2]) if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    assert m.median() == want
'''),
]
