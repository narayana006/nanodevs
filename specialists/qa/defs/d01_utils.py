TASKS = []

TASKS.append(dict(
    id="qa_chunk_list", diff="easy",
    spec="Write tests for `chunk(items, size)` and `flatten(nested)` in listutil.py.",
    files={"listutil.py": r'''
def chunk(items, size):
    """Split items into consecutive lists of length size; the last may be shorter. size < 1 -> ValueError."""
    if size < 1:
        raise ValueError("size must be >= 1")
    return [list(items[i:i + size]) for i in range(0, len(items), size)]


def flatten(nested):
    """Flatten one level of nesting: [[1, 2], [3]] -> [1, 2, 3]. Non-list elements are kept as is."""
    out = []
    for x in nested:
        if isinstance(x, list):
            out.extend(x)
        else:
            out.append(x)
    return out
'''},
    tests=r'''
from listutil import chunk, flatten

assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
assert chunk([], 3) == []
assert chunk([1, 2], 5) == [[1, 2]]
assert chunk([1, 2, 3], 1) == [[1], [2], [3]]
assert chunk("abcd", 3) == [["a", "b", "c"], ["d"]]
for bad in (0, -1):
    try:
        chunk([1], bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

assert flatten([[1, 2], [3]]) == [1, 2, 3]
assert flatten([1, [2, 3], 4]) == [1, 2, 3, 4]
assert flatten([]) == []
assert flatten([[1, [2]], 3]) == [1, [2], 3]
assert flatten([[], []]) == []
''',
    muts=[
        ("off-by-one: last partial chunk dropped", "range(0, len(items), size)", "range(0, len(items) - size + 1, size)"),
        ("boundary: size 1 rejected", "if size < 1:", "if size < 2:"),
        ("exception-type", 'raise ValueError("size must be >= 1")', 'raise TypeError("size must be >= 1")'),
        ("missing-edge-case: negative size not rejected", "if size < 1:", "if size == 0:"),
        ("logic: flatten recurses all levels", "out.extend(x)", "out.extend(flatten(x))"),
        ("logic: non-list elements dropped", "        else:\n            out.append(x)\n", ""),
    ],
    weak=5, regress=[dict(mut=1, report="chunk([1, 2, 3, 4, 5], 2) returns [[1, 2], [3, 4]]: the trailing partial chunk [5] is lost.", test="from listutil import chunk\nassert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]\n")],
))

