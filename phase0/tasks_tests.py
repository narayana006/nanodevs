"""Write-the-tests tasks, graded by mutation: the tests must pass on the correct module and fail on every broken variant."""

TASKS_TESTS = [
    dict(
        id="tests_calendar", kind="tests", module="calendar_utils",
        files={"calendar_utils.py": r'''
def is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31
'''},
        instruction="Write tests for `is_leap(year)` and `days_in_month(year, month)` in calendar_utils.py.",
        mutants=[
            {"calendar_utils.py": r'''
def is_leap(year):
    return year % 4 == 0


def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31
'''},
            {"calendar_utils.py": r'''
def is_leap(year):
    return year % 4 == 0 and year % 100 != 0


def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31
'''},
            {"calendar_utils.py": r'''
def is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap(year) else 28
    return 30 if month in (4, 6, 9) else 31
'''},
        ],
        reference_tests=r'''
from calendar_utils import is_leap, days_in_month

assert is_leap(2000) is True
assert is_leap(1900) is False
assert is_leap(2024) is True
assert is_leap(2023) is False
assert is_leap(2400) is True
assert is_leap(2100) is False
assert days_in_month(2024, 2) == 29
assert days_in_month(2023, 2) == 28
for m in (4, 6, 9, 11):
    assert days_in_month(2023, m) == 30
for m in (1, 3, 5, 7, 8, 10, 12):
    assert days_in_month(2023, m) == 31
''',
    ),
    dict(
        id="tests_numutil", kind="tests", module="numutil",
        files={"numutil.py": r'''
def clamp(x, lo, hi):
    if lo > hi:
        raise ValueError("lo must not exceed hi")
    return max(lo, min(x, hi))


def normalize(xs):
    """Scale numbers linearly to 0..1. An empty list gives []; all-equal values give zeros."""
    if not xs:
        return []
    lo, hi = min(xs), max(xs)
    if lo == hi:
        return [0.0 for _ in xs]
    return [(x - lo) / (hi - lo) for x in xs]
'''},
        instruction="Write tests for `clamp` and `normalize` in numutil.py.",
        mutants=[
            {"numutil.py": r'''
def clamp(x, lo, hi):
    return max(lo, min(x, hi))


def normalize(xs):
    if not xs:
        return []
    lo, hi = min(xs), max(xs)
    if lo == hi:
        return [0.0 for _ in xs]
    return [(x - lo) / (hi - lo) for x in xs]
'''},
            {"numutil.py": r'''
def clamp(x, lo, hi):
    if lo > hi:
        raise ValueError("lo must not exceed hi")
    return max(lo, min(x, hi))


def normalize(xs):
    if not xs:
        return []
    lo, hi = min(xs), max(xs)
    if lo == hi:
        return [1.0 for _ in xs]
    return [(x - lo) / (hi - lo) for x in xs]
'''},
            {"numutil.py": r'''
def clamp(x, lo, hi):
    if lo > hi:
        raise ValueError("lo must not exceed hi")
    return max(lo, min(x, hi - 1))


def normalize(xs):
    if not xs:
        return []
    lo, hi = min(xs), max(xs)
    if lo == hi:
        return [0.0 for _ in xs]
    return [(x - lo) / (hi - lo) for x in xs]
'''},
            {"numutil.py": r'''
def clamp(x, lo, hi):
    if lo > hi:
        raise ValueError("lo must not exceed hi")
    return max(lo, min(x, hi))


def normalize(xs):
    if not xs:
        return []
    lo, hi = min(xs), max(xs)
    if lo == hi:
        return [0.0 for _ in xs]
    return [(x - lo) / hi for x in xs]
'''},
        ],
        reference_tests=r'''
from numutil import clamp, normalize

assert clamp(5, 0, 10) == 5
assert clamp(-1, 0, 10) == 0
assert clamp(11, 0, 10) == 10
assert clamp(0, 0, 10) == 0
assert clamp(10, 0, 10) == 10
try:
    clamp(1, 5, 3)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert normalize([]) == []
assert normalize([5, 5]) == [0.0, 0.0]
assert normalize([2, 4, 6]) == [0.0, 0.5, 1.0]
assert normalize([10, 20]) == [0.0, 1.0]
''',
    ),
    dict(
        id="tests_bounded_stack", kind="tests", module="containers",
        files={"containers.py": r'''
class BoundedStack:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._items = []

    def push(self, x):
        if len(self._items) >= self.capacity:
            raise OverflowError("full")
        self._items.append(x)

    def pop(self):
        if not self._items:
            raise IndexError("empty")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("empty")
        return self._items[-1]

    def __len__(self):
        return len(self._items)
'''},
        instruction="Write tests for the `BoundedStack` class in containers.py.",
        mutants=[
            {"containers.py": r'''
class BoundedStack:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._items = []

    def push(self, x):
        if len(self._items) > self.capacity:
            raise OverflowError("full")
        self._items.append(x)

    def pop(self):
        if not self._items:
            raise IndexError("empty")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("empty")
        return self._items[-1]

    def __len__(self):
        return len(self._items)
'''},
            {"containers.py": r'''
class BoundedStack:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._items = []

    def push(self, x):
        if len(self._items) >= self.capacity:
            raise OverflowError("full")
        self._items.append(x)

    def pop(self):
        if not self._items:
            return None
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("empty")
        return self._items[-1]

    def __len__(self):
        return len(self._items)
'''},
            {"containers.py": r'''
class BoundedStack:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._items = []

    def push(self, x):
        if len(self._items) >= self.capacity:
            raise OverflowError("full")
        self._items.append(x)

    def pop(self):
        if not self._items:
            raise IndexError("empty")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("empty")
        return self._items.pop()

    def __len__(self):
        return len(self._items)
'''},
            {"containers.py": r'''
class BoundedStack:
    def __init__(self, capacity):
        self.capacity = capacity
        self._items = []

    def push(self, x):
        if len(self._items) >= self.capacity:
            raise OverflowError("full")
        self._items.append(x)

    def pop(self):
        if not self._items:
            raise IndexError("empty")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("empty")
        return self._items[-1]

    def __len__(self):
        return len(self._items)
'''},
        ],
        reference_tests=r'''
from containers import BoundedStack

s = BoundedStack(2)
assert len(s) == 0
s.push(1)
s.push(2)
assert len(s) == 2
try:
    s.push(3)
except OverflowError:
    pass
else:
    raise AssertionError("expected OverflowError")
assert s.peek() == 2 and len(s) == 2
assert s.pop() == 2
assert s.pop() == 1
for call in (s.pop, s.peek):
    try:
        call()
    except IndexError:
        pass
    else:
        raise AssertionError("expected IndexError")
try:
    BoundedStack(0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    ),
    dict(
        id="tests_top_words", kind="tests", module="wordfreq",
        files={"wordfreq.py": r'''
import re


def top_words(text, n=3):
    """Most frequent words, case-insensitive (letters and apostrophes only); ties are broken alphabetically."""
    words = re.findall(r"[a-z']+", text.lower())
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:n]]
'''},
        instruction="Write tests for `top_words(text, n=3)` in wordfreq.py (read its docstring for the exact rules).",
        mutants=[
            {"wordfreq.py": r'''
