"""Harder fix-the-bug tasks: several files, the fault is not always in the file that fails."""

TASKS_FIX = [
    dict(
        id="fix_pricing_cart", kind="fix",
        files={
            "pricing.py": r'''
def apply_discount(price, percent):
    """Return price reduced by the given percentage (0-100), rounded to cents."""
    return round(price - percent, 2)
''',
            "cart.py": r'''
from pricing import apply_discount


class Cart:
    def __init__(self):
        self.items = []

    def add(self, name, price, qty=1):
        self.items.append((name, price, qty))

    def subtotal(self):
        return round(sum(p * q for _, p, q in self.items), 2)

    def total(self, discount_percent=0, tax_rate=0.0):
        discounted = apply_discount(self.subtotal(), discount_percent)
        return round(discounted * (1 + tax_rate), 2)
''',
        },
        tests=r'''
from cart import Cart

c = Cart()
c.add("pen", 2.5, 4)
c.add("book", 10.0)
assert c.subtotal() == 20.0
assert c.total() == 20.0
assert c.total(discount_percent=10) == 18.0
assert c.total(discount_percent=25, tax_rate=0.1) == 16.5
assert Cart().total(50) == 0.0
''',
        reference={"pricing.py": r'''
def apply_discount(price, percent):
    """Return price reduced by the given percentage (0-100), rounded to cents."""
    return round(price * (1 - percent / 100), 2)
'''},
    ),
    dict(
        id="fix_lru_recency", kind="fix",
        files={"lru.py": r'''
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self._d = OrderedDict()

    def get(self, key, default=None):
        return self._d.get(key, default)

    def put(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) > self.capacity:
            self._d.popitem(last=False)
'''},
        tests=r'''
from lru import LRUCache

c = LRUCache(2)
c.put("a", 1)
c.put("b", 2)
assert c.get("a") == 1
c.put("c", 3)
assert c.get("b") is None
assert c.get("a") == 1 and c.get("c") == 3
c.put("a", 10)
c.put("d", 4)
assert c.get("c") is None and c.get("a") == 10
''',
        reference={"lru.py": r'''
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self._d = OrderedDict()

    def get(self, key, default=None):
        if key in self._d:
            self._d.move_to_end(key)
            return self._d[key]
        return default

    def put(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) > self.capacity:
            self._d.popitem(last=False)
'''},
    ),
    dict(
        id="fix_calc_assoc", kind="fix",
        files={"calc.py": r'''
import re


def tokenize(s):
    return re.findall(r"\d+\.?\d*|[()+\-*/]", s)


class Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def eat(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def expr(self):
        left = self.term()
        if self.peek() in ("+", "-"):
            op = self.eat()
            right = self.expr()
            return left + right if op == "+" else left - right
        return left

    def term(self):
        left = self.factor()
        while self.peek() in ("*", "/"):
            op = self.eat()
            right = self.factor()
            left = left * right if op == "*" else left / right
        return left

    def factor(self):
        tok = self.eat()
        if tok == "(":
            v = self.expr()
            self.eat()
            return v
        if tok == "-":
            return -self.factor()
        return float(tok)


def evaluate(s):
    return Parser(tokenize(s)).expr()
'''},
        tests=r'''
from calc import evaluate

assert evaluate("2+3*4") == 14
assert evaluate("(1+2)*3") == 9
assert evaluate("-3+5") == 2
assert evaluate("10-3-2") == 5
assert evaluate("8-2-2-2") == 2
assert evaluate("1-2+3") == 2
''',
        reference={"calc.py": r'''
import re


def tokenize(s):
    return re.findall(r"\d+\.?\d*|[()+\-*/]", s)


class Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def eat(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def expr(self):
        left = self.term()
        while self.peek() in ("+", "-"):
            op = self.eat()
            right = self.term()
            left = left + right if op == "+" else left - right
        return left

    def term(self):
        left = self.factor()
        while self.peek() in ("*", "/"):
            op = self.eat()
            right = self.factor()
            left = left * right if op == "*" else left / right
        return left

    def factor(self):
        tok = self.eat()
        if tok == "(":
            v = self.expr()
            self.eat()
            return v
        if tok == "-":
            return -self.factor()
        return float(tok)


def evaluate(s):
    return Parser(tokenize(s)).expr()
'''},
    ),
    dict(
        id="fix_csv_quotes", kind="fix",
        files={"csvparse.py": r'''
def parse_csv_line(line):
    """Split one CSV line. Fields may be quoted; inside quotes a doubled quote ("") is a literal quote."""
    fields, cur, in_q = [], [], False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_q:
            if ch == '"':
                in_q = False
            else:
                cur.append(ch)
        else:
            if ch == '"':
                in_q = True
            elif ch == ",":
                fields.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        i += 1
    fields.append("".join(cur))
    return fields
'''},
        tests=r'''
from csvparse import parse_csv_line

assert parse_csv_line("a,b,c") == ["a", "b", "c"]
assert parse_csv_line('a,"b,c",d') == ["a", "b,c", "d"]
assert parse_csv_line('"say ""hi""",x') == ['say "hi"', "x"]
assert parse_csv_line("") == [""]
assert parse_csv_line("a,,b") == ["a", "", "b"]
assert parse_csv_line('"",x') == ["", "x"]
''',
        reference={"csvparse.py": r'''
def parse_csv_line(line):
    """Split one CSV line. Fields may be quoted; inside quotes a doubled quote ("") is a literal quote."""
    fields, cur, in_q = [], [], False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_q:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    cur.append('"')
                    i += 1
                else:
                    in_q = False
            else:
                cur.append(ch)
        else:
            if ch == '"':
                in_q = True
            elif ch == ",":
                fields.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        i += 1
    fields.append("".join(cur))
    return fields
'''},
    ),
    dict(
        id="fix_token_bucket", kind="fix",
        files={"ratelimit.py": r'''
class TokenBucket:
    def __init__(self, capacity, refill_per_sec, now=0.0):
        self.capacity = capacity
        self.rate = refill_per_sec
        self.tokens = capacity
        self.last = now

    def allow(self, now, cost=1):
        elapsed = now - self.last
        self.tokens = self.tokens + elapsed * self.rate
        self.last = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
'''},
        tests=r'''
from ratelimit import TokenBucket

b = TokenBucket(2, 1.0)
assert b.allow(0) and b.allow(0) and not b.allow(0)
assert b.allow(1)
assert not b.allow(1)
assert b.allow(100) and b.allow(100) and not b.allow(100)
''',
        reference={"ratelimit.py": r'''
class TokenBucket:
    def __init__(self, capacity, refill_per_sec, now=0.0):
        self.capacity = capacity
        self.rate = refill_per_sec
        self.tokens = capacity
        self.last = now

    def allow(self, now, cost=1):
        elapsed = now - self.last
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
'''},
    ),
    dict(
        id="fix_graph_undirected", kind="fix",
        files={
            "graph.py": r'''
class Graph:
    """Undirected graph."""

    def __init__(self):
        self.adj = {}

    def add_edge(self, a, b):
        self.adj.setdefault(a, set()).add(b)
        self.adj.setdefault(b, set())

    def neighbors(self, n):
        return sorted(self.adj.get(n, ()))
''',
            "paths.py": r'''
from collections import deque


def shortest_path(g, src, dst):
    prev = {src: None}
    q = deque([src])
    while q:
        n = q.popleft()
        if n == dst:
            path = []
            while n is not None:
                path.append(n)
                n = prev[n]
            return path[::-1]
        for m in g.neighbors(n):
            if m not in prev:
                prev[m] = n
                q.append(m)
    return None
''',
        },
        tests=r'''
from graph import Graph
from paths import shortest_path

g = Graph()
g.add_edge("a", "b")
g.add_edge("b", "c")
g.add_edge("c", "d")
assert shortest_path(g, "a", "d") == ["a", "b", "c", "d"]
assert shortest_path(g, "d", "a") == ["d", "c", "b", "a"]
assert g.neighbors("b") == ["a", "c"]
g.add_edge("a", "d")
assert shortest_path(g, "d", "a") == ["d", "a"]
assert shortest_path(g, "a", "z") is None
''',
        reference={"graph.py": r'''
class Graph:
    """Undirected graph."""

    def __init__(self):
        self.adj = {}

    def add_edge(self, a, b):
        self.adj.setdefault(a, set()).add(b)
        self.adj.setdefault(b, set()).add(a)

    def neighbors(self, n):
        return sorted(self.adj.get(n, ()))
'''},
    ),
    dict(
        id="fix_paginate", kind="fix",
        files={"pagination.py": r'''
def paginate(items, page, per_page):
    """Return {"items", "total_pages", "has_next"} for a 1-indexed page."""
    total_pages = len(items) // per_page
    start = page * per_page
    return {
        "items": items[start:start + per_page],
        "total_pages": total_pages,
        "has_next": page < total_pages,
    }
'''},
        tests=r'''
from pagination import paginate

items = list(range(1, 11))
assert paginate(items, 1, 4) == {"items": [1, 2, 3, 4], "total_pages": 3, "has_next": True}
assert paginate(items, 3, 4) == {"items": [9, 10], "total_pages": 3, "has_next": False}
assert paginate([], 1, 5) == {"items": [], "total_pages": 0, "has_next": False}
assert paginate(items, 4, 4)["items"] == []
assert paginate(items, 2, 5) == {"items": [6, 7, 8, 9, 10], "total_pages": 2, "has_next": False}
''',
        reference={"pagination.py": r'''
import math


def paginate(items, page, per_page):
    """Return {"items", "total_pages", "has_next"} for a 1-indexed page."""
    total_pages = math.ceil(len(items) / per_page)
    start = (page - 1) * per_page
    return {
        "items": items[start:start + per_page],
        "total_pages": total_pages,
        "has_next": page < total_pages,
    }
'''},
    ),
    dict(
        id="fix_wrap_width", kind="fix",
        files={"wrap.py": r'''
def wrap(text, width):
    """Greedy word wrap: no line longer than width (a single longer word gets its own line)."""
    lines, cur = [], ""
    for word in text.split():
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) < width:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines
'''},
        tests=r'''
from wrap import wrap

assert wrap("the quick brown fox", 9) == ["the quick", "brown fox"]
assert wrap("", 5) == []
assert wrap("superlongword a", 5) == ["superlongword", "a"]
assert wrap("a b c", 3) == ["a b", "c"]
assert wrap("aa bb cc dd", 5) == ["aa bb", "cc dd"]
''',
        reference={"wrap.py": r'''
def wrap(text, width):
    """Greedy word wrap: no line longer than width (a single longer word gets its own line)."""
    lines, cur = [], ""
    for word in text.split():
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
    ),
    dict(
        id="fix_leap_calendar", kind="fix",
        files={"calendar_utils.py": r'''
def is_leap(year):
    return year % 4 == 0


def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31


def day_of_year(year, month, day):
    return sum(days_in_month(year, m) for m in range(1, month)) + day
'''},
        tests=r'''
from calendar_utils import is_leap, days_in_month, day_of_year

assert is_leap(2000) is True
assert is_leap(1900) is False
assert is_leap(2024) is True
assert is_leap(2023) is False
assert days_in_month(1900, 2) == 28
assert day_of_year(2000, 12, 31) == 366
assert day_of_year(1900, 3, 1) == 60
''',
        reference={"calendar_utils.py": r'''
def is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31


def day_of_year(year, month, day):
    return sum(days_in_month(year, m) for m in range(1, month)) + day
'''},
    ),
    dict(
        id="fix_transfer_rollback", kind="fix",
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
    dst.deposit(amount)
'''},
        tests=r'''
from bank import Account, InsufficientFunds, transfer

a, b = Account("a", 100), Account("b", 50)
transfer(a, b, 30)
assert (a.balance, b.balance) == (70, 80)

c = Account("c", 10, frozen=True)
try:
    transfer(a, c, 20)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert (a.balance, c.balance) == (70, 10)

try:
    transfer(a, b, 500)
except InsufficientFunds:
    pass
else:
    raise AssertionError("expected InsufficientFunds")
assert (a.balance, b.balance) == (70, 80)
''',
        reference={"bank.py": r'''
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
    ),
]