TASKS.append(dict(
    id="qa_roman", diff="medium",
    spec="Write tests for `to_roman(n)` and `from_roman(s)` in roman.py.",
    files={"roman.py": r'''
VALUES = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def to_roman(n):
    """Integer 1..3999 -> Roman numeral. Out of range -> ValueError."""
    if not 1 <= n <= 3999:
        raise ValueError("out of range")
    out = []
    for v, s in VALUES:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def from_roman(s):
    """Roman numeral (upper case, subtractive notation) -> int. Invalid input -> ValueError."""
    if not s or any(c not in "IVXLCDM" for c in s):
        raise ValueError("invalid roman numeral")
    total = 0
    prev = 0
    for c in reversed(s):
        v = dict((b, a) for a, b in VALUES)[c]
        if v < prev:
            total -= v
        else:
            total += v
            prev = v
    return total
'''},
    tests=r'''
from roman import to_roman, from_roman

assert to_roman(1) == "I"
assert to_roman(4) == "IV"
assert to_roman(9) == "IX"
assert to_roman(14) == "XIV"
assert to_roman(40) == "XL"
assert to_roman(90) == "XC"
assert to_roman(400) == "CD"
assert to_roman(900) == "CM"
assert to_roman(1994) == "MCMXCIV"
assert to_roman(3999) == "MMMCMXCIX"
assert to_roman(2024) == "MMXXIV"
for bad in (0, -5, 4000):
    try:
        to_roman(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

assert from_roman("I") == 1
assert from_roman("IV") == 4
assert from_roman("XIV") == 14
assert from_roman("MCMXCIV") == 1994
assert from_roman("MMMCMXCIX") == 3999
assert from_roman("XL") == 40
assert from_roman("VI") == 6
for n in (1, 3, 8, 49, 99, 444, 1666, 3888):
    assert from_roman(to_roman(n)) == n
for bad in ("", "ABC", "iv"):
    try:
        from_roman(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("boundary: 3999 rejected", "if not 1 <= n <= 3999:", "if not 1 <= n < 3999:"),
        ("boundary: 0 accepted", "if not 1 <= n <= 3999:", "if not 0 <= n <= 3999:"),
        ("missing-edge-case: 4000 accepted", "if not 1 <= n <= 3999:", "if not 1 <= n:"),
        ("logic: subtractive 900 missing", '(900, "CM"), ', ""),
        ("logic: subtractive 4 missing", '(4, "IV"), ', ""),
        ("comparison: subtract on equal", "if v < prev:", "if v <= prev:"),
        ("empty-input: empty string accepted", "if not s or any", "if any"),
        ("exception-type", 'raise ValueError("invalid roman numeral")', 'raise KeyError("invalid roman numeral")'),
    ],
    weak=5, regress=[dict(mut=6, report="from_roman('XX') returns 0 instead of 20 (equal adjacent symbols cancel each other).", test="from roman import from_roman\nassert from_roman('XX') == 20\nassert from_roman('II') == 2\n")],
))

TASKS.append(dict(
    id="qa_slugify", diff="medium",
    spec="Write tests for `slugify(text, max_len=None)` in slug.py.",
    files={"slug.py": r'''
import re


def slugify(text, max_len=None):
    """Lower-case, replace every run of non-alphanumeric ASCII characters with a single '-',
    strip leading/trailing '-'. If max_len is given, truncate to max_len characters and strip a
    trailing '-' again. max_len < 1 -> ValueError."""
    if max_len is not None and max_len < 1:
        raise ValueError("max_len must be >= 1")
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if max_len is not None:
        s = s[:max_len].rstrip("-")
    return s
'''},
    tests=r'''
from slug import slugify

assert slugify("Hello World") == "hello-world"
assert slugify("  Hello   World  ") == "hello-world"
assert slugify("a--b__c") == "a-b-c"
assert slugify("Rock & Roll!") == "rock-roll"
assert slugify("") == ""
assert slugify("!!!") == ""
assert slugify("ABC123") == "abc123"
assert slugify("hello world", max_len=5) == "hello"
assert slugify("hello world", max_len=6) == "hello"
assert slugify("hello world", max_len=7) == "hello-w"
assert slugify("abc", max_len=10) == "abc"
assert slugify("abc", max_len=3) == "abc"
assert slugify("abc", max_len=1) == "a"
for bad in (0, -2):
    try:
        slugify("abc", max_len=bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("logic: runs not collapsed", '[^a-z0-9]+', '[^a-z0-9]'),
        ("missing-edge-case: no strip", '.strip("-")\n    if max', '\n    if max'),
        ("missing-edge-case: trailing dash after truncation", "s[:max_len].rstrip(\"-\")", "s[:max_len]"),
        ("off-by-one: truncation", "s[:max_len]", "s[:max_len - 1]"),
        ("boundary: max_len 1 rejected", "if max_len is not None and max_len < 1:", "if max_len is not None and max_len < 2:"),
        ("logic: case kept", "text.lower()", "text"),
        ("logic: digits dropped", "[^a-z0-9]+", "[^a-z]+"),
    ],
    weak=5,
))