import re


def top_words(text, n=3):
    words = re.findall(r"[A-Za-z']+", text)
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:n]]
'''},
            {"wordfreq.py": r'''
import re


def top_words(text, n=3):
    words = re.findall(r"[a-z']+", text.lower())
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    return [w for w, _ in ranked[:n]]
'''},
            {"wordfreq.py": r'''
import re


def top_words(text, n=3):
    words = re.findall(r"[a-z']+", text.lower())
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:n + 1]]
'''},
            {"wordfreq.py": r'''
import re


def top_words(text, n=3):
    words = re.findall(r"[a-z]+", text.lower())
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:n]]
'''},
        ],
        reference_tests=r'''
from wordfreq import top_words

assert top_words("the cat the dog the cat", 2) == ["the", "cat"]
assert top_words("The the THE cat", 1) == ["the"]
assert top_words("b a c", 3) == ["a", "b", "c"]
assert top_words("a a b c", 2) == ["a", "b"]
assert top_words("don't don't can't", 1) == ["don't"]
assert top_words("", 3) == []
assert top_words("a b c d") == ["a", "b", "c"]
''',
    ),
    dict(
        id="tests_bank", kind="tests", module="bank",
        files={"bank.py": r'''
class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, owner, balance=0, frozen=False):
        self.owner = owner
        self.balance = balance
        self.frozen = frozen

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if self.frozen:
            raise ValueError("account frozen")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance:
            raise InsufficientFunds(self.owner)
        self.balance -= amount


def transfer(src, dst, amount):
    src.withdraw(amount)
    try:
        dst.deposit(amount)
    except Exception:
        src.balance += amount
        raise
'''},
        instruction="Write tests for `Account`, `InsufficientFunds` and `transfer` in bank.py.",
        mutants=[
            {"bank.py": r'''
class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, owner, balance=0, frozen=False):
        self.owner = owner
        self.balance = balance
        self.frozen = frozen

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if self.frozen:
            raise ValueError("account frozen")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance -= amount


def transfer(src, dst, amount):
    src.withdraw(amount)
    try:
        dst.deposit(amount)
    except Exception:
        src.balance += amount
        raise
'''},
            {"bank.py": r'''
