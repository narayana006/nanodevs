"""Refactor tasks: working code is restructured; behaviour must not change. Hidden tests check old behaviour AND the new structure."""
from common import feat


def R(id, diff, topic, files, instruction, visible, hidden, replace):
    return feat(id, diff, topic, files, instruction, visible, hidden, replace=replace, kind="refactor")


TASKS_REFACTOR = [
    R("py_ref_extract_normalize", "easy", "extract-function",
      {"names.py": r'''
def initials(name):
    parts = name.strip().split()
    parts = [p.capitalize() for p in parts if p]
    return ".".join(p[0] for p in parts) + ("." if parts else "")


def display(name):
    parts = name.strip().split()
    parts = [p.capitalize() for p in parts if p]
    return " ".join(parts)


def sort_key(name):
    parts = name.strip().split()
    parts = [p.capitalize() for p in parts if p]
    return (parts[-1] if parts else "", parts[:-1])
'''},
      "Three functions repeat the same normalisation. Extract it into a module-level helper `_clean_parts(name)` (returns the list of capitalised words) and make "
      "initials, display and sort_key all use it. Behaviour must not change.",
      "import names\nassert names._clean_parts('  ada  LOVELACE ') == ['Ada', 'Lovelace']\n",
      r'''
import names
assert names._clean_parts("  ada  LOVELACE ") == ["Ada", "Lovelace"] and names._clean_parts("") == []
assert names.initials("ada byron lovelace") == "A.B.L." and names.initials("  ") == ""
assert names.display("  ada   LOVELACE") == "Ada Lovelace" and names.display("") == ""
assert names.sort_key("ada king lovelace") == ("Lovelace", ["Ada", "King"]) and names.sort_key("") == ("", [])
names._clean_parts = lambda n: ["Zed", "Q"]
assert names.initials("x") == "Z.Q." and names.display("x") == "Zed Q" and names.sort_key("x") == ("Q", ["Zed"])
''',
      {"names.py": r'''
def _clean_parts(name):
    return [p.capitalize() for p in name.strip().split() if p]


def initials(name):
    parts = _clean_parts(name)
    return ".".join(p[0] for p in parts) + ("." if parts else "")


def display(name):
    return " ".join(_clean_parts(name))


def sort_key(name):
    parts = _clean_parts(name)
    return (parts[-1] if parts else "", parts[:-1])
'''}),
    R("py_ref_dispatch_table", "easy", "dispatch",
      {"shapes.py": r'''
import math


def area(kind, *dims):
    if kind == "circle":
        return math.pi * dims[0] ** 2
    elif kind == "square":
        return dims[0] ** 2
    elif kind == "rect":
        return dims[0] * dims[1]
    elif kind == "triangle":
        return 0.5 * dims[0] * dims[1]
    elif kind == "ellipse":
        return math.pi * dims[0] * dims[1]
    else:
        raise ValueError("unknown shape: " + kind)
'''},
      "Replace the if/elif chain with a module-level dict `AREA_FUNCS` mapping each shape name to a function of its dimensions, and add `register(kind, fn)` that adds a new "
      "shape to the table. `area(kind, *dims)` must keep returning the same values and keep raising ValueError('unknown shape: ...') for unknown kinds.",
      "import shapes\nassert 'circle' in shapes.AREA_FUNCS\n",
      r'''
import math
import shapes
assert set(shapes.AREA_FUNCS) == {"circle", "square", "rect", "triangle", "ellipse"}
assert shapes.area("square", 3) == 9 and shapes.area("rect", 2, 5) == 10 and shapes.area("triangle", 4, 5) == 10.0
assert abs(shapes.area("circle", 1) - math.pi) < 1e-12 and abs(shapes.area("ellipse", 2, 3) - 6 * math.pi) < 1e-12
try:
    shapes.area("hexagon", 1)
    assert False
except ValueError as e:
    assert str(e) == "unknown shape: hexagon"
shapes.register("cube_face", lambda s: s * s)
assert shapes.area("cube_face", 4) == 16
shapes.AREA_FUNCS["square"] = lambda s: -1
assert shapes.area("square", 3) == -1
''',
      {"shapes.py": r'''
import math

AREA_FUNCS = {
    "circle": lambda r: math.pi * r ** 2,
    "square": lambda s: s ** 2,
    "rect": lambda w, h: w * h,
    "triangle": lambda b, h: 0.5 * b * h,
    "ellipse": lambda a, b: math.pi * a * b,
}


def register(kind, fn):
    AREA_FUNCS[kind] = fn


def area(kind, *dims):
    if kind not in AREA_FUNCS:
        raise ValueError("unknown shape: " + kind)
    return AREA_FUNCS[kind](*dims)
'''}),
    R("py_ref_global_to_class", "medium", "encapsulation",
      {"ids.py": r'''
_counter = 0
_prefix = "id"


def set_prefix(p):
    global _prefix
    _prefix = p


def next_id():
    global _counter
    _counter += 1
    return "%s-%04d" % (_prefix, _counter)


def reset():
    global _counter
    _counter = 0
'''},
      "The module keeps its state in globals. Introduce `class IdGenerator(prefix='id')` with methods `next_id()`, `reset()` and `set_prefix(p)` holding independent state per "
      "instance, and keep the three module-level functions working with the same behaviour by delegating to a module-level default instance `default` (an IdGenerator). "
      "No `global` statements may remain.",
      "import ids\nassert ids.IdGenerator('a').next_id() == 'a-0001'\n",
      r'''
import ast
import ids
a, b = ids.IdGenerator("a"), ids.IdGenerator()
assert a.next_id() == "a-0001" and a.next_id() == "a-0002" and b.next_id() == "id-0001"
a.reset()
assert a.next_id() == "a-0001" and b.next_id() == "id-0002"
b.set_prefix("b")
assert b.next_id() == "b-0003"
assert isinstance(ids.default, ids.IdGenerator)
assert ids.next_id() == "id-0001" and ids.next_id() == "id-0002"
ids.set_prefix("z")
assert ids.next_id() == "z-0003"
ids.reset()
assert ids.next_id() == "z-0001"
assert ids.default.next_id() == "z-0002"
src = open(ids.__file__).read()
assert not any(isinstance(n, ast.Global) for n in ast.walk(ast.parse(src)))
''',
      {"ids.py": r'''
class IdGenerator:
    def __init__(self, prefix="id"):
        self._prefix = prefix
        self._counter = 0

    def set_prefix(self, p):
        self._prefix = p

    def next_id(self):
        self._counter += 1
        return "%s-%04d" % (self._prefix, self._counter)

    def reset(self):
        self._counter = 0


default = IdGenerator()


def set_prefix(p):
    default.set_prefix(p)


def next_id():
    return default.next_id()


def reset():
    default.reset()
'''}),
    R("py_ref_lazy_generator", "medium", "generators",
      {"seq.py": r'''
def collatz(n):
    """Return the full Collatz sequence from n down to 1 as a list."""
    out = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        out.append(n)
    return out


def evens_squared(limit):
    """Squares of the even numbers below limit, as a list."""
    out = []
    for i in range(limit):
        if i % 2 == 0:
            out.append(i * i)
    return out
'''},
      "Add lazy generator versions `iter_collatz(n)` and `iter_evens_squared(limit)` (they yield the same values one by one) and rewrite `collatz` and `evens_squared` "
      "to return `list(...)` of them, so the logic exists only once. The list-returning functions must behave exactly as before.",
      "import seq\nassert next(seq.iter_collatz(6)) == 6\n",
      r'''
import inspect
import seq
assert inspect.isgeneratorfunction(seq.iter_collatz) and inspect.isgeneratorfunction(seq.iter_evens_squared)
assert seq.collatz(6) == [6, 3, 10, 5, 16, 8, 4, 2, 1] and seq.collatz(1) == [1]
assert list(seq.iter_collatz(6)) == seq.collatz(6)
assert seq.evens_squared(7) == [0, 4, 16, 36] and seq.evens_squared(0) == []
g = seq.iter_evens_squared(10 ** 12)
assert next(g) == 0 and next(g) == 4 and next(g) == 16
assert not inspect.isgeneratorfunction(seq.collatz) and isinstance(seq.collatz(7), list)
seq.iter_collatz = lambda n: iter([42])
assert seq.collatz(5) == [42]
seq.iter_evens_squared = lambda n: iter([7, 8])
assert seq.evens_squared(5) == [7, 8]
''',
      {"seq.py": r'''
def iter_collatz(n):
    yield n
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        yield n


def collatz(n):
    """Return the full Collatz sequence from n down to 1 as a list."""
    return list(iter_collatz(n))


def iter_evens_squared(limit):
    for i in range(0, limit, 2):
        yield i * i


def evens_squared(limit):
    """Squares of the even numbers below limit, as a list."""
    return list(iter_evens_squared(limit))
'''}),
    R("py_ref_rules_list", "medium", "strategy",
      {"discounts.py": r'''
def final_price(price, qty, is_member, coupon):
    total = price * qty
    if qty >= 10:
        total = total * 0.90
    elif qty >= 5:
        total = total * 0.95
    if is_member:
        total = total * 0.97
    if coupon == "HALF":
        total = total * 0.5
    elif coupon == "TENOFF":
        total = max(total - 10, 0)
    return round(total, 2)
'''},
      "Refactor into a list `RULES` of small functions `rule(total, qty, is_member, coupon) -> total`, applied in order by `final_price`: `bulk_rule`, `member_rule`, `coupon_rule` "
      "(each a module-level function, in that order in RULES). `final_price` must return exactly the same results as before (rounded to 2 decimals at the end only).",
      "import discounts\nassert [r.__name__ for r in discounts.RULES] == ['bulk_rule', 'member_rule', 'coupon_rule']\n",
      r'''
import discounts as d
assert [r.__name__ for r in d.RULES] == ["bulk_rule", "member_rule", "coupon_rule"]
assert d.bulk_rule(100.0, 10, False, None) == 90.0 and d.bulk_rule(100.0, 5, False, None) == 95.0 and d.bulk_rule(100.0, 4, False, None) == 100.0
assert d.member_rule(100.0, 1, True, None) == 97.0 and d.member_rule(100.0, 1, False, None) == 100.0
assert d.coupon_rule(100.0, 1, False, "HALF") == 50.0 and d.coupon_rule(5.0, 1, False, "TENOFF") == 0 and d.coupon_rule(50.0, 1, False, "x") == 50.0
assert d.final_price(10.0, 1, False, None) == 10.0
assert d.final_price(10.0, 10, True, "HALF") == round(100 * 0.9 * 0.97 * 0.5, 2)
assert d.final_price(3.0, 5, False, "TENOFF") == 4.25
assert d.final_price(20.0, 6, True, "TENOFF") == round(120 * 0.95 * 0.97 - 10, 2)
assert d.final_price(1.0, 1, True, "TENOFF") == 0
d.RULES.append(lambda total, q, m, c: total + 1)
assert d.final_price(10.0, 1, False, None) == 11.0
''',
      {"discounts.py": r'''
def bulk_rule(total, qty, is_member, coupon):
    if qty >= 10:
        return total * 0.90
    if qty >= 5:
        return total * 0.95
    return total


def member_rule(total, qty, is_member, coupon):
    return total * 0.97 if is_member else total


def coupon_rule(total, qty, is_member, coupon):
    if coupon == "HALF":
        return total * 0.5
    if coupon == "TENOFF":
        return max(total - 10, 0)
    return total


RULES = [bulk_rule, member_rule, coupon_rule]


def final_price(price, qty, is_member, coupon):
    total = price * qty
    for rule in RULES:
        total = rule(total, qty, is_member, coupon)
    return round(total, 2)
'''}),
    R("py_ref_tuple_to_dataclass", "medium", "dataclasses",
      {"staff.py": r'''
def make(name, dept, salary):
    return (name, dept, salary)


def raise_salary(rec, pct):
    return (rec[0], rec[1], round(rec[2] * (1 + pct / 100), 2))


def by_dept(records):
    out = {}
    for rec in records:
        out.setdefault(rec[1], []).append(rec[0])
    return out


def payroll(records):
    return sum(rec[2] for rec in records)
'''},
      "Records are bare tuples with magic indexes. Introduce `@dataclass(frozen=True) class Employee` with fields name, dept, salary and a `to_tuple()` method; `make` returns an "
      "Employee; `raise_salary`, `by_dept` and `payroll` work on Employee objects with the same results as before (raise_salary returns a new Employee).",
      "import staff\ne = staff.make('a', 'x', 10)\nassert e.name == 'a' and e.to_tuple() == ('a', 'x', 10)\n",
      r'''
import dataclasses
import staff
e = staff.make("ann", "eng", 100.0)
assert isinstance(e, staff.Employee) and (e.name, e.dept, e.salary) == ("ann", "eng", 100.0) and e.to_tuple() == ("ann", "eng", 100.0)
assert dataclasses.is_dataclass(e)
try:
    e.salary = 1
    assert False
except dataclasses.FrozenInstanceError:
    pass
r = staff.raise_salary(e, 10)
assert isinstance(r, staff.Employee) and r.salary == 110.0 and e.salary == 100.0 and r.name == "ann"
recs = [e, staff.make("bob", "eng", 50.0), staff.make("cy", "ops", 70.0)]
assert staff.by_dept(recs) == {"eng": ["ann", "bob"], "ops": ["cy"]}
assert staff.payroll(recs) == 220.0 and staff.payroll([]) == 0
assert staff.make("a", "b", 1) == staff.make("a", "b", 1)
''',
      {"staff.py": r'''
from dataclasses import dataclass


@dataclass(frozen=True)
class Employee:
    name: str
    dept: str
    salary: float

    def to_tuple(self):
        return (self.name, self.dept, self.salary)


def make(name, dept, salary):
    return Employee(name, dept, salary)


def raise_salary(rec, pct):
    return Employee(rec.name, rec.dept, round(rec.salary * (1 + pct / 100), 2))


def by_dept(records):
    out = {}
    for rec in records:
        out.setdefault(rec.dept, []).append(rec.name)
    return out


def payroll(records):
    return sum(rec.salary for rec in records)
'''}),
    R("py_ref_split_pipeline", "medium", "extract-function",
      {"orders.py": r'''
def process(rows):
    """rows: list of dicts with 'sku', 'qty', 'price'. Returns {'valid': [...], 'rejected': n, 'revenue': float, 'by_sku': {...}}."""
    valid = []
    rejected = 0
    for r in rows:
        if not isinstance(r.get("sku"), str) or not r["sku"]:
            rejected += 1
            continue
        if not isinstance(r.get("qty"), int) or r["qty"] <= 0:
            rejected += 1
            continue
        if not isinstance(r.get("price"), (int, float)) or r["price"] < 0:
            rejected += 1
            continue
        valid.append({"sku": r["sku"].strip().upper(), "qty": r["qty"], "price": float(r["price"])})
    revenue = 0.0
    by_sku = {}
    for r in valid:
        line = r["qty"] * r["price"]
        revenue += line
        by_sku[r["sku"]] = round(by_sku.get(r["sku"], 0.0) + line, 2)
    return {"valid": valid, "rejected": rejected, "revenue": round(revenue, 2), "by_sku": by_sku}
'''},
      "`process` does three jobs inline. Split it into `is_valid(row)` (True/False for one raw row), `normalize(row)` (the cleaned dict for a valid row) and `summarize(valid_rows)` "
      "(returns {'revenue': ..., 'by_sku': ...}), and make `process` compose them. Output of `process` must not change.",
      "import orders\nassert orders.is_valid({'sku': 'a', 'qty': 1, 'price': 2})\n",
      r'''
import orders as o
good = {"sku": " ab ", "qty": 2, "price": 1.5}
assert o.is_valid(good) is True and o.is_valid({"sku": "", "qty": 1, "price": 1}) is False
assert o.is_valid({"sku": "a", "qty": 0, "price": 1}) is False and o.is_valid({"sku": "a", "qty": 1.5, "price": 1}) is False
assert o.is_valid({"sku": "a", "qty": 1, "price": -1}) is False and o.is_valid({"sku": "a", "qty": 1}) is False and o.is_valid({"sku": 5, "qty": 1, "price": 1}) is False
assert o.normalize(good) == {"sku": "AB", "qty": 2, "price": 1.5}
assert o.summarize([{"sku": "A", "qty": 2, "price": 1.5}, {"sku": "A", "qty": 1, "price": 1.0}, {"sku": "B", "qty": 3, "price": 0.1}]) == {"revenue": 4.3, "by_sku": {"A": 4.0, "B": 0.3}}
rows = [good, {"sku": "x", "qty": -1, "price": 1}, {"sku": "ab", "qty": 1, "price": 2}, {"qty": 1, "price": 1}]
assert o.process(rows) == {"valid": [{"sku": "AB", "qty": 2, "price": 1.5}, {"sku": "AB", "qty": 1, "price": 2.0}], "rejected": 2, "revenue": 5.0, "by_sku": {"AB": 5.0}}
assert o.process([]) == {"valid": [], "rejected": 0, "revenue": 0.0, "by_sku": {}}
calls = []
o.is_valid = lambda r: calls.append(r) or False
assert o.process([good])["rejected"] == 1 and calls == [good]
''',
      {"orders.py": r'''
def is_valid(r):
    if not isinstance(r.get("sku"), str) or not r["sku"]:
        return False
    if not isinstance(r.get("qty"), int) or r["qty"] <= 0:
        return False
    if not isinstance(r.get("price"), (int, float)) or r["price"] < 0:
        return False
    return True


def normalize(r):
    return {"sku": r["sku"].strip().upper(), "qty": r["qty"], "price": float(r["price"])}


def summarize(valid):
    revenue = 0.0
    by_sku = {}
    for r in valid:
        line = r["qty"] * r["price"]
        revenue += line
        by_sku[r["sku"]] = round(by_sku.get(r["sku"], 0.0) + line, 2)
    return {"revenue": round(revenue, 2), "by_sku": by_sku}


def process(rows):
    """rows: list of dicts with 'sku', 'qty', 'price'."""
    valid = [normalize(r) for r in rows if is_valid(r)]
    out = summarize(valid)
    return {"valid": valid, "rejected": len(rows) - len(valid), "revenue": out["revenue"], "by_sku": out["by_sku"]}
'''}),
    R("py_ref_move_modules", "medium", "multi-file",
      {"utils.py": r'''
import math


def area_circle(r):
    return math.pi * r * r


def perimeter_rect(w, h):
    return 2 * (w + h)


def slugify(s):
    return "-".join(s.lower().split())


def truncate(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"
''', "app.py": r'''
from utils import area_circle, slugify


def describe(name, r):
    return "%s: %.2f" % (slugify(name), area_circle(r))
'''},
      "utils.py has grown into a grab-bag. Move the geometry functions (`area_circle`, `perimeter_rect`) into a new module `geometry.py` and the text functions (`slugify`, `truncate`) "
      "into a new module `textutil.py`. utils.py must keep working for old callers by re-exporting all four names (the same function objects). Update app.py to import from the "
      "new modules directly. Behaviour must not change.",
      "import geometry, textutil\nassert geometry.perimeter_rect(1, 2) == 6 and textutil.slugify('A B') == 'a-b'\n",
      r'''
import geometry, textutil, utils, app, ast
assert geometry.perimeter_rect(1, 2) == 6 and abs(geometry.area_circle(1) - 3.141592653589793) < 1e-12
assert textutil.slugify("Hello  Big World") == "hello-big-world" and textutil.truncate("abcdef", 4) == "abc…" and textutil.truncate("abc", 3) == "abc"
for mod, names in ((geometry, ["area_circle", "perimeter_rect"]), (textutil, ["slugify", "truncate"])):
    for n in names:
        assert getattr(utils, n) is getattr(mod, n), n
        assert getattr(mod, n).__module__ == mod.__name__
assert app.describe("My Circle", 2) == "my-circle: 12.57"
tree = ast.parse(open(app.__file__).read())
mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
assert "utils" not in mods and {"geometry", "textutil"} <= mods
assert "def " not in open(utils.__file__).read()
''',
      {"geometry.py": r'''
import math


def area_circle(r):
    return math.pi * r * r


def perimeter_rect(w, h):
    return 2 * (w + h)
''', "textutil.py": r'''
def slugify(s):
    return "-".join(s.lower().split())


def truncate(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"
''', "utils.py": r'''
from geometry import area_circle, perimeter_rect
from textutil import slugify, truncate

__all__ = ["area_circle", "perimeter_rect", "slugify", "truncate"]
''', "app.py": r'''
from geometry import area_circle
from textutil import slugify


def describe(name, r):
    return "%s: %.2f" % (slugify(name), area_circle(r))
'''}),
    R("py_ref_flatten_nesting", "medium", "readability",
      {"grades.py": r'''
def grade(student):
    result = "invalid"
    if student is not None:
        if "scores" in student:
            if len(student["scores"]) > 0:
                total = 0
                for s in student["scores"]:
                    if s is not None:
                        if 0 <= s <= 100:
                            total += s
                        else:
                            return "invalid"
                avg = total / len(student["scores"])
                if avg >= 90:
                    result = "A"
                else:
                    if avg >= 80:
                        result = "B"
                    else:
                        if avg >= 70:
                            result = "C"
                        else:
                            result = "F"
    return result
'''},
      "Rewrite `grade` with guard clauses and early returns so that no statement is nested more than 3 levels deep inside the function body (count only if/for/while/try/with "
      "blocks), without changing behaviour. A None score counts as 0 toward the average but still divides by the full list length; any score outside 0..100 makes the result "
      "'invalid'.",
      "import grades\nassert grades.grade({'scores': [95, 91]}) == 'A'\n",
      r'''
import ast
import grades
g = grades.grade
assert g({"scores": [95, 91]}) == "A" and g({"scores": [85, 80]}) == "B" and g({"scores": [70, 75]}) == "C" and g({"scores": [10, 20]}) == "F"
assert g({"scores": [90]}) == "A" and g({"scores": [80]}) == "B" and g({"scores": [70]}) == "C" and g({"scores": [69.9]}) == "F"
assert g(None) == "invalid" and g({}) == "invalid" and g({"scores": []}) == "invalid"
assert g({"scores": [50, 101]}) == "invalid" and g({"scores": [-1]}) == "invalid"
assert g({"scores": [None, 100, 100, 100]}) == "C" and g({"scores": [None]}) == "F"
assert g({"scores": [100, 101, None]}) == "invalid"
fn = [n for n in ast.parse(open(grades.__file__).read()).body if isinstance(n, ast.FunctionDef) and n.name == "grade"][0]


def depth(node, d=0):
    best = d
    for ch in ast.iter_child_nodes(node):
        nd = d + 1 if isinstance(ch, (ast.If, ast.For, ast.While, ast.Try, ast.With)) else d
        best = max(best, depth(ch, nd))
    return best


assert depth(fn) <= 3, depth(fn)
''',
      {"grades.py": r'''
def grade(student):
    if not student or not student.get("scores"):
        return "invalid"
    scores = student["scores"]
    total = 0
    for s in scores:
        if s is None:
            continue
        if not 0 <= s <= 100:
            return "invalid"
        total += s
    avg = total / len(scores)
    if avg >= 90:
        return "A"
    if avg >= 80:
        return "B"
    if avg >= 70:
        return "C"
    return "F"
'''}),
    R("py_ref_no_loops", "easy", "idioms",
      {"coll.py": r'''
def squares_of_evens(nums):
    out = []
    for n in nums:
        if n % 2 == 0:
            out.append(n * n)
    return out


def lengths_by_word(words):
    out = {}
    for w in words:
        out[w] = len(w)
    return out


def any_negative(nums):
    for n in nums:
        if n < 0:
            return True
    return False


def total_len(words):
    t = 0
    for w in words:
        t += len(w)
    return t
'''},
      "Rewrite these four functions in idiomatic style using comprehensions and builtins (any/sum): the function bodies must contain no `for` or `while` statements (comprehensions "
      "and generator expressions are fine). Behaviour must not change.",
      "import coll\nassert coll.squares_of_evens([1, 2, 4]) == [4, 16]\n",
      r'''
import ast
import coll
assert coll.squares_of_evens([1, 2, 3, 4, -2]) == [4, 16, 4] and coll.squares_of_evens([]) == []
assert coll.lengths_by_word(["a", "bb", "a"]) == {"a": 1, "bb": 2} and coll.lengths_by_word([]) == {}
assert coll.any_negative([1, -1]) is True and coll.any_negative([0, 1]) is False and coll.any_negative([]) is False
assert coll.total_len(["ab", "c", ""]) == 3 and coll.total_len([]) == 0
assert coll.squares_of_evens(x for x in range(5)) == [0, 4, 16]
tree = ast.parse(open(coll.__file__).read())
for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
    assert not any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(fn)), fn.name
assert len([n for n in tree.body if isinstance(n, ast.FunctionDef)]) == 4
''',
      {"coll.py": r'''
def squares_of_evens(nums):
    return [n * n for n in nums if n % 2 == 0]


def lengths_by_word(words):
    return {w: len(w) for w in words}


def any_negative(nums):
    return any(n < 0 for n in nums)


def total_len(words):
    return sum(len(w) for w in words)
'''}),
    R("py_ref_context_manager", "medium", "idioms",
      {"timing.py": r'''
class FakeClock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t


def timed_call(clock, fn, *args):
    """Call fn(*args); return (result, elapsed seconds measured by clock). Elapsed is recorded even if fn raises? No: exceptions propagate."""
    start = clock.now()
    result = fn(*args)
    return result, clock.now() - start
'''},
      "Add `class Timer(clock)` usable as a context manager: entering records the start time (clock.now()), exiting records `elapsed` (also when the body raises, and the exception still "
      "propagates). `elapsed` is None before exit. Then rewrite `timed_call` to use Timer so the timing logic lives in one place; its behaviour is unchanged.",
      "import timing\nc = timing.FakeClock()\nwith timing.Timer(c) as t:\n    c.t += 2\nassert t.elapsed == 2\n",
      r'''
import timing
c = timing.FakeClock()
with timing.Timer(c) as t:
    assert t.elapsed is None
    c.t += 2.5
assert t.elapsed == 2.5
try:
    with timing.Timer(c) as t2:
        c.t += 1
        raise KeyError("boom")
except KeyError:
    pass
assert t2.elapsed == 1
def work(x):
    c.t += 3
    return x * 2
assert timing.timed_call(c, work, 4) == (8, 3)
def bad():
    c.t += 1
    raise ValueError("no")
try:
    timing.timed_call(c, bad)
    assert False
except ValueError:
    pass
used = []
orig = timing.Timer.__enter__
def spy(self):
    used.append(1)
    return orig(self)
timing.Timer.__enter__ = spy
timing.timed_call(c, work, 1)
assert used == [1]
''',
      {"timing.py": r'''
class FakeClock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t


class Timer:
    def __init__(self, clock):
        self.clock = clock
        self.elapsed = None
        self._start = None

    def __enter__(self):
        self._start = self.clock.now()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = self.clock.now() - self._start
        return False


def timed_call(clock, fn, *args):
    """Call fn(*args); return (result, elapsed seconds measured by clock). Exceptions propagate."""
    with Timer(clock) as t:
        result = fn(*args)
    return result, t.elapsed
'''}),
    R("py_ref_enum_status", "medium", "types",
      {"tickets.py": r'''
def can_move(status, new_status):
    if status == "open":
        return new_status in ("in_progress", "closed")
    if status == "in_progress":
        return new_status in ("open", "review", "closed")
    if status == "review":
        return new_status in ("in_progress", "closed")
    return False


def label(status):
    if status == "open":
        return "Open"
    if status == "in_progress":
        return "In progress"
    if status == "review":
        return "In review"
    if status == "closed":
        return "Closed"
    raise ValueError("bad status: %r" % (status,))
'''},
      "Replace the magic strings with `class Status(str, Enum)` (members OPEN='open', IN_PROGRESS='in_progress', REVIEW='review', CLOSED='closed'), a module-level dict "
      "`TRANSITIONS` mapping each Status to the set of Statuses it may move to, and a dict `LABELS`. `can_move` and `label` must accept either Status members or the plain strings "
      "and return what they returned before (an unknown or non-str status in `label` raises ValueError('bad status: ...'); `can_move` with an unknown status returns False).",
      "import tickets\nassert tickets.Status.OPEN == 'open'\n",
      r'''
import tickets as t
from enum import Enum
S = t.Status
assert issubclass(S, Enum) and issubclass(S, str) and [s.value for s in S] == ["open", "in_progress", "review", "closed"]
assert set(t.TRANSITIONS) == set(S) and t.TRANSITIONS[S.CLOSED] == set()
assert t.TRANSITIONS[S.OPEN] == {S.IN_PROGRESS, S.CLOSED} and t.TRANSITIONS[S.REVIEW] == {S.IN_PROGRESS, S.CLOSED}
assert t.can_move("open", "in_progress") and t.can_move(S.OPEN, S.CLOSED) and t.can_move("in_progress", S.REVIEW)
assert not t.can_move("open", "review") and not t.can_move("closed", "open") and not t.can_move("nope", "open") and not t.can_move("open", "nope")
assert t.can_move(S.IN_PROGRESS, "open")
assert t.label("in_progress") == "In progress" and t.label(S.REVIEW) == "In review" and t.label("open") == "Open" and t.label(S.CLOSED) == "Closed"
assert set(t.LABELS) == set(S)
for bad in ("nope", None, 3):
    try:
        t.label(bad)
        assert False
    except ValueError as e:
        assert str(e).startswith("bad status:")
''',
      {"tickets.py": r'''
from enum import Enum


class Status(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    CLOSED = "closed"


TRANSITIONS = {
    Status.OPEN: {Status.IN_PROGRESS, Status.CLOSED},
    Status.IN_PROGRESS: {Status.OPEN, Status.REVIEW, Status.CLOSED},
    Status.REVIEW: {Status.IN_PROGRESS, Status.CLOSED},
    Status.CLOSED: set(),
}

LABELS = {
    Status.OPEN: "Open",
    Status.IN_PROGRESS: "In progress",
    Status.REVIEW: "In review",
    Status.CLOSED: "Closed",
}


def _coerce(s):
    try:
        return Status(s)
    except ValueError:
        return None


def can_move(status, new_status):
    a, b = _coerce(status), _coerce(new_status)
    return a is not None and b is not None and b in TRANSITIONS[a]


def label(status):
    s = _coerce(status)
    if s is None:
        raise ValueError("bad status: %r" % (status,))
    return LABELS[s]
'''}),
    R("py_ref_base_class", "medium", "inheritance",
      {"animals.py": r'''
class Dog:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return "%s the %s says %s" % (self.name, "dog", "Woof")

    def speak_n(self, n):
        return " ".join(["Woof"] * n)


class Cat:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return "%s the %s says %s" % (self.name, "cat", "Meow")

    def speak_n(self, n):
        return " ".join(["Meow"] * n)


class Cow:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return "%s the %s says %s" % (self.name, "cow", "Moo")

    def speak_n(self, n):
        return " ".join(["Moo"] * n)
'''},
      "Remove the duplication with a base class `Animal` that implements `__init__`, `describe` and `speak_n` once, driven by class attributes `species` and `sound`. "
      "Dog, Cat and Cow become subclasses that only set those two attributes (they must not define their own methods). Behaviour is unchanged; a new subclass that only "
      "sets the two attributes must work.",
      "import animals\nassert issubclass(animals.Dog, animals.Animal)\n",
      r'''
import animals as a
for cls, species, sound in ((a.Dog, "dog", "Woof"), (a.Cat, "cat", "Meow"), (a.Cow, "cow", "Moo")):
    assert issubclass(cls, a.Animal) and cls.species == species and cls.sound == sound
    assert {k for k in vars(cls) if not k.startswith("__")} == {"species", "sound"}, vars(cls).keys()
    x = cls("Bo")
    assert x.name == "Bo" and x.describe() == "Bo the %s says %s" % (species, sound)
    assert x.speak_n(3) == " ".join([sound] * 3) and x.speak_n(0) == ""
class Duck(a.Animal):
    species = "duck"
    sound = "Quack"
assert Duck("D").describe() == "D the duck says Quack" and Duck("D").speak_n(2) == "Quack Quack"
''',
      {"animals.py": r'''
class Animal:
    species = "animal"
    sound = "..."

    def __init__(self, name):
        self.name = name

    def describe(self):
        return "%s the %s says %s" % (self.name, self.species, self.sound)

    def speak_n(self, n):
        return " ".join([self.sound] * n)


class Dog(Animal):
    species = "dog"
    sound = "Woof"


class Cat(Animal):
    species = "cat"
    sound = "Meow"


class Cow(Animal):
    species = "cow"
    sound = "Moo"
'''}),
    R("py_ref_memoize_decorator", "medium", "decorators",
      {"memo.py": r'''
_fib_cache = {}
_paths_cache = {}


def fib(n):
    if n in _fib_cache:
        return _fib_cache[n]
    r = n if n < 2 else fib(n - 1) + fib(n - 2)
    _fib_cache[n] = r
    return r


def grid_paths(r, c):
    key = (r, c)
    if key in _paths_cache:
        return _paths_cache[key]
    res = 1 if r == 0 or c == 0 else grid_paths(r - 1, c) + grid_paths(r, c - 1)
    _paths_cache[key] = res
    return res
'''},
      "Both functions hand-roll the same cache. Add a decorator `memoize(fn)` in memo.py (positional-hashable arguments only) that returns a wrapper with a `cache` dict attribute "
      "(args tuple -> result) and a `calls` int attribute counting how many times the WRAPPED function body actually ran; apply it to `fib` and `grid_paths` and delete the "
      "module-level cache dicts. `functools.wraps` semantics (`__name__`) must be preserved. Results are unchanged.",
      "import memo\nassert memo.fib(10) == 55 and memo.fib.calls == 11\n",
      r'''
import memo
assert memo.fib(10) == 55 and memo.fib.calls == 11
assert memo.fib(10) == 55 and memo.fib.calls == 11
assert memo.fib.cache[(10,)] == 55 and memo.fib.__name__ == "fib"
assert memo.fib(90) == 2880067194370816120
assert memo.grid_paths(3, 3) == 20 and memo.grid_paths(16, 16) == 601080390 and memo.grid_paths.__name__ == "grid_paths"
assert memo.grid_paths.cache[(3, 3)] == 20
assert not hasattr(memo, "_fib_cache") and not hasattr(memo, "_paths_cache")
n = []
@memo.memoize
def sq(x):
    n.append(x)
    return x * x
assert sq(4) == 16 and sq(4) == 16 and sq(5) == 25 and n == [4, 5] and sq.calls == 2 and sq.cache == {(4,): 16, (5,): 25}
@memo.memoize
def add(a, b):
    return a + b
assert add(1, 2) == 3 and add(2, 1) == 3 and add.calls == 2
''',
      {"memo.py": r'''
import functools


def memoize(fn):
    @functools.wraps(fn)
    def wrapper(*args):
        if args in wrapper.cache:
            return wrapper.cache[args]
        wrapper.calls += 1
        r = fn(*args)
        wrapper.cache[args] = r
        return r
    wrapper.cache = {}
    wrapper.calls = 0
    return wrapper


@memoize
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)


@memoize
def grid_paths(r, c):
    return 1 if r == 0 or c == 0 else grid_paths(r - 1, c) + grid_paths(r, c - 1)
'''}),
    R("py_ref_error_hierarchy", "medium", "exceptions",
      {"loader.py": r'''
def load(d, required):
    """d: dict; required: list of keys. Returns a copy of d with 'port' converted to int."""
    for k in required:
        if k not in d:
            raise KeyError("missing key: " + k)
    out = dict(d)
    if "port" in out:
        try:
            out["port"] = int(out["port"])
        except (TypeError, ValueError):
            raise ValueError("bad port: %r" % (out["port"],))
        if not 0 < out["port"] < 65536:
            raise ValueError("port out of range: %d" % out["port"])
    return out
'''},
      "Introduce a small exception hierarchy: `ConfigError(Exception)` base, `MissingKeyError(ConfigError, KeyError)` and `InvalidValueError(ConfigError, ValueError)`. `load` must raise "
      "MissingKeyError for a missing key and InvalidValueError for a bad or out-of-range port, with the SAME messages as now (so existing `except KeyError` / `except ValueError` "
      "callers keep working). Note KeyError's str() adds quotes: store the message so that `e.args[0]` equals the old message.",
      "import loader\nassert issubclass(loader.MissingKeyError, loader.ConfigError)\n",
      r'''
import loader as l
assert issubclass(l.ConfigError, Exception) and not issubclass(l.ConfigError, (KeyError, ValueError))
assert issubclass(l.MissingKeyError, (l.ConfigError, KeyError)) and issubclass(l.InvalidValueError, (l.ConfigError, ValueError))
assert l.load({"port": "8080", "host": "h"}, ["host"]) == {"port": 8080, "host": "h"} and l.load({}, []) == {}
for d, req, exc, msg in [({}, ["host"], l.MissingKeyError, "missing key: host"), ({"port": "x"}, [], l.InvalidValueError, "bad port: 'x'"),
                         ({"port": None}, [], l.InvalidValueError, "bad port: None"), ({"port": "70000"}, [], l.InvalidValueError, "port out of range: 70000"),
                         ({"port": 0}, [], l.InvalidValueError, "port out of range: 0")]:
    try:
        l.load(d, req)
        assert False, d
    except l.ConfigError as e:
        assert type(e) is exc and e.args[0] == msg, (type(e), e.args)
try:
    l.load({}, ["a"])
except KeyError as e:
    assert e.args[0] == "missing key: a"
try:
    l.load({"port": "q"}, [])
except ValueError:
    pass
''',
      {"loader.py": r'''
class ConfigError(Exception):
    pass


class MissingKeyError(ConfigError, KeyError):
    pass


class InvalidValueError(ConfigError, ValueError):
    pass


def load(d, required):
    """d: dict; required: list of keys. Returns a copy of d with 'port' converted to int."""
    for k in required:
        if k not in d:
            raise MissingKeyError("missing key: " + k)
    out = dict(d)
    if "port" in out:
        try:
            out["port"] = int(out["port"])
        except (TypeError, ValueError):
            raise InvalidValueError("bad port: %r" % (out["port"],))
        if not 0 < out["port"] < 65536:
            raise InvalidValueError("port out of range: %d" % out["port"])
    return out
'''}),
    R("py_ref_pure_functions", "easy", "purity",
      {"lists.py": r'''
def add_all(items, extra):
    items.extend(extra)
    return items


def drop_negatives(nums):
    i = 0
    while i < len(nums):
        if nums[i] < 0:
            nums.pop(i)
        else:
            i += 1
    return nums


def sorted_desc(nums):
    nums.sort(reverse=True)
    return nums
'''},
      "These functions mutate their arguments. Make them pure: each must leave its input list untouched and return a NEW list with the same contents as before.",
      "import lists\nx = [1]\nlists.add_all(x, [2])\nassert x == [1]\n",
      r'''
import lists
a = [1, 2]
r = lists.add_all(a, [3, 4])
assert r == [1, 2, 3, 4] and a == [1, 2] and r is not a
b = [3, -1, 2, -5, 0]
r = lists.drop_negatives(b)
assert r == [3, 2, 0] and b == [3, -1, 2, -5, 0] and r is not b
c = [2, 9, 4]
r = lists.sorted_desc(c)
assert r == [9, 4, 2] and c == [2, 9, 4]
assert lists.add_all([], []) == [] and lists.drop_negatives([]) == [] and lists.sorted_desc([]) == []
t = (1, 2)
assert lists.add_all(list(t), (3,)) == [1, 2, 3]
''',
      {"lists.py": r'''
def add_all(items, extra):
    return list(items) + list(extra)


def drop_negatives(nums):
    return [n for n in nums if n >= 0]


def sorted_desc(nums):
    return sorted(nums, reverse=True)
'''}),
    R("py_ref_state_table", "hard", "state-machines",
      {"door.py": r'''
class Door:
    def __init__(self):
        self.state = "closed"

    def handle(self, event):
        if self.state == "closed":
            if event == "open":
                self.state = "opened"
            elif event == "lock":
                self.state = "locked"
            else:
                raise ValueError("invalid event %s in state closed" % event)
        elif self.state == "opened":
            if event == "close":
                self.state = "closed"
            else:
                raise ValueError("invalid event %s in state opened" % event)
        elif self.state == "locked":
            if event == "unlock":
                self.state = "closed"
            elif event == "kick":
                self.state = "broken"
            else:
                raise ValueError("invalid event %s in state locked" % event)
        else:
            raise ValueError("invalid event %s in state %s" % (event, self.state))
        return self.state
'''},
      "Make the state machine data-driven: a module-level dict `TRANSITIONS` mapping (state, event) -> new state, with `Door.handle` looking events up in it. Same states, same "
      "errors (ValueError with the exact same message format 'invalid event E in state S'). Add `allowed()` returning the sorted list of events valid in the current state "
      "(empty list in 'broken').",
      "import door\nassert door.TRANSITIONS[('closed', 'open')] == 'opened'\n",
      r'''
import door
T = door.TRANSITIONS
assert T == {("closed", "open"): "opened", ("closed", "lock"): "locked", ("opened", "close"): "closed", ("locked", "unlock"): "closed", ("locked", "kick"): "broken"}
d = door.Door()
assert d.state == "closed" and d.allowed() == ["lock", "open"]
assert d.handle("lock") == "locked" and d.allowed() == ["kick", "unlock"]
assert d.handle("unlock") == "closed" and d.handle("open") == "opened" and d.allowed() == ["close"]
try:
    d.handle("open")
    assert False
except ValueError as e:
    assert str(e) == "invalid event open in state opened" and d.state == "opened"
d.handle("close"); d.handle("lock")
assert d.handle("kick") == "broken" and d.allowed() == []
try:
    d.handle("open")
    assert False
except ValueError as e:
    assert str(e) == "invalid event open in state broken"
T[("closed", "paint")] = "painted"
e = door.Door()
assert e.handle("paint") == "painted"
''',
      {"door.py": r'''
TRANSITIONS = {
    ("closed", "open"): "opened",
    ("closed", "lock"): "locked",
    ("opened", "close"): "closed",
    ("locked", "unlock"): "closed",
    ("locked", "kick"): "broken",
}


class Door:
    def __init__(self):
        self.state = "closed"

    def handle(self, event):
        key = (self.state, event)
        if key not in TRANSITIONS:
            raise ValueError("invalid event %s in state %s" % (event, self.state))
        self.state = TRANSITIONS[key]
        return self.state

    def allowed(self):
        return sorted(e for s, e in TRANSITIONS if s == self.state)
'''}),
    R("py_ref_iterator_class", "medium", "iterators",
      {"ranges.py": r'''
def step_range(start, stop, step):
    """Return the list start, start+step, ... strictly before stop (step > 0); ValueError if step <= 0."""
    if step <= 0:
        raise ValueError("step must be positive")
    out = []
    x = start
    while x < stop:
        out.append(x)
        x += step
    return out
'''},
      "Add `class StepRange(start, stop, step)` — a re-iterable, lazy sequence: `__iter__` yields the values (a fresh iterator each time, nothing precomputed), `__len__`, "
      "`__contains__` (O(1) arithmetic, not a scan), `__getitem__` for non-negative and negative integer indexes (IndexError when out of range), and `__repr__` "
      "'StepRange(0, 10, 3)'. A step <= 0 raises ValueError in the constructor. Rewrite `step_range` as `list(StepRange(...))` (same validation and results).",
      "import ranges\nassert list(ranges.StepRange(0, 10, 4)) == [0, 4, 8]\n",
      r'''
import ranges as r
s = r.StepRange(0, 10, 3)
assert list(s) == [0, 3, 6, 9] and list(s) == [0, 3, 6, 9] and len(s) == 4
assert 6 in s and 7 not in s and 12 not in s and -3 not in s and 0 in s
assert s[0] == 0 and s[3] == 9 and s[-1] == 9 and s[-4] == 0
for bad in (4, -5):
    try:
        s[bad]
        assert False
    except IndexError:
        pass
assert repr(s) == "StepRange(0, 10, 3)"
assert len(r.StepRange(5, 5, 1)) == 0 and list(r.StepRange(5, 1, 1)) == []
big = r.StepRange(0, 10 ** 15, 7)
assert len(big) == (10 ** 15 + 6) // 7 and 7 * 123456 in big and big[10] == 70
it = iter(big)
assert next(it) == 0 and next(it) == 7
for args in ((0, 5, 0), (0, 5, -1)):
    try:
        r.StepRange(*args)
        assert False
    except ValueError:
        pass
    try:
        r.step_range(*args)
        assert False
    except ValueError:
        pass
assert r.step_range(1, 8, 3) == [1, 4, 7] and isinstance(r.step_range(1, 8, 3), list)
''',
      {"ranges.py": r'''
class StepRange:
    def __init__(self, start, stop, step):
        if step <= 0:
            raise ValueError("step must be positive")
        self.start, self.stop, self.step = start, stop, step

    def __len__(self):
        return max(0, -((self.start - self.stop) // self.step))

    def __iter__(self):
        x = self.start
        while x < self.stop:
            yield x
            x += self.step

    def __contains__(self, x):
        return self.start <= x < self.stop and (x - self.start) % self.step == 0

    def __getitem__(self, i):
        n = len(self)
        if i < 0:
            i += n
        if not 0 <= i < n:
            raise IndexError(i)
        return self.start + i * self.step

    def __repr__(self):
        return "StepRange(%r, %r, %r)" % (self.start, self.stop, self.step)


def step_range(start, stop, step):
    """Return the list start, start+step, ... strictly before stop (step > 0); ValueError if step <= 0."""
    return list(StepRange(start, stop, step))
'''}),
    R("py_ref_dedupe_formatters", "easy", "extract-function",
      {"report.py": r'''
def format_user(u):
    name = u["name"].strip()
    if len(name) > 12:
        name = name[:11] + "~"
    return "%-12s | %5d pts" % (name, u["points"])


def format_team(t):
    name = t["name"].strip()
    if len(name) > 12:
        name = name[:11] + "~"
    return "%-12s | %5d pts" % (name, t["points"])


def format_player_row(p):
    name = p["name"].strip()
    if len(name) > 12:
        name = name[:11] + "~"
    return "%-12s | %5d pts" % (name, p["points"])
'''},
      "The three formatters are copies. Add one module-level function `format_row(name, points)` containing the formatting logic and make the three functions thin wrappers around it "
      "(same output as before).",
      "import report\nassert report.format_row('a', 1) == 'a            |     1 pts'\n",
      r'''
import report as r
assert r.format_row("a", 1) == "a            |     1 pts"
assert r.format_row("  Alexander the Great ", 12345) == "Alexander t~ | 12345 pts"
assert r.format_row("x" * 12, 0) == "x" * 12 + " |     0 pts"
for f in (r.format_user, r.format_team, r.format_player_row):
    assert f({"name": " bob ", "points": 7}) == "bob          |     7 pts"
    assert f({"name": "Wolfgang Amadeus", "points": 99}) == "Wolfgang Am~ |    99 pts"
r.format_row = lambda n, p: "<%s:%s>" % (n, p)
assert r.format_user({"name": "q", "points": 1}) == "<q:1>" and r.format_team({"name": "t", "points": 2}) == "<t:2>" and r.format_player_row({"name": "p", "points": 3}) == "<p:3>"
''',
      {"report.py": r'''
def format_row(name, points):
    name = name.strip()
    if len(name) > 12:
        name = name[:11] + "~"
    return "%-12s | %5d pts" % (name, points)


def format_user(u):
    return format_row(u["name"], u["points"])


def format_team(t):
    return format_row(t["name"], t["points"])


def format_player_row(p):
    return format_row(p["name"], p["points"])
'''}),
]