TASKS.append(dict(
    id="qa_rle", diff="easy",
    spec="Write tests for `rle_encode(s)` and `rle_decode(s)` in rle.py.",
    files={"rle.py": r'''
def rle_encode(s):
    """'aaabcc' -> '3a1b2c'. Empty string -> ''. Digits in the input are not supported (ValueError)."""
    if any(c.isdigit() for c in s):
        raise ValueError("digits not supported")
    out = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f"{j - i}{s[i]}")
        i = j
    return "".join(out)


def rle_decode(s):
    """'3a1b2c' -> 'aaabcc'. Counts may have several digits ('12x'). Malformed input -> ValueError."""
    out = []
    num = ""
    for c in s:
        if c.isdigit():
            num += c
        else:
            if not num:
                raise ValueError("missing count")
            out.append(c * int(num))
            num = ""
    if num:
        raise ValueError("dangling count")
    return "".join(out)
'''},
    tests=r'''
from rle import rle_encode, rle_decode

assert rle_encode("aaabcc") == "3a1b2c"
assert rle_encode("") == ""
assert rle_encode("a") == "1a"
assert rle_encode("abc") == "1a1b1c"
assert rle_encode("a" * 12) == "12a"
assert rle_encode("aabbaa") == "2a2b2a"
try:
    rle_encode("a1")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")

assert rle_decode("3a1b2c") == "aaabcc"
assert rle_decode("") == ""
assert rle_decode("12x") == "x" * 12
assert rle_decode("1a") == "a"
assert rle_decode("10a2b") == "a" * 10 + "bb"
for bad in ("a", "3", "2a3", "ab"):
    try:
        rle_decode(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for " + bad)
for s in ("aaabccddddd", "z", "xyxyxy"):
    assert rle_decode(rle_encode(s)) == s
''',
    muts=[
        ("off-by-one: count", 'f"{j - i}{s[i]}"', 'f"{j - i - 1}{s[i]}"'),
        ("logic: run end not checked", "while j < len(s) and s[j] == s[i]:", "while j < len(s) - 1 and s[j] == s[i]:"),
        ("missing-edge-case: multi digit counts", "num += c", "num = c"),
        ("missing-edge-case: dangling count accepted", 'if num:\n        raise ValueError("dangling count")', 'if False:\n        raise ValueError("dangling count")'),
        ("missing-edge-case: missing count accepted", 'if not num:\n                raise ValueError("missing count")', 'if not num:\n                num = "1"'),
        ("exception-type", 'raise ValueError("digits not supported")', 'raise TypeError("digits not supported")'),
        ("missing-edge-case: digits accepted", "if any(c.isdigit() for c in s):", "if False:"),
    ],
    weak=5,
))

TASKS.append(dict(
    id="qa_title_case", diff="medium",
    spec="Write tests for `title_case(text)` in titles.py.",
    files={"titles.py": r'''
SMALL = {"a", "an", "the", "and", "or", "of", "in", "on", "to", "for", "but"}


def title_case(text):
    """Capitalise each word, except small words (SMALL) that are not the first or last word, which stay
    lower case. The rest of each capitalised word is lower-cased. Whitespace is normalised to single spaces."""
    words = text.split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in SMALL and 0 < i < len(words) - 1:
            out.append(lw)
        else:
            out.append(lw[:1].upper() + lw[1:])
    return " ".join(out)
'''},
    tests=r'''
from titles import title_case

assert title_case("the lord of the rings") == "The Lord of the Rings"
assert title_case("war and peace") == "War and Peace"
assert title_case("a tale to remember") == "A Tale to Remember"
assert title_case("what to do in") == "What to Do In"
assert title_case("HELLO wORLD") == "Hello World"
assert title_case("  spaced   out  ") == "Spaced Out"
assert title_case("") == ""
assert title_case("of") == "Of"
assert title_case("the") == "The"
assert title_case("to be or not to be") == "To Be or Not to Be"
assert title_case("x") == "X"
assert title_case("WAR AND PEACE") == "War and Peace"
''',
    muts=[
        ("off-by-one: first word small", "0 < i < len(words) - 1", "0 <= i < len(words) - 1"),
        ("off-by-one: last word small", "0 < i < len(words) - 1", "0 < i < len(words)"),
        ("logic: rest of word not lower-cased", "lw[:1].upper() + lw[1:]", "lw[:1].upper() + w[1:]"),
        ("logic: small word membership", 'SMALL = {"a", "an", "the", "and", "or", "of", "in", "on", "to", "for", "but"}', 'SMALL = {"a", "an", "the", "and", "or", "of", "in", "on", "for", "but"}'),
        ("logic: and now lower-cased check uses original case", "lw in SMALL", "w in SMALL"),
        ("empty-input: crash-free whitespace", 'return " ".join(out)', 'return "  ".join(out)'),
    ],
    weak=5,
))

