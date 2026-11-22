"""Write-from-spec tasks, part 1 (strings, lists, parsing, simple structures)."""
from common import task


def W(id, diff, topic, stub, instruction, visible, hidden, ref, files=None, name="solution.py"):
    files = files or {name: stub}
    return task(id, "write", diff, topic, files, instruction, visible, hidden, ref if isinstance(ref, dict) else {name: ref})


TASKS_WRITE = [
    W("py_write_fizz_rules", "easy", "strings", "def fizz(n, rules):\n    raise NotImplementedError\n",
      "Implement `fizz(n, rules)`. `rules` is a list of (divisor, word) pairs. Return a list of strings for 1..n: for each number, "
      "concatenate the words (in rule order) of every rule whose divisor divides it; if none apply use str(number).",
      "from solution import fizz\nassert fizz(5, [(3, 'Fizz'), (5, 'Buzz')]) == ['1', '2', 'Fizz', '4', 'Buzz']\n",
      r'''
from solution import fizz
assert fizz(15, [(3, "Fizz"), (5, "Buzz")])[-1] == "FizzBuzz"
assert fizz(5, [(3, "Fizz"), (5, "Buzz")]) == ["1", "2", "Fizz", "4", "Buzz"]
assert fizz(0, [(2, "x")]) == []
assert fizz(4, []) == ["1", "2", "3", "4"]
assert fizz(6, [(2, "a"), (3, "b"), (6, "c")])[5] == "abc"
assert fizz(6, [(3, "b"), (2, "a")])[5] == "ba"
''',
      "def fizz(n, rules):\n    out = []\n    for i in range(1, n + 1):\n        s = ''.join(w for d, w in rules if i % d == 0)\n        out.append(s or str(i))\n    return out\n"),
    W("py_write_caesar", "easy", "strings", "def caesar(text, shift):\n    raise NotImplementedError\n",
      "Implement `caesar(text, shift)`: shift every ASCII letter forward by `shift` positions in the alphabet (wrapping, preserving case); "
      "a negative shift shifts backwards, shifts larger than 26 wrap; non-letters are unchanged.",
      "from solution import caesar\nassert caesar('abc', 1) == 'bcd'\n",
      r'''
from solution import caesar
assert caesar("abc", 1) == "bcd"
assert caesar("xyz", 3) == "abc"
assert caesar("Hello, World!", 13) == "Uryyb, Jbeyq!"
assert caesar("Uryyb, Jbeyq!", -13) == "Hello, World!"
assert caesar("abc", 53) == "bcd"
assert caesar("abc", -27) == "zab"
assert caesar("", 5) == ""
assert caesar("123 é", 4) == "123 é"
''',
      "def caesar(text, shift):\n    out = []\n    for c in text:\n        if 'a' <= c <= 'z':\n            out.append(chr((ord(c) - 97 + shift) % 26 + 97))\n        elif 'A' <= c <= 'Z':\n            out.append(chr((ord(c) - 65 + shift) % 26 + 65))\n        else:\n            out.append(c)\n    return ''.join(out)\n"),
    W("py_write_anagram_groups", "easy", "strings", "def anagram_groups(words):\n    raise NotImplementedError\n",
      "Implement `anagram_groups(words)`: group words that are anagrams of each other (case-insensitive comparison, original spelling kept). "
      "Return a list of groups with at least 2 words; each group sorted alphabetically (plain string sort), and the groups sorted by their first word.",
      "from solution import anagram_groups\nassert anagram_groups(['listen', 'silent', 'cat']) == [['listen', 'silent']]\n",
      r'''
from solution import anagram_groups
assert anagram_groups(["listen", "silent", "cat"]) == [["listen", "silent"]]
assert anagram_groups(["tea", "eat", "ate", "tan", "nat", "bat"]) == [["ate", "eat", "tea"], ["nat", "tan"]]
assert anagram_groups([]) == []
assert anagram_groups(["Dusty", "study", "x"]) == [["Dusty", "study"]]
assert anagram_groups(["a", "a"]) == [["a", "a"]]
''',
      "def anagram_groups(words):\n    g = {}\n    for w in words:\n        g.setdefault(''.join(sorted(w.lower())), []).append(w)\n    res = [sorted(v) for v in g.values() if len(v) >= 2]\n    return sorted(res, key=lambda x: x[0])\n"),
    W("py_write_second_largest", "easy", "lists", "def second_largest(nums):\n    raise NotImplementedError\n",
      "Implement `second_largest(nums)`: the second largest DISTINCT value. Raise ValueError if there are fewer than two distinct values.",
      "from solution import second_largest\nassert second_largest([1, 5, 3]) == 3\n",
      r'''
from solution import second_largest
assert second_largest([1, 5, 3]) == 3
assert second_largest([5, 5, 4]) == 4
assert second_largest([-1, -2]) == -2
assert second_largest([2, 2, 3, 3, 1]) == 2
for bad in ([], [1], [7, 7, 7]):
    try:
        second_largest(bad)
        assert False
    except ValueError:
        pass
''',
      "def second_largest(nums):\n    d = sorted(set(nums), reverse=True)\n    if len(d) < 2:\n        raise ValueError('need two distinct values')\n    return d[1]\n"),
    W("py_write_title_case", "easy", "strings", "def title_case(s):\n    raise NotImplementedError\n",
      "Implement `title_case(s)`: capitalise each word (first letter upper, rest lower), but keep these small words lower-case unless "
      "they are the first or last word: a, an, the, of, in, on, and, or, to, for. Words are separated by single spaces.",
      "from solution import title_case\nassert title_case('the lord of the rings') == 'The Lord of the Rings'\n",
      r'''
from solution import title_case
assert title_case("the lord of the rings") == "The Lord of the Rings"
assert title_case("a tale of two cities") == "A Tale of Two Cities"
assert title_case("WAR AND PEACE") == "War and Peace"
assert title_case("what to do in") == "What to Do In"
assert title_case("") == ""
assert title_case("the") == "The"
assert title_case("on") == "On"
''',
      "SMALL = {'a', 'an', 'the', 'of', 'in', 'on', 'and', 'or', 'to', 'for'}\n\n\ndef title_case(s):\n    ws = s.split(' ') if s else []\n    out = []\n    for i, w in enumerate(ws):\n        lw = w.lower()\n        if lw in SMALL and 0 < i < len(ws) - 1:\n            out.append(lw)\n        else:\n            out.append(lw[:1].upper() + lw[1:])\n    return ' '.join(out)\n"),
    W("py_write_rle_encode", "easy", "strings", "def rle_encode(s):\n    raise NotImplementedError\n",
      "Implement `rle_encode(s)`: run-length encode as count followed by the character for every run, including runs of length 1 "
      "('aaab' -> '3a1b'). Empty string gives ''. Input never contains digits.",
      "from solution import rle_encode\nassert rle_encode('aaab') == '3a1b'\n",
      "from solution import rle_encode\nassert rle_encode('aaab') == '3a1b'\nassert rle_encode('') == ''\nassert rle_encode('a') == '1a'\nassert rle_encode('abc') == '1a1b1c'\nassert rle_encode('x' * 12) == '12x'\nassert rle_encode('aabbaa') == '2a2b2a'\n",
      "def rle_encode(s):\n    out = []\n    i = 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        out.append(str(j - i) + s[i])\n        i = j\n    return ''.join(out)\n"),
    W("py_write_gcd_lcm", "easy", "math", "def gcd_all(nums):\n    raise NotImplementedError\n\n\ndef lcm_all(nums):\n    raise NotImplementedError\n",
      "Implement `gcd_all(nums)` and `lcm_all(nums)` for lists of positive ints (do not import math). An empty list raises ValueError. A single number returns itself.",
      "from solution import gcd_all, lcm_all\nassert gcd_all([12, 18]) == 6 and lcm_all([4, 6]) == 12\n",
      r'''
from solution import gcd_all, lcm_all
assert gcd_all([12, 18]) == 6 and lcm_all([4, 6]) == 12
assert gcd_all([7]) == 7 and lcm_all([7]) == 7
assert gcd_all([12, 18, 30]) == 6
assert lcm_all([2, 3, 4, 5]) == 60
assert gcd_all([13, 17]) == 1
for f in (gcd_all, lcm_all):
    try:
        f([])
        assert False
    except ValueError:
        pass
''',
      "def _g(a, b):\n    while b:\n        a, b = b, a % b\n    return a\n\n\ndef gcd_all(nums):\n    if not nums:\n        raise ValueError('empty')\n    r = nums[0]\n    for n in nums[1:]:\n        r = _g(r, n)\n    return r\n\n\ndef lcm_all(nums):\n    if not nums:\n        raise ValueError('empty')\n    r = nums[0]\n    for n in nums[1:]:\n        r = r * n // _g(r, n)\n    return r\n"),
    W("py_write_valid_ipv4", "easy", "parsing", "def is_ipv4(s):\n    raise NotImplementedError\n",
      "Implement `is_ipv4(s)`: True for dotted-quad IPv4 addresses: exactly four decimal parts, each 0-255, digits only, no leading zeros "
      "(except a lone '0'), no spaces or signs.",
      "from solution import is_ipv4\nassert is_ipv4('192.168.0.1') and not is_ipv4('256.1.1.1')\n",
      r'''
from solution import is_ipv4
assert is_ipv4("192.168.0.1") and is_ipv4("0.0.0.0") and is_ipv4("255.255.255.255")
for bad in ["256.1.1.1", "1.2.3", "1.2.3.4.5", "01.2.3.4", "1.2.3.-4", "a.b.c.d", "1..3.4", " 1.2.3.4", "1.2.3.4 ", "+1.2.3.4", ""]:
    assert not is_ipv4(bad), bad
''',
      "def is_ipv4(s):\n    p = s.split('.')\n    if len(p) != 4:\n        return False\n    for x in p:\n        if not (x.isascii() and x.isdigit()) or (len(x) > 1 and x[0] == '0') or int(x) > 255:\n            return False\n    return True\n"),
    W("py_write_invert_dict", "easy", "dicts", "def invert(d):\n    raise NotImplementedError\n",
      "Implement `invert(d)`: swap keys and values. When several keys share a value, the inverted value is the list of those keys "
      "in the original insertion order; unique values map to a single key (not a list).",
      "from solution import invert\nassert invert({'a': 1, 'b': 2}) == {1: 'a', 2: 'b'}\n",
      r'''
from solution import invert
assert invert({"a": 1, "b": 2}) == {1: "a", 2: "b"}
assert invert({"a": 1, "b": 1, "c": 2}) == {1: ["a", "b"], 2: "c"}
assert invert({}) == {}
assert invert({"x": 0, "y": 0, "z": 0}) == {0: ["x", "y", "z"]}
''',
      "def invert(d):\n    g = {}\n    for k, v in d.items():\n        g.setdefault(v, []).append(k)\n    return {v: ks[0] if len(ks) == 1 else ks for v, ks in g.items()}\n"),
    W("py_write_case_convert", "easy", "strings", "def snake_to_camel(s):\n    raise NotImplementedError\n\n\ndef camel_to_snake(s):\n    raise NotImplementedError\n",
      "Implement `snake_to_camel(s)` ('user_id_map' -> 'userIdMap'; ignore empty segments caused by repeated or leading/trailing underscores) "
      "and `camel_to_snake(s)` ('userIdMap' -> 'user_id_map'; an upper-case letter starts a new word; the result is lower-case; "
      "runs of capitals such as 'HTTPServer' become 'h_t_t_p_server' by the simple rule). Both return '' for ''.",
      "from solution import snake_to_camel, camel_to_snake\nassert snake_to_camel('a_b') == 'aB' and camel_to_snake('aB') == 'a_b'\n",
      r'''
from solution import snake_to_camel as sc, camel_to_snake as cs
assert sc("user_id_map") == "userIdMap"
assert sc("__x__y_") == "xY"
assert sc("single") == "single"
assert sc("") == ""
assert cs("userIdMap") == "user_id_map"
assert cs("HTTPServer") == "h_t_t_p_server"
assert cs("Abc") == "abc"
assert cs("") == ""
assert cs(sc("a_b_c")) == "a_b_c"
''',
      "def snake_to_camel(s):\n    parts = [p for p in s.split('_') if p]\n    return ''.join(p if i == 0 else p[0].upper() + p[1:] for i, p in enumerate(parts))\n\n\ndef camel_to_snake(s):\n    out = []\n    for i, c in enumerate(s):\n        if c.isupper() and i:\n            out.append('_')\n        out.append(c.lower())\n    return ''.join(out)\n"),
    W("py_write_min_add_parens", "easy", "parsing", "def min_additions(s):\n    raise NotImplementedError\n",
      "Implement `min_additions(s)` for a string of '(' and ')': the minimum number of parentheses to insert so the string becomes balanced.",
      "from solution import min_additions\nassert min_additions('())') == 1\n",
      "from solution import min_additions\nassert min_additions('())') == 1\nassert min_additions('(((') == 3\nassert min_additions('') == 0\nassert min_additions('()') == 0\nassert min_additions(')(') == 2\nassert min_additions('()))((') == 4\n",
      "def min_additions(s):\n    open_ = add = 0\n    for c in s:\n        if c == '(':\n            open_ += 1\n        elif open_:\n            open_ -= 1\n        else:\n            add += 1\n    return add + open_\n"),
    W("py_write_hex_color", "easy", "parsing", "def parse_color(s):\n    raise NotImplementedError\n",
      "Implement `parse_color(s)`: parse '#rrggbb' or the short form '#rgb' (each digit doubled), case-insensitive, into an (r, g, b) tuple of ints. "
      "Anything else (missing '#', wrong length, non-hex digits) raises ValueError.",
      "from solution import parse_color\nassert parse_color('#ff0080') == (255, 0, 128)\n",
      r'''
from solution import parse_color
assert parse_color("#ff0080") == (255, 0, 128)
assert parse_color("#FFF") == (255, 255, 255)
assert parse_color("#a1c") == (170, 17, 204)
for bad in ["ff0080", "#ff00", "#gg0000", "", "#12345678", "#"]:
    try:
        parse_color(bad)
        assert False, bad
    except ValueError:
        pass
''',
      "def parse_color(s):\n    if not s.startswith('#') or len(s) not in (4, 7) or any(c not in '0123456789abcdefABCDEF' for c in s[1:]):\n        raise ValueError(s)\n    h = s[1:]\n    if len(h) == 3:\n        h = ''.join(c * 2 for c in h)\n    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))\n"),
    # ---------------- medium
    W("py_write_spiral", "medium", "matrices", "def spiral(m):\n    raise NotImplementedError\n",
      "Implement `spiral(m)`: return the elements of a rectangular matrix (list of rows, possibly empty) in clockwise spiral order starting at the top-left.",
      "from solution import spiral\nassert spiral([[1, 2], [3, 4]]) == [1, 2, 4, 3]\n",
      r'''
from solution import spiral
assert spiral([[1, 2], [3, 4]]) == [1, 2, 4, 3]
assert spiral([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
assert spiral([[1, 2, 3, 4]]) == [1, 2, 3, 4]
assert spiral([[1], [2], [3]]) == [1, 2, 3]
assert spiral([]) == []
assert spiral([[1, 2, 3], [4, 5, 6]]) == [1, 2, 3, 6, 5, 4]
assert spiral([[1, 2], [3, 4], [5, 6]]) == [1, 2, 4, 6, 5, 3]
''',
      "def spiral(m):\n    out = []\n    if not m:\n        return out\n    t, b, l, r = 0, len(m) - 1, 0, len(m[0]) - 1\n    while t <= b and l <= r:\n        out += [m[t][c] for c in range(l, r + 1)]\n        t += 1\n        out += [m[i][r] for i in range(t, b + 1)]\n        r -= 1\n        if t <= b:\n            out += [m[b][c] for c in range(r, l - 1, -1)]\n            b -= 1\n        if l <= r:\n            out += [m[i][l] for i in range(b, t - 1, -1)]\n            l += 1\n    return out\n"),
    W("py_write_sudoku_valid", "medium", "matrices", "def is_valid_board(board):\n    raise NotImplementedError\n",
      "Implement `is_valid_board(board)`: `board` is 9 strings of 9 characters, each a digit '1'-'9' or '.' for empty. Return True iff no digit repeats "
      "in any row, column or 3x3 box (the board need not be solvable).",
      "from solution import is_valid_board\nassert is_valid_board(['.' * 9] * 9)\n",
      r'''
from solution import is_valid_board
empty = ["........."] * 9
assert is_valid_board(empty)
ok = ["53..7....", "6..195...", ".98....6.", "8...6...3", "4..8.3..1", "7...2...6", ".6....28.", "...419..5", "....8..79"]
assert is_valid_board(ok)
row = list(empty); row[0] = "55......."
assert not is_valid_board(row)
col = list(empty); col[0] = "1........"; col[8] = "1........"
assert not is_valid_board(col)
box = list(empty); box[0] = "1........"; box[2] = ".1......."
assert not is_valid_board(box)
box2 = list(empty); box2[3] = "...2....."; box2[5] = ".....2..."
assert not is_valid_board(box2)
far = list(empty); far[0] = "1........"; far[3] = ".1......."
assert is_valid_board(far)
''',
      "def is_valid_board(board):\n    seen = set()\n    for r in range(9):\n        for c in range(9):\n            d = board[r][c]\n            if d == '.':\n                continue\n            for k in (('r', r, d), ('c', c, d), ('b', r // 3, c // 3, d)):\n                if k in seen:\n                    return False\n                seen.add(k)\n    return True\n"),
    W("py_write_merge_k_sorted", "medium", "heaps", "def merge_sorted(lists):\n    raise NotImplementedError\n",
      "Implement `merge_sorted(lists)`: merge any number of individually sorted lists into one sorted list using a heap (heapq allowed), stable "
      "by list order for equal items. Empty lists are fine.",
      "from solution import merge_sorted\nassert merge_sorted([[1, 4], [2, 3]]) == [1, 2, 3, 4]\n",
      r'''
from solution import merge_sorted
assert merge_sorted([[1, 4], [2, 3]]) == [1, 2, 3, 4]
assert merge_sorted([]) == []
assert merge_sorted([[], [1], []]) == [1]
assert merge_sorted([[1, 1, 5], [1, 2], [0, 9]]) == [0, 1, 1, 1, 2, 5, 9]
import random
random.seed(1)
ls = [sorted(random.randint(0, 99) for _ in range(random.randint(0, 20))) for _ in range(15)]
assert merge_sorted(ls) == sorted(x for l in ls for x in l)
''',
      "import heapq\n\n\ndef merge_sorted(lists):\n    h = [(l[0], i, 0) for i, l in enumerate(lists) if l]\n    heapq.heapify(h)\n    out = []\n    while h:\n        v, i, j = heapq.heappop(h)\n        out.append(v)\n        if j + 1 < len(lists[i]):\n            heapq.heappush(h, (lists[i][j + 1], i, j + 1))\n    return out\n"),
    W("py_write_number_words", "medium", "strings", "def to_words(n):\n    raise NotImplementedError\n",
      "Implement `to_words(n)` for 0 <= n <= 999999 returning English words: 'zero', 'forty-two', 'one hundred five', 'one thousand', "
      "'twelve thousand three hundred forty-five', 'nine hundred ninety-nine thousand nine hundred ninety-nine'. Hyphenate tens-units (21-99), "
      "no 'and', singular 'hundred'/'thousand'. Raise ValueError outside the range.",
      "from solution import to_words\nassert to_words(42) == 'forty-two'\n",
      r'''
from solution import to_words as w
assert w(0) == "zero" and w(7) == "seven" and w(13) == "thirteen" and w(20) == "twenty"
assert w(42) == "forty-two" and w(100) == "one hundred" and w(105) == "one hundred five"
assert w(1000) == "one thousand" and w(1001) == "one thousand one"
assert w(12345) == "twelve thousand three hundred forty-five"
assert w(999999) == "nine hundred ninety-nine thousand nine hundred ninety-nine"
assert w(100000) == "one hundred thousand"
assert w(90010) == "ninety thousand ten"
for bad in (-1, 1000000):
    try:
        w(bad)
        assert False
    except ValueError:
        pass
''',
      "ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()\nTENS = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()\n\n\ndef _under1000(n):\n    parts = []\n    if n >= 100:\n        parts.append(ONES[n // 100] + ' hundred')\n        n %= 100\n    if n >= 20:\n        parts.append(TENS[n // 10] + ('-' + ONES[n % 10] if n % 10 else ''))\n    elif n or not parts:\n        parts.append(ONES[n])\n    return ' '.join(parts)\n\n\ndef to_words(n):\n    if not 0 <= n <= 999999:\n        raise ValueError(n)\n    if n == 0:\n        return 'zero'\n    th, rest = divmod(n, 1000)\n    parts = []\n    if th:\n        parts.append(_under1000(th) + ' thousand')\n    if rest:\n        parts.append(_under1000(rest))\n    return ' '.join(parts)\n"),
    W("py_write_coin_change", "medium", "dp", "def min_coins(coins, amount):\n    raise NotImplementedError\n",
      "Implement `min_coins(coins, amount)`: the fewest coins (unlimited supply of each denomination) summing exactly to amount, or -1 if impossible. "
      "amount 0 needs 0 coins.",
      "from solution import min_coins\nassert min_coins([1, 2, 5], 11) == 3\n",
      "from solution import min_coins\nassert min_coins([1, 2, 5], 11) == 3\nassert min_coins([2], 3) == -1\nassert min_coins([5], 0) == 0\nassert min_coins([1, 3, 4], 6) == 2\nassert min_coins([], 5) == -1\nassert min_coins([186, 419, 83, 408], 6249) == 20\n",
      "def min_coins(coins, amount):\n    INF = float('inf')\n    dp = [0] + [INF] * amount\n    for a in range(1, amount + 1):\n        for c in coins:\n            if c <= a and dp[a - c] + 1 < dp[a]:\n                dp[a] = dp[a - c] + 1\n    return -1 if dp[amount] == INF else dp[amount]\n"),
    W("py_write_lis", "medium", "dp", "def lis(nums):\n    raise NotImplementedError\n",
      "Implement `lis(nums)`: return the longest strictly increasing subsequence as a list. If several have the maximum length, return the one that "
      "is lexicographically smallest as a list of values.",
      "from solution import lis\nassert lis([3, 1, 2]) == [1, 2]\n",
      r'''
from solution import lis
assert lis([3, 1, 2]) == [1, 2]
assert lis([]) == []
assert lis([5]) == [5]
assert lis([5, 4, 3]) == [3]
assert lis([10, 9, 2, 5, 3, 7, 101, 18]) == [2, 3, 7, 18]
assert lis([1, 1, 1]) == [1]
assert lis([0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15]) == [0, 2, 6, 9, 11, 15]
''',
      "def lis(nums):\n    n = len(nums)\n    if not n:\n        return []\n    # best[i] = longest strictly increasing subsequence starting at i, lexicographically smallest\n    best = [None] * n\n    for i in range(n - 1, -1, -1):\n        cand = [nums[i]]\n        for j in range(i + 1, n):\n            if nums[j] > nums[i]:\n                c = [nums[i]] + best[j]\n                if len(c) > len(cand) or (len(c) == len(cand) and c < cand):\n                    cand = c\n        best[i] = cand\n    res = []\n    for b in best:\n        if len(b) > len(res) or (len(b) == len(res) and b < res):\n            res = b\n    return res\n"),
    W("py_write_islands", "medium", "graphs", "def count_islands(grid):\n    raise NotImplementedError\n",
      "Implement `count_islands(grid)`: `grid` is a list of strings of '1' (land) and '0' (water). Count 4-directionally connected land regions. "
      "Must not hit the recursion limit on a 200x200 all-land grid.",
      "from solution import count_islands\nassert count_islands(['11', '00']) == 1\n",
      r'''
from solution import count_islands
assert count_islands(["11", "00"]) == 1
assert count_islands(["101", "010", "101"]) == 5
assert count_islands([]) == 0
assert count_islands(["000"]) == 0
assert count_islands(["11000", "11000", "00100", "00011"]) == 3
assert count_islands(["1" * 200] * 200) == 1
g = ["1110", "0100", "0111"]
assert count_islands(g) == 1
''',
      "def count_islands(grid):\n    seen = set()\n    n = 0\n    for r in range(len(grid)):\n        for c in range(len(grid[0])):\n            if grid[r][c] == '1' and (r, c) not in seen:\n                n += 1\n                st = [(r, c)]\n                seen.add((r, c))\n                while st:\n                    y, x = st.pop()\n                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n                        ny, nx = y + dy, x + dx\n                        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == '1' and (ny, nx) not in seen:\n                            seen.add((ny, nx))\n                            st.append((ny, nx))\n    return n\n"),
    W("py_write_bipartite", "medium", "graphs", "def is_bipartite(n, edges):\n    raise NotImplementedError\n",
      "Implement `is_bipartite(n, edges)`: undirected graph with nodes 0..n-1 and `edges` a list of (u, v) pairs (may be disconnected; self-loop "
      "means not bipartite; duplicate edges are fine). Return True iff the nodes can be 2-coloured.",
      "from solution import is_bipartite\nassert is_bipartite(2, [(0, 1)])\n",
      r'''
from solution import is_bipartite
assert is_bipartite(2, [(0, 1)])
assert not is_bipartite(3, [(0, 1), (1, 2), (2, 0)])
assert is_bipartite(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
assert is_bipartite(5, [])
assert not is_bipartite(1, [(0, 0)])
assert is_bipartite(6, [(0, 1), (2, 3), (3, 4), (4, 5), (0, 1)])
assert not is_bipartite(7, [(0, 1), (3, 4), (4, 5), (5, 3), (5, 6)])
assert is_bipartite(0, [])
''',
      "def is_bipartite(n, edges):\n    adj = [[] for _ in range(n)]\n    for u, v in edges:\n        if u == v:\n            return False\n        adj[u].append(v)\n        adj[v].append(u)\n    col = [-1] * n\n    for s in range(n):\n        if col[s] != -1:\n            continue\n        col[s] = 0\n        st = [s]\n        while st:\n            u = st.pop()\n            for v in adj[u]:\n                if col[v] == -1:\n                    col[v] = 1 - col[u]\n                    st.append(v)\n                elif col[v] == col[u]:\n                    return False\n    return True\n"),
    W("py_write_has_cycle_directed", "medium", "graphs", "def has_cycle(graph):\n    raise NotImplementedError\n",
      "Implement `has_cycle(graph)`: `graph` maps node -> list of successor nodes (successors may be missing as keys). Return True iff the directed "
      "graph contains a cycle (a self-loop counts). Must be iterative-safe for a 5000-node chain.",
      "from solution import has_cycle\nassert has_cycle({'a': ['b'], 'b': ['a']})\n",
      r'''
from solution import has_cycle
assert has_cycle({"a": ["b"], "b": ["a"]})
assert not has_cycle({"a": ["b", "c"], "b": ["c"]})
assert has_cycle({"a": ["a"]})
assert not has_cycle({})
assert has_cycle({"a": ["b"], "b": ["c"], "c": ["d"], "d": ["b"]})
assert not has_cycle({"a": ["c"], "b": ["c"], "c": []})
chain = {i: [i + 1] for i in range(5000)}
assert not has_cycle(chain)
chain[5000] = [0]
assert has_cycle(chain)
''',
      "def has_cycle(graph):\n    WHITE, GREY, BLACK = 0, 1, 2\n    color = {}\n    for s in list(graph):\n        if color.get(s, WHITE) != WHITE:\n            continue\n        color[s] = GREY\n        st = [(s, iter(graph.get(s, [])))]\n        while st:\n            u, it = st[-1]\n            for v in it:\n                c = color.get(v, WHITE)\n                if c == GREY:\n                    return True\n                if c == WHITE:\n                    color[v] = GREY\n                    st.append((v, iter(graph.get(v, []))))\n                    break\n            else:\n                color[u] = BLACK\n                st.pop()\n    return False\n"),
    W("py_write_num_matrix", "medium", "data-structures",
      "class NumMatrix:\n    def __init__(self, matrix):\n        raise NotImplementedError\n\n    def region_sum(self, r1, c1, r2, c2):\n        raise NotImplementedError\n",
      "Implement class `NumMatrix(matrix)` with `region_sum(r1, c1, r2, c2)`: sum of the inclusive rectangle with corners (r1,c1) and (r2,c2) "
      "(r1<=r2, c1<=c2). Precompute prefix sums so each query is O(1). Out-of-range indices raise IndexError.",
      "from solution import NumMatrix\nassert NumMatrix([[1, 2], [3, 4]]).region_sum(0, 0, 1, 1) == 10\n",
      r'''
from solution import NumMatrix
m = NumMatrix([[3, 0, 1, 4, 2], [5, 6, 3, 2, 1], [1, 2, 0, 1, 5], [4, 1, 0, 1, 7], [1, 0, 3, 0, 5]])
assert m.region_sum(2, 1, 4, 3) == 8
assert m.region_sum(1, 1, 2, 2) == 11
assert m.region_sum(1, 2, 2, 4) == 12
assert m.region_sum(0, 0, 0, 0) == 3
assert m.region_sum(0, 0, 4, 4) == sum(map(sum, [[3, 0, 1, 4, 2], [5, 6, 3, 2, 1], [1, 2, 0, 1, 5], [4, 1, 0, 1, 7], [1, 0, 3, 0, 5]]))
try:
    m.region_sum(0, 0, 5, 0)
    assert False
except IndexError:
    pass
n = NumMatrix([[-1]])
assert n.region_sum(0, 0, 0, 0) == -1
''',
      "class NumMatrix:\n    def __init__(self, matrix):\n        self.R = len(matrix)\n        self.C = len(matrix[0]) if matrix else 0\n        self.p = [[0] * (self.C + 1) for _ in range(self.R + 1)]\n        for r in range(self.R):\n            for c in range(self.C):\n                self.p[r + 1][c + 1] = matrix[r][c] + self.p[r][c + 1] + self.p[r + 1][c] - self.p[r][c]\n\n    def region_sum(self, r1, c1, r2, c2):\n        if not (0 <= r1 <= r2 < self.R and 0 <= c1 <= c2 < self.C):\n            raise IndexError('out of range')\n        p = self.p\n        return p[r2 + 1][c2 + 1] - p[r1][c2 + 1] - p[r2 + 1][c1] + p[r1][c1]\n"),
    W("py_write_insert_interval", "medium", "intervals", "def insert_interval(intervals, new):\n    raise NotImplementedError\n",
      "Implement `insert_interval(intervals, new)`: `intervals` is a sorted list of disjoint closed intervals [start, end]; `new` is [start, end]. "
      "Insert it, merging anything that overlaps or touches (e.g. [1,2] and [2,3] merge). Return a new list of lists; do not mutate the input.",
      "from solution import insert_interval\nassert insert_interval([[1, 3]], [4, 5]) == [[1, 3], [4, 5]]\n",
      r'''
from solution import insert_interval
assert insert_interval([[1, 3]], [4, 5]) == [[1, 3], [4, 5]]
assert insert_interval([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
assert insert_interval([], [5, 7]) == [[5, 7]]
assert insert_interval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]) == [[1, 2], [3, 10], [12, 16]]
assert insert_interval([[1, 2]], [2, 3]) == [[1, 3]]
assert insert_interval([[5, 6]], [1, 2]) == [[1, 2], [5, 6]]
assert insert_interval([[1, 10]], [3, 4]) == [[1, 10]]
src = [[1, 3]]
insert_interval(src, [2, 9])
assert src == [[1, 3]]
''',
      "def insert_interval(intervals, new):\n    out = []\n    s, e = new\n    placed = False\n    for a, b in intervals:\n        if b < s:\n            out.append([a, b])\n        elif a > e:\n            if not placed:\n                out.append([s, e])\n                placed = True\n            out.append([a, b])\n        else:\n            s, e = min(s, a), max(e, b)\n    if not placed:\n        out.append([s, e])\n    return out\n"),
    W("py_write_min_rooms", "medium", "heaps", "def min_rooms(meetings):\n    raise NotImplementedError\n",
      "Implement `min_rooms(meetings)`: meetings are (start, end) with start < end; a meeting ending at t does not conflict with one starting at t. "
      "Return the minimum number of rooms needed.",
      "from solution import min_rooms\nassert min_rooms([(0, 30), (5, 10), (15, 20)]) == 2\n",
      "from solution import min_rooms\nassert min_rooms([(0, 30), (5, 10), (15, 20)]) == 2\nassert min_rooms([]) == 0\nassert min_rooms([(1, 2), (2, 3)]) == 1\nassert min_rooms([(1, 5), (2, 6), (3, 7)]) == 3\nassert min_rooms([(7, 10), (2, 4)]) == 1\nassert min_rooms([(1, 4), (2, 3), (3, 6), (4, 5)]) == 2\n",
      "import heapq\n\n\ndef min_rooms(meetings):\n    h = []\n    best = 0\n    for s, e in sorted(meetings):\n        while h and h[0] <= s:\n            heapq.heappop(h)\n        heapq.heappush(h, e)\n        best = max(best, len(h))\n    return best\n"),
    W("py_write_ini_parser", "medium", "parsing", "def parse_ini(text):\n    raise NotImplementedError\n",
      "Implement `parse_ini(text)` returning a dict of section -> dict of key -> value (all strings). `[name]` starts a section; `key = value` lines "
      "(whitespace around key and value stripped; split on the FIRST '='); blank lines and lines starting with ';' or '#' are ignored; keys before any "
      "section go into section ''. Later duplicates override earlier ones. A non-blank, non-comment line that is neither a header nor key=value "
      "raises ValueError.",
      "from solution import parse_ini\nassert parse_ini('[a]\\nx=1') == {'a': {'x': '1'}}\n",
      r'''
from solution import parse_ini
assert parse_ini("[a]\nx=1") == {"a": {"x": "1"}}
t = """
top = 1
; comment
[db]
host = localhost
url = a=b=c
# another
port=5432
host = remote

[empty]
"""
assert parse_ini(t) == {"": {"top": "1"}, "db": {"host": "remote", "url": "a=b=c", "port": "5432"}, "empty": {}}
assert parse_ini("") == {}
try:
    parse_ini("[a]\njunk")
    assert False
except ValueError:
    pass
assert parse_ini("[ s ]\nk =  v v ") == {"s": {"k": "v v"}}
''',
      "def parse_ini(text):\n    out = {}\n    cur = None\n    for raw in text.splitlines():\n        line = raw.strip()\n        if not line or line[0] in ';#':\n            continue\n        if line.startswith('[') and line.endswith(']'):\n            cur = out.setdefault(line[1:-1].strip(), {})\n        elif '=' in line:\n            k, v = line.split('=', 1)\n            if cur is None:\n                cur = out.setdefault('', {})\n            cur[k.strip()] = v.strip()\n        else:\n            raise ValueError(raw)\n    return out\n"),
    W("py_write_template_render", "medium", "parsing", "def render(template, context):\n    raise NotImplementedError\n",
      "Implement `render(template, context)`: replace each `{{ name }}` (optional spaces inside the braces) with str(context[name]). `{{ name|default }}` "
      "uses the text after `|` (stripped) when name is missing. A missing name without default raises KeyError. Dotted names like `user.name` look up "
      "nested dicts. Text outside `{{ }}` is untouched; a `{{` without closing `}}` raises ValueError.",
      "from solution import render\nassert render('Hi {{ n }}', {'n': 'Bo'}) == 'Hi Bo'\n",
      r'''
from solution import render
assert render("Hi {{ n }}", {"n": "Bo"}) == "Hi Bo"
assert render("{{a}}{{b}}", {"a": 1, "b": 2.5}) == "12.5"
assert render("x {{ who|world }}!", {}) == "x world!"
assert render("x {{ who|world }}!", {"who": "me"}) == "x me!"
assert render("{{ user.name }}", {"user": {"name": "Ann"}}) == "Ann"
assert render("no tags {single}", {}) == "no tags {single}"
assert render("{{ z|0 }}", {"z": 0}) == "0"
for tpl, ctx, exc in [("{{ q }}", {}, KeyError), ("oops {{ q", {"q": 1}, ValueError), ("{{ u.v }}", {"u": {}}, KeyError)]:
    try:
        render(tpl, ctx)
        assert False, tpl
    except exc:
        pass
''',
      "def render(template, context):\n    out = []\n    i = 0\n    while True:\n        j = template.find('{{', i)\n        if j < 0:\n            out.append(template[i:])\n            break\n        out.append(template[i:j])\n        k = template.find('}}', j + 2)\n        if k < 0:\n            raise ValueError('unclosed')\n        expr = template[j + 2:k]\n        default = None\n        if '|' in expr:\n            expr, default = expr.split('|', 1)\n            default = default.strip()\n        cur = context\n        try:\n            for part in expr.strip().split('.'):\n                cur = cur[part]\n        except (KeyError, TypeError):\n            if default is None:\n                raise KeyError(expr.strip())\n            cur = default\n        out.append(str(cur))\n        i = k + 2\n    return ''.join(out)\n"),
    W("py_write_shell_split", "medium", "parsing", "def split_args(line):\n    raise NotImplementedError\n",
      "Implement `split_args(line)`: split a command line into arguments on whitespace. Single quotes keep everything literal up to the closing quote; "
      "double quotes group text and allow `\\\"` and `\\\\` escapes; a backslash outside quotes escapes the next character. Adjacent quoted/unquoted "
      "pieces join into one argument (`a\"b c\"d` -> `ab cd`); empty quotes `\"\"` produce an empty argument. Unterminated quotes raise ValueError.",
      "from solution import split_args\nassert split_args('a b') == ['a', 'b']\n",
      r'''
from solution import split_args
assert split_args("a b") == ["a", "b"]
assert split_args("  a   b  ") == ["a", "b"]
assert split_args("") == []
assert split_args('echo "hello world"') == ["echo", "hello world"]
assert split_args("echo 'a  b' c") == ["echo", "a  b", "c"]
assert split_args('a"b c"d') == ["ab cd"]
assert split_args('x "" y') == ["x", "", "y"]
assert split_args(r'a\ b') == ["a b"]
assert split_args(r'"say \"hi\""') == ['say "hi"']
assert split_args(r"'a\b'") == ["a\\b"]
assert split_args(r'"a\\b"') == ["a\\b"]
for bad in ['"abc', "'abc", 'a "b']:
    try:
        split_args(bad)
        assert False, bad
    except ValueError:
        pass
''',
      "def split_args(line):\n    args = []\n    cur = []\n    have = False\n    i = 0\n    n = len(line)\n    while i < n:\n        c = line[i]\n        if c in ' \\t\\n':\n            if have:\n                args.append(''.join(cur))\n                cur, have = [], False\n            i += 1\n        elif c == \"'\":\n            j = line.find(\"'\", i + 1)\n            if j < 0:\n                raise ValueError('unterminated')\n            cur.append(line[i + 1:j])\n            have = True\n            i = j + 1\n        elif c == '\"':\n            i += 1\n            have = True\n            while True:\n                if i >= n:\n                    raise ValueError('unterminated')\n                d = line[i]\n                if d == '\"':\n                    i += 1\n                    break\n                if d == '\\\\' and i + 1 < n and line[i + 1] in '\"\\\\':\n                    cur.append(line[i + 1])\n                    i += 2\n                else:\n                    cur.append(d)\n                    i += 1\n        elif c == '\\\\' and i + 1 < n:\n            cur.append(line[i + 1])\n            have = True\n            i += 2\n        else:\n            cur.append(c)\n            have = True\n            i += 1\n    if have:\n        args.append(''.join(cur))\n    return args\n"),
]