class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, owner, balance=0, frozen=False):
        self.owner = owner
        self.balance = balance
        self.frozen = frozen

    def deposit(self, amount):
        if self.frozen:
            raise ValueError("account frozen")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance:
            raise InsufficientFunds(self.owner)
        self.balance -= amount


def transfer(src, dst, amount):
    src.withdraw(amount)
    try:
        dst.deposit(amount)
    except Exception:
        src.balance += amount
        raise
'''},
            {"bank.py": r'''
class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, owner, balance=0, frozen=False):
        self.owner = owner
        self.balance = balance
        self.frozen = frozen

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if self.frozen:
            raise ValueError("account frozen")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance:
            raise InsufficientFunds(self.owner)
        self.balance -= amount


def transfer(src, dst, amount):
    src.withdraw(amount)
    dst.deposit(amount)
'''},
            {"bank.py": r'''
class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, owner, balance=0, frozen=False):
        self.owner = owner
        self.balance = balance
        self.frozen = frozen

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance:
            raise InsufficientFunds(self.owner)
        self.balance -= amount


def transfer(src, dst, amount):
    src.withdraw(amount)
    try:
        dst.deposit(amount)
    except Exception:
        src.balance += amount
        raise
'''},
        ],
        reference_tests=r'''
from bank import Account, InsufficientFunds, transfer


def raises(exc, fn, *a):
    try:
        fn(*a)
    except exc:
        return True
    return False


a = Account("a", 100)
a.deposit(50)
assert a.balance == 150
a.withdraw(30)
assert a.balance == 120
assert raises(InsufficientFunds, a.withdraw, 500)
assert a.balance == 120
assert raises(ValueError, a.deposit, 0)
assert raises(ValueError, a.deposit, -5)
assert raises(ValueError, a.withdraw, 0)
f = Account("f", 10, frozen=True)
assert raises(ValueError, f.deposit, 5)
assert f.balance == 10
b = Account("b", 10)
transfer(a, b, 20)
assert (a.balance, b.balance) == (100, 30)
assert raises(ValueError, transfer, a, f, 10)
assert (a.balance, f.balance) == (100, 10)
assert raises(InsufficientFunds, transfer, a, b, 1000)
assert (a.balance, b.balance) == (100, 30)
''',
    ),
    dict(
        id="tests_textutil", kind="tests", module="textutil",
        files={"textutil.py": r'''
def slugify(s):
    """Lowercase; each run of non-alphanumeric characters becomes one '-'; no leading or trailing '-'."""
    out, prev_dash = [], False
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-")


def truncate(s, n, suffix="..."):
    """Return s unchanged if len(s) <= n, otherwise cut it so the result (with suffix) is exactly n characters."""
    if n < len(suffix):
        raise ValueError("n too small")
    if len(s) <= n:
        return s
    return s[: n - len(suffix)] + suffix
'''},
        instruction="Write tests for `slugify` and `truncate` in textutil.py (read the docstrings for the exact rules).",
        mutants=[
            {"textutil.py": r'''
def slugify(s):
    out, prev_dash = [], False
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out)


def truncate(s, n, suffix="..."):
    if n < len(suffix):
        raise ValueError("n too small")
    if len(s) <= n:
        return s
    return s[: n - len(suffix)] + suffix
'''},
            {"textutil.py": r'''
def slugify(s):
    out, prev_dash = [], False
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-")


def truncate(s, n, suffix="..."):
    if n < len(suffix):
        raise ValueError("n too small")
    if len(s) < n:
        return s
    return s[: n - len(suffix)] + suffix
'''},
            {"textutil.py": r'''
def slugify(s):
    out = []
    for ch in s.lower():
        out.append(ch if ch.isalnum() else "-")
    return "".join(out).strip("-")


def truncate(s, n, suffix="..."):
    if n < len(suffix):
        raise ValueError("n too small")
    if len(s) <= n:
        return s
    return s[: n - len(suffix)] + suffix
'''},
            {"textutil.py": r'''
def slugify(s):
    out, prev_dash = [], False
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-")


def truncate(s, n, suffix="..."):
    if len(s) <= n:
        return s
    return s[: n - len(suffix)] + suffix
'''},
        ],
        reference_tests=r'''
from textutil import slugify, truncate

assert slugify("Hello, World!") == "hello-world"
assert slugify("  a  b  ") == "a-b"
assert slugify("A--B") == "a-b"
assert slugify("") == ""
assert slugify("x") == "x"
assert truncate("hello", 5) == "hello"
assert truncate("hello world", 8) == "hello..."
assert truncate("abcdef", 4, "~") == "abc~"
assert truncate("hi", 10) == "hi"
try:
    truncate("hello world", 2)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    ),
]