TASKS.append(dict(
    id="qa_parse_duration", diff="hard",
    spec="Write tests for `parse_duration(text)` in duration.py.",
    files={"duration.py": r'''
import re

UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
PART = re.compile(r"(\d+)([dhms])")


def parse_duration(text):
    """Parse strings like '1h30m', '2d', '90s', '1d 2h 3m 4s' into whole seconds.
    Units must appear in descending order (d, h, m, s) and at most once each; spaces between parts are allowed.
    Empty or malformed strings, unknown units, or repeated/misordered units -> ValueError."""
    s = text.replace(" ", "")
    if not s:
        raise ValueError("empty")
    pos = 0
    total = 0
    last = -1
    order = "dhms"
    while pos < len(s):
        m = PART.match(s, pos)
        if not m:
            raise ValueError("bad duration: %r" % text)
        idx = order.index(m.group(2))
        if idx <= last:
            raise ValueError("units out of order")
        last = idx
        total += int(m.group(1)) * UNITS[m.group(2)]
        pos = m.end()
    return total
'''},
    tests=r'''
from duration import parse_duration

assert parse_duration("90s") == 90
assert parse_duration("1m") == 60
assert parse_duration("1h") == 3600
assert parse_duration("2d") == 172800
assert parse_duration("1h30m") == 5400
assert parse_duration("1d 2h 3m 4s") == 86400 + 7200 + 180 + 4
assert parse_duration("0s") == 0
assert parse_duration("120m") == 7200
assert parse_duration("1d4s") == 86404
for bad in ("", "   ", "abc", "10", "5x", "1s1h", "1h1h", "1m 1m", "h", "1h-2m", "1.5h"):
    try:
        parse_duration(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)
''',
    muts=[
        ("logic: day multiplier", '"d": 86400', '"d": 84600'),
        ("logic: hour multiplier", '"h": 3600', '"h": 3000'),
        ("comparison: repeated unit allowed", "if idx <= last:", "if idx < last:"),
        ("comparison: misordered allowed", "if idx <= last:", "if idx == last:"),
        ("empty-input: empty accepted", 'if not s:\n        raise ValueError("empty")', "if False:\n        pass"),
        ("logic: trailing garbage ignored", "while pos < len(s):", "while PART.match(s, pos):"),
        ("logic: spaces not removed", 'text.replace(" ", "")', "text"),
        ("logic: sum replaced by last part", "total += int", "total = int"),
    ],
    weak=5,
))

TASKS.append(dict(
    id="qa_bisect", diff="medium",
    spec="Write tests for `lower_bound` and `upper_bound` in bsearch.py.",
    files={"bsearch.py": r'''
def lower_bound(xs, target):
    """Index of the first element >= target in the sorted list xs (len(xs) if none)."""
    lo, hi = 0, len(xs)
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(xs, target):
    """Index of the first element > target in the sorted list xs (len(xs) if none)."""
    lo, hi = 0, len(xs)
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo
'''},
    tests=r'''
from bsearch import lower_bound, upper_bound

xs = [1, 2, 2, 2, 5, 8]
assert lower_bound(xs, 2) == 1
assert upper_bound(xs, 2) == 4
assert lower_bound(xs, 0) == 0
assert upper_bound(xs, 0) == 0
assert lower_bound(xs, 9) == 6
assert upper_bound(xs, 9) == 6
assert lower_bound(xs, 5) == 4
assert upper_bound(xs, 5) == 5
assert lower_bound(xs, 3) == 4
assert upper_bound(xs, 3) == 4
assert lower_bound(xs, 1) == 0
assert upper_bound(xs, 8) == 6
assert lower_bound(xs, 8) == 5
assert lower_bound([], 1) == 0
assert upper_bound([], 1) == 0
assert lower_bound([7], 7) == 0
assert upper_bound([7], 7) == 1
assert lower_bound([7], 8) == 1
big = list(range(0, 100, 3))
for t in range(-2, 105):
    assert lower_bound(big, t) == sum(1 for x in big if x < t)
    assert upper_bound(big, t) == sum(1 for x in big if x <= t)
''',
    muts=[
        ("comparison: lower_bound uses <=", "if xs[mid] < target:", "if xs[mid] <= target:"),
        ("comparison: upper_bound uses <", "if xs[mid] <= target:", "if xs[mid] < target:"),
        ("off-by-one: hi starts at len-1", "lo, hi = 0, len(xs)\n    while lo < hi:\n        mid = (lo + hi) // 2\n        if xs[mid] < target:", "lo, hi = 0, len(xs) - 1\n    while lo < hi:\n        mid = (lo + hi) // 2\n        if xs[mid] < target:"),
        ("off-by-one: lo = mid", "lo = mid + 1\n        else:\n            hi = mid\n    return lo\n\n\ndef upper_bound", "lo = mid\n        else:\n            hi = mid\n    return lo\n\n\ndef upper_bound"),
        ("off-by-one: hi = mid - 1 in upper", "hi = mid\n    return lo\n'''" if False else "        if xs[mid] <= target:\n            lo = mid + 1\n        else:\n            hi = mid\n", "        if xs[mid] <= target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n"),
    ],
    weak=5,
))

