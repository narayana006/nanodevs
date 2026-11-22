"""20 hand-written Python bug-fix tasks for the phase 0 model comparison.

Each task has a correct version, a version with one injected bug, and plain-assert tests.
The correct version is used only to check that the tests are valid (it must pass,
the buggy version must fail). Models never see the correct version.
"""

TASKS = [
    dict(
        id="fizzbuzz",
        correct='''
def fizzbuzz(n):
    out = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            out.append("FizzBuzz")
        elif i % 3 == 0:
            out.append("Fizz")
        elif i % 5 == 0:
            out.append("Buzz")
        else:
            out.append(str(i))
    return out
''',
        buggy='''
def fizzbuzz(n):
    out = []
    for i in range(1, n + 1):
        if i % 3 == 0:
            out.append("Fizz")
        elif i % 5 == 0:
            out.append("Buzz")
        elif i % 15 == 0:
            out.append("FizzBuzz")
        else:
            out.append(str(i))
    return out
''',
        tests='''
assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]
assert fizzbuzz(15)[-1] == "FizzBuzz"
assert fizzbuzz(0) == []
''',
    ),
    dict(
        id="is_palindrome",
        correct='''
def is_palindrome(s):
    chars = [c.lower() for c in s if c.isalnum()]
    return chars == chars[::-1]
''',
        buggy='''
def is_palindrome(s):
    chars = [c for c in s if c.isalnum()]
    return chars == chars[::-1]
''',
        tests='''
assert is_palindrome("A man, a plan, a canal: Panama") is True
assert is_palindrome("race a car") is False
assert is_palindrome("") is True
assert is_palindrome("No lemon, no melon") is True
''',
    ),
    dict(
        id="binary_search",
        correct='''
def binary_search(arr, x):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == x:
            return mid
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
''',
        buggy='''
def binary_search(arr, x):
    lo, hi = 0, len(arr) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] == x:
            return mid
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
''',
        tests='''
assert binary_search([1, 3, 5, 7], 7) == 3
assert binary_search([1, 3, 5, 7], 1) == 0
assert binary_search([5], 5) == 0
assert binary_search([], 3) == -1
assert binary_search([1, 3, 5, 7], 4) == -1
''',
    ),
    dict(
        id="flatten",
        correct='''
def flatten(items):
    out = []
    for x in items:
        if isinstance(x, list):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out
''',
        buggy='''
def flatten(items):
    out = []
    for x in items:
        if isinstance(x, list):
            out.extend(x)
        else:
            out.append(x)
    return out
''',
        tests='''
assert flatten([1, [2, [3, [4]]], 5]) == [1, 2, 3, 4, 5]
assert flatten([]) == []
assert flatten([[], [[]]]) == []
''',
    ),
    dict(
        id="merge_sorted",
        correct='''
def merge_sorted(a, b):
    out = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out
''',
        buggy='''
def merge_sorted(a, b):
    out = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    out.extend(a[i:])
    return out
''',
        tests='''
assert merge_sorted([1, 4], [2, 3, 9, 10]) == [1, 2, 3, 4, 9, 10]
assert merge_sorted([], [1]) == [1]
assert merge_sorted([1, 2], []) == [1, 2]
''',
    ),
    dict(
        id="moving_average",
        correct='''
def moving_average(xs, k):
    return [sum(xs[i:i + k]) / k for i in range(len(xs) - k + 1)]
''',
        buggy='''
def moving_average(xs, k):
    return [sum(xs[i:i + k]) / k for i in range(len(xs) - k)]
''',
        tests='''
assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]
assert moving_average([1, 2, 3], 3) == [2.0]
assert moving_average([1, 2], 3) == []
''',
    ),
    dict(
        id="word_count",
        correct='''
def word_count(text):
    counts = {}
    for w in text.lower().split():
        w = w.strip(".,!?;:")
        if w:
            counts[w] = counts.get(w, 0) + 1
    return counts
''',
        buggy='''
def word_count(text):
    counts = {}
    for w in text.lower().split(" "):
        w = w.strip(".,!?;:")
        counts[w] = counts.get(w, 0) + 1
    return counts
''',
        tests='''
assert word_count("The cat. the  dog!") == {"the": 2, "cat": 1, "dog": 1}
assert word_count("") == {}
assert word_count("a a a") == {"a": 3}
''',
    ),
    dict(
        id="max_subarray",
        correct='''
def max_subarray(nums):
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best
''',
        buggy='''
def max_subarray(nums):
    best = cur = 0
    for x in nums:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best
''',
        tests='''
assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
assert max_subarray([-3, -1, -2]) == -1
assert max_subarray([5]) == 5
''',
    ),
    dict(
        id="chunk",
        correct='''
def chunk(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]
''',
        buggy='''
def chunk(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst) - n + 1, n)]
''',
        tests='''
assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
assert chunk([], 3) == []
assert chunk([1], 3) == [[1]]
''',
    ),
    dict(
        id="roman_to_int",
        correct='''
def roman_to_int(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, ch in enumerate(s):
        v = vals[ch]
        if i + 1 < len(s) and vals[s[i + 1]] > v:
            total -= v
        else:
            total += v
    return total
''',
        buggy='''
def roman_to_int(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for ch in s:
        total += vals[ch]
    return total
''',
        tests='''
assert roman_to_int("III") == 3
assert roman_to_int("IV") == 4
assert roman_to_int("IX") == 9
assert roman_to_int("LVIII") == 58
assert roman_to_int("MCMXCIV") == 1994
''',
    ),
    dict(
        id="dedupe_keep_order",
        correct='''
def dedupe_keep_order(items):
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
''',
        buggy='''
def dedupe_keep_order(items):
    return list(set(items))
''',
        tests='''
assert dedupe_keep_order([3, 1, 3, 2]) == [3, 1, 2]
assert dedupe_keep_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]
assert dedupe_keep_order([]) == []
''',
    ),
    dict(
        id="gcd",
        correct='''
def gcd(a, b):
    while b:
        a, b = b, a % b
    return abs(a)
''',
        buggy='''
def gcd(a, b):
    while b:
        a, b = b, a % b
    return abs(b)
''',
        tests='''
assert gcd(12, 18) == 6
assert gcd(7, 0) == 7
assert gcd(0, 5) == 5
assert gcd(-4, 6) == 2
''',
    ),
    dict(
        id="rotate_left",
        correct='''
def rotate_left(lst, k):
    if not lst:
        return []
    k %= len(lst)
    return lst[k:] + lst[:k]
''',
        buggy='''
def rotate_left(lst, k):
    if not lst:
        return []
    return lst[k:] + lst[:k]
''',
        tests='''
assert rotate_left([1, 2, 3, 4], 1) == [2, 3, 4, 1]
assert rotate_left([1, 2, 3], 4) == [2, 3, 1]
assert rotate_left([], 3) == []
assert rotate_left([1, 2, 3], 0) == [1, 2, 3]
''',
    ),
    dict(
        id="parse_kv",
        correct='''
def parse_kv(s):
    out = {}
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = int(v.strip())
    return out
''',
        buggy='''
def parse_kv(s):
    out = {}
    for part in s.split(";"):
        k, v = part.split("=")
        out[k] = int(v)
    return out
''',
        tests='''
assert parse_kv("a=1;b=2") == {"a": 1, "b": 2}
assert parse_kv(" a = 1 ; b=2;") == {"a": 1, "b": 2}
assert parse_kv("") == {}
''',
    ),
    dict(
        id="balanced",
        correct='''
def balanced(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack
''',
        buggy='''
def balanced(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack:
                return False
            stack.pop()
    return True
''',
        tests='''
assert balanced("([]{})") is True
assert balanced("(]") is False
assert balanced("((") is False
assert balanced("a(b)c") is True
assert balanced(")(") is False
''',
    ),
    dict(
        id="top_k",
        correct='''
def top_k(nums, k):
    return sorted(nums, reverse=True)[:k]
''',
        buggy='''
def top_k(nums, k):
    return sorted(nums)[:k]
''',
        tests='''
assert top_k([5, 1, 9, 3], 2) == [9, 5]
assert top_k([1], 3) == [1]
assert top_k([], 2) == []
''',
    ),
    dict(
        id="transpose",
        correct='''
def transpose(m):
    return [list(row) for row in zip(*m)] if m else []
''',
        buggy='''
def transpose(m):
    return [[m[i][j] for i in range(len(m))] for j in range(len(m))]
''',
        tests='''
assert transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]
assert transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
assert transpose([]) == []
''',
    ),
    dict(
        id="compound_interest",
        correct='''
def compound_interest(p, r, n, t):
    return p * (1 + r / n) ** (n * t)
''',
        buggy='''
def compound_interest(p, r, n, t):
    return p * (1 + r) ** (n * t)
''',
        tests='''
assert abs(compound_interest(1000, 0.05, 12, 1) - 1051.1618978) < 1e-3
assert abs(compound_interest(100, 0.1, 1, 2) - 121.0) < 1e-9
assert compound_interest(500, 0.0, 4, 10) == 500
''',
    ),
    dict(
        id="min_stack",
        correct='''
class MinStack:
    def __init__(self):
        self._s = []
        self._m = []

    def push(self, x):
        self._s.append(x)
        self._m.append(x if not self._m else min(x, self._m[-1]))

    def pop(self):
        self._m.pop()
        return self._s.pop()

    def min(self):
        return self._m[-1]
''',
        buggy='''
class MinStack:
    def __init__(self):
        self._s = []
        self._m = []

    def push(self, x):
        self._s.append(x)
        self._m.append(x if not self._m else min(x, self._m[-1]))

    def pop(self):
        return self._s.pop()

    def min(self):
        return self._m[-1]
''',
        tests='''
s = MinStack()
s.push(3)
s.push(1)
s.push(2)
assert s.min() == 1
assert s.pop() == 2
assert s.min() == 1
assert s.pop() == 1
assert s.min() == 3
try:
    MinStack().pop()
    raise AssertionError("pop on empty must raise IndexError")
except IndexError:
    pass
''',
    ),
    dict(
        id="merge_intervals",
        correct='''
def merge_intervals(iv):
    out = []
    for s, e in sorted(iv):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
''',
        buggy='''
def merge_intervals(iv):
    out = []
    for s, e in sorted(iv):
        if out and s < out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
''',
        tests='''
assert merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]]
assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]
assert merge_intervals([[5, 6], [1, 2]]) == [[1, 2], [5, 6]]
assert merge_intervals([]) == []
''',
    ),
]