TASKS.append(dict(
    id="qa_dedupe", diff="easy",
    spec="Write tests for `dedupe(items, key=None)` and `count_by(items, key)` in dedupe.py.",
    files={"dedupe.py": r'''
def dedupe(items, key=None):
    """Remove duplicates, keeping the FIRST occurrence and the original order. With key, two items are
    duplicates when key(a) == key(b). Works for unhashable items only when key returns hashable values."""
    seen = set()
    out = []
    for x in items:
        k = x if key is None else key(x)
        if k in seen:
            continue
        seen.add(k)
        out.append(x)
    return out


def count_by(items, key):
    """Dict mapping key(item) -> number of items, in first-seen order."""
    counts = {}
    for x in items:
        k = key(x)
        counts[k] = counts.get(k, 0) + 1
    return counts
'''},
    tests=r'''
from dedupe import dedupe, count_by

assert dedupe([1, 2, 1, 3, 2]) == [1, 2, 3]
assert dedupe([]) == []
assert dedupe([3, 3, 3]) == [3]
assert dedupe(["b", "a", "b"]) == ["b", "a"]
assert dedupe(["Apple", "apple", "Bob"], key=str.lower) == ["Apple", "Bob"]
assert dedupe([[1], [2], [1]], key=tuple) == [[1], [2]]
assert dedupe([0, False, "", None]) == [0, "", None]
assert dedupe([1, 2, 3]) == [1, 2, 3]
assert count_by([1, 2, 3, 4, 5], lambda x: x % 2) == {1: 3, 0: 2}
assert list(count_by([1, 2, 3, 4, 5], lambda x: x % 2)) == [1, 0]
assert count_by([], len) == {}
assert count_by(["a", "bb", "cc"], len) == {1: 1, 2: 2}
''',
    muts=[
        ("ordering: keeps last occurrence", "        if k in seen:\n            continue\n        seen.add(k)\n        out.append(x)\n", "        if k in seen:\n            out = [y for y in out if (y if key is None else key(y)) != k]\n        seen.add(k)\n        out.append(x)\n"),
        ("ordering: sorted output", "    return out\n\n\ndef count_by", "    return sorted(out)\n\n\ndef count_by"),
        ("logic: key ignored", "k = x if key is None else key(x)", "k = x"),
        ("logic: duplicates kept when falsy", "if k in seen:", "if k and k in seen:"),
        ("off-by-one: counts start at 2", "counts.get(k, 0) + 1", "counts.get(k, 1) + 1"),
        ("logic: key result of count_by is item", "k = key(x)\n        counts", "k = x\n        counts"),
    ],
    weak=5,
))

TASKS.append(dict(
    id="qa_moving_avg", diff="medium",
    spec="Write tests for `moving_average(xs, window)` and `ema(xs, alpha)` in smooth.py.",
    files={"smooth.py": r'''
def moving_average(xs, window):
    """Simple moving average. Returns len(xs) - window + 1 values (empty if window > len(xs)).
    window < 1 -> ValueError."""
    if window < 1:
        raise ValueError("window must be >= 1")
    return [sum(xs[i:i + window]) / window for i in range(len(xs) - window + 1)]


def ema(xs, alpha):
    """Exponential moving average: e0 = x0, e_i = alpha * x_i + (1 - alpha) * e_{i-1}.
    alpha must satisfy 0 < alpha <= 1 else ValueError. Empty input -> []."""
    if not 0 < alpha <= 1:
        raise ValueError("alpha out of range")
    out = []
    for x in xs:
        out.append(x if not out else alpha * x + (1 - alpha) * out[-1])
    return out
'''},
    tests=r'''
from smooth import moving_average, ema

assert moving_average([1, 2, 3, 4, 5], 2) == [1.5, 2.5, 3.5, 4.5]
assert moving_average([1, 2, 3, 4, 5], 5) == [3.0]
assert moving_average([1, 2, 3], 4) == []
assert moving_average([], 1) == []
assert moving_average([4, 8], 1) == [4.0, 8.0]
assert moving_average([1, 2, 3, 4], 3) == [2.0, 3.0]
for bad in (0, -1):
    try:
        moving_average([1], bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

assert ema([], 0.5) == []
assert ema([10], 0.5) == [10]
assert ema([10, 20], 0.5) == [10, 15.0]
assert ema([10, 20, 30], 1) == [10, 20, 30]
assert ema([4, 8], 0.25) == [4, 5.0]
for bad in (0, -0.1, 1.5):
    try:
        ema([1], bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("off-by-one: one value too few", "range(len(xs) - window + 1)", "range(len(xs) - window)"),
        ("off-by-one: divides by window-1", "/ window for", "/ (window - 1 or 1) for"),
        ("boundary: window 1 rejected", "if window < 1:", "if window < 2:"),
        ("boundary: alpha 1 rejected", "if not 0 < alpha <= 1:", "if not 0 < alpha < 1:"),
        ("boundary: alpha 0 accepted", "if not 0 < alpha <= 1:", "if not 0 <= alpha <= 1:"),
        ("swapped-args: weights swapped", "alpha * x + (1 - alpha) * out[-1]", "(1 - alpha) * x + alpha * out[-1]"),
        ("empty-input: first value not seeded", "x if not out else", "0 if not out else"),
    ],
    weak=5,
))

TASKS.append(dict(
    id="qa_primes", diff="easy",
    spec="Write tests for `gcd`, `lcm` and `is_prime` in nt.py.",
    files={"nt.py": r'''
def gcd(a, b):
    """Greatest common divisor of two non-negative ints; gcd(0, 0) == 0."""
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    """Least common multiple of two non-negative ints; 0 if either is 0."""
    if a == 0 or b == 0:
        return 0
    return a // gcd(a, b) * b


def is_prime(n):
    """True when n is a prime number (n >= 2 with no divisor other than 1 and n)."""
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True
'''},
    tests=r'''
from nt import gcd, lcm, is_prime

assert gcd(12, 18) == 6
assert gcd(18, 12) == 6
assert gcd(7, 13) == 1
assert gcd(0, 5) == 5
assert gcd(5, 0) == 5
assert gcd(0, 0) == 0
assert gcd(9, 9) == 9
assert lcm(4, 6) == 12
assert lcm(6, 4) == 12
assert lcm(0, 3) == 0
assert lcm(3, 0) == 0
assert lcm(0, 0) == 0
assert lcm(7, 13) == 91
assert lcm(5, 5) == 5
assert [n for n in range(-3, 30) if is_prime(n)] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
assert is_prime(49) is False
assert is_prime(25) is False
assert is_prime(9) is False
assert is_prime(4) is False
assert is_prime(97) is True
assert is_prime(1) is False
assert is_prime(0) is False
''',
    muts=[
        ("logic: gcd stops early", "while b:", "while b > 1:"),
        ("swapped-args: remainder", "a, b = b, a % b", "a, b = b, b % a if a else b"),
        ("missing-edge-case: lcm zero", "    if a == 0 or b == 0:\n        return 0\n", ""),
        ("logic: lcm multiplies", "a // gcd(a, b) * b", "a * b"),
        ("boundary: 1 is prime", "if n < 2:", "if n < 1:"),
        ("boundary: squares are prime", "while i * i <= n:", "while i * i < n:"),
        ("logic: only checks odd start", "    i = 2\n", "    i = 3\n"),
    ],
    weak=5,
))
