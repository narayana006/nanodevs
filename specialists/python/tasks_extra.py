"""Extra multi-file fix tasks and harder refactors."""
from common import fix, feat

TASKS_EXTRA = [
    fix("py_fix_cache_key_collision", "hard", "caching",
        {"keys.py": r'''
def make_key(args, kwargs):
    """Hashable cache key for a call: positional args plus keyword args (order of keywords must not matter)."""
    return ",".join(str(a) for a in args) + "|" + ",".join("%s=%s" % (k, v) for k, v in kwargs.items())
''', "cache.py": r'''
from keys import make_key


def cached(fn):
    store = {}

    def wrapper(*args, **kwargs):
        k = make_key(args, kwargs)
        if k not in store:
            store[k] = fn(*args, **kwargs)
        return store[k]
    wrapper.store = store
    return wrapper
'''},
        [("keys.py", 'return ",".join(str(a) for a in args) + "|" + ",".join("%s=%s" % (k, v) for k, v in kwargs.items())',
          "return (tuple(args), tuple(sorted(kwargs.items())))")],
        "Calls with different arguments sometimes return each other's cached results.",
        "from cache import cached\n@cached\ndef f(x):\n    return type(x).__name__\nassert f(1) == 'int' and f('1') == 'str'\n",
        r'''
from cache import cached
calls = []
@cached
def f(*a, **k):
    calls.append((a, k))
    return (a, k)
assert f(1) == ((1,), {}) and f("1") == (("1",), {})
assert f(1, 2) != f((1, 2))
assert f(a=1, b=2) == ((), {"a": 1, "b": 2})
n = len(calls)
assert f(b=2, a=1) == ((), {"a": 1, "b": 2}) and len(calls) == n
assert f("a,b") == (("a,b",), {}) and f("a", "b") == (("a", "b"), {})
assert f(x="1|y=2") == ((), {"x": "1|y=2"})
assert f(1.0) == ((1.0,), {})
before = len(calls)
f(1); f("1"); f(1, 2); f("a", "b")
assert len(calls) == before
'''),
    fix("py_fix_twelve_hour_clock", "medium", "parsing",
        {"times.py": r'''
def parse_time(s):
    """Parse '9:05 AM' / '12:30 PM' (12-hour clock) into minutes since midnight."""
    clock, ampm = s.strip().split()
    h, m = clock.split(":")
    h, m = int(h), int(m)
    if not 1 <= h <= 12 or not 0 <= m <= 59:
        raise ValueError("bad time: " + s)
    if ampm.upper() == "PM":
        h += 12
    elif ampm.upper() != "AM":
        raise ValueError("bad time: " + s)
    return h * 60 + m
''', "schedule.py": r'''
from times import parse_time


def conflicts(slots):
    """slots: list of (name, start, end) with 12-hour time strings (end is exclusive). Returns sorted list of (name_a, name_b) pairs that overlap."""
    parsed = [(n, parse_time(s), parse_time(e)) for n, s, e in slots]
    out = []
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            a, b = parsed[i], parsed[j]
            if a[1] < b[2] and b[1] < a[2]:
                out.append(tuple(sorted((a[0], b[0]))))
    return sorted(out)
'''},
        [("times.py", '    if ampm.upper() == "PM":\n        h += 12\n    elif ampm.upper() != "AM":\n        raise ValueError("bad time: " + s)\n    return h * 60 + m',
          '    if ampm.upper() not in ("AM", "PM"):\n        raise ValueError("bad time: " + s)\n    h %= 12\n    if ampm.upper() == "PM":\n        h += 12\n    return h * 60 + m')],
        "Noon and midnight are parsed wrongly, so lunchtime meetings are reported as non-conflicting.",
        "from times import parse_time\nassert parse_time('12:30 PM') == 750\n",
        r'''
from times import parse_time as p
from schedule import conflicts
assert p("12:30 PM") == 750 and p("12:00 AM") == 0 and p("12:15 AM") == 15 and p("1:00 PM") == 780 and p("11:59 PM") == 1439 and p("9:05 am") == 545
for bad in ("13:00 PM", "0:30 AM", "5:61 PM", "5:00 XM"):
    try:
        p(bad)
        assert False, bad
    except ValueError:
        pass
slots = [("lunch", "11:30 AM", "12:30 PM"), ("call", "12:00 PM", "1:00 PM"), ("late", "1:00 PM", "2:00 PM"), ("night", "11:00 PM", "12:30 AM")]
assert conflicts(slots) == [("call", "lunch")]
assert conflicts([("a", "12:00 AM", "1:00 AM"), ("b", "12:30 AM", "2:00 AM")]) == [("a", "b")]
assert conflicts([("a", "12:00 PM", "1:00 PM"), ("b", "1:00 PM", "2:00 PM")]) == []
'''),
    fix("py_fix_amortize_residual", "hard", "math",
        {"loan.py": r'''
def amortize(principal, annual_rate, months):
    """Monthly payment schedule: list of (payment, interest, principal_paid, balance_after), all rounded to cents.
    The loan must be fully repaid: the last row's balance is exactly 0 and principal_paid sums to the principal."""
    r = annual_rate / 12
    pay = round(principal * r / (1 - (1 + r) ** -months), 2) if r else round(principal / months, 2)
    bal = round(principal, 2)
    rows = []
    for m in range(1, months + 1):
        interest = round(bal * r, 2)
        paid = round(pay - interest, 2)
        bal = round(bal - paid, 2)
        rows.append((pay, interest, paid, bal))
    return rows
'''},
        [("loan.py", "        paid = round(pay - interest, 2)\n        bal = round(bal - paid, 2)\n        rows.append((pay, interest, paid, bal))",
          "        p = pay\n        paid = round(p - interest, 2)\n        if m == months:\n            paid = bal\n            p = round(paid + interest, 2)\n        bal = round(bal - paid, 2)\n        rows.append((p, interest, paid, bal))")],
        "After the last payment a few cents of the loan remain unpaid.",
        "from loan import amortize\nassert amortize(1000, 0.12, 12)[-1][3] == 0\n",
        r'''
from loan import amortize
rows = amortize(1000, 0.12, 12)
assert rows[0] == (88.85, 10.0, 78.85, 921.15)
assert len(rows) == 12 and rows[-1][3] == 0
assert round(sum(r[2] for r in rows), 2) == 1000.0
assert all(abs(r[0] - 88.85) < 0.2 for r in rows)
assert all(rows[i][3] < rows[i - 1][3] for i in range(1, 12))
for principal, rate, n in [(250000, 0.065, 360), (9999.99, 0.0349, 47), (1200, 0.0, 12), (500, 0.2, 1)]:
    rs = amortize(principal, rate, n)
    assert len(rs) == n and rs[-1][3] == 0, (principal, rate, n, rs[-1])
    assert abs(sum(r[2] for r in rs) - principal) < 0.005, (principal, rate, n)
    assert all(abs(r[0] - rs[0][0]) < 0.5 + n * 0.01 for r in rs)
r1 = amortize(500, 0.2, 1)
assert r1 == [(round(500 + 500 * 0.2 / 12, 2), round(500 * 0.2 / 12, 2), 500.0, 0.0)]
assert amortize(1200, 0.0, 12)[0] == (100.0, 0.0, 100.0, 1100.0)
'''),
    fix("py_fix_keyword_prefix", "medium", "parsing",
        {"lexer.py": r'''
KEYWORDS = ("if", "else", "while", "for", "in", "return")


def lex(src):
    """Split on whitespace into (kind, text): KW for keywords, ID for identifiers, NUM for digit strings."""
    out = []
    for w in src.split():
        if any(w.startswith(k) for k in KEYWORDS):
            out.append(("KW", w))
        elif w.isdigit():
            out.append(("NUM", w))
        else:
            out.append(("ID", w))
    return out
''', "highlight.py": r'''
from lexer import lex


def highlight(src):
    parts = []
    for kind, text in lex(src):
        parts.append("<b>%s</b>" % text if kind == "KW" else text)
    return " ".join(parts)
'''},
        [("lexer.py", "if any(w.startswith(k) for k in KEYWORDS):", "if w in KEYWORDS:")],
        "Identifiers that merely start with a keyword (like `index` or `format`) are treated as keywords.",
        "from lexer import lex\nassert lex('index') == [('ID', 'index')]\n",
        r'''
from lexer import lex
from highlight import highlight
assert lex("index") == [("ID", "index")] and lex("format") == [("ID", "format")] and lex("returned 42") == [("ID", "returned"), ("NUM", "42")]
assert lex("if x in items return 1") == [("KW", "if"), ("ID", "x"), ("KW", "in"), ("ID", "items"), ("KW", "return"), ("NUM", "1")]
assert lex("") == [] and lex("else") == [("KW", "else")] and lex("elsewhere") == [("ID", "elsewhere")]
assert highlight("for i in forest") == "<b>for</b> i <b>in</b> forest"
assert highlight("whileloop while") == "whileloop <b>while</b>"
'''),
    feat("py_ref_expression_visitor", "hard", "polymorphism",
         {"expr.py": r'''
class Num:
    def __init__(self, value):
        self.value = value


class Var:
    def __init__(self, name):
        self.name = name


class BinOp:
    def __init__(self, op, left, right):
        self.op, self.left, self.right = op, left, right


def evaluate(node, env):
    if isinstance(node, Num):
        return node.value
    if isinstance(node, Var):
        return env[node.name]
    if isinstance(node, BinOp):
        a, b = evaluate(node.left, env), evaluate(node.right, env)
        if node.op == "+":
            return a + b
        if node.op == "-":
            return a - b
        if node.op == "*":
            return a * b
        if node.op == "/":
            return a / b
    raise TypeError("unknown node")


def to_str(node):
    if isinstance(node, Num):
        return str(node.value)
    if isinstance(node, Var):
        return node.name
    if isinstance(node, BinOp):
        return "(%s %s %s)" % (to_str(node.left), node.op, to_str(node.right))
    raise TypeError("unknown node")


def depth(node):
    if isinstance(node, (Num, Var)):
        return 1
    if isinstance(node, BinOp):
        return 1 + max(depth(node.left), depth(node.right))
    raise TypeError("unknown node")
'''},
         "Replace the isinstance chains with polymorphism: give each node class `evaluate(env)`, `to_str()` and `depth()` methods, and keep the module-level functions "
         "`evaluate(node, env)`, `to_str(node)` and `depth(node)` as thin wrappers that just call the node's method (so a NEW node class that defines the three methods works "
         "without touching the functions). Objects without the methods still raise TypeError('unknown node'). Behaviour for the existing node types is unchanged.",
         "import expr\nassert expr.Num(3).to_str() == '3'\n",
         r'''
import expr as e
tree = e.BinOp("*", e.BinOp("+", e.Num(1), e.Var("x")), e.Num(4))
assert tree.evaluate({"x": 2}) == 12 and e.evaluate(tree, {"x": 2}) == 12
assert tree.to_str() == "((1 + x) * 4)" and e.to_str(tree) == "((1 + x) * 4)"
assert tree.depth() == 3 and e.depth(tree) == 3 and e.depth(e.Num(1)) == 1
assert e.evaluate(e.BinOp("/", e.Num(1), e.Num(4)), {}) == 0.25 and e.evaluate(e.BinOp("-", e.Num(1), e.Num(4)), {}) == -3
try:
    e.evaluate(e.Var("y"), {})
    assert False
except KeyError:
    pass
try:
    e.BinOp("^", e.Num(1), e.Num(2)).evaluate({})
    assert False
except TypeError:
    pass
class Neg:
    def __init__(self, inner):
        self.inner = inner
    def evaluate(self, env):
        return -self.inner.evaluate(env)
    def to_str(self):
        return "-" + self.inner.to_str()
    def depth(self):
        return 1 + self.inner.depth()
n = e.BinOp("+", Neg(e.Num(2)), e.Num(10))
assert e.evaluate(n, {}) == 8 and e.to_str(n) == "(-2 + 10)" and e.depth(n) == 3
for f in (lambda: e.evaluate(object(), {}), lambda: e.to_str("x"), lambda: e.depth(3)):
    try:
        f()
        assert False
    except TypeError as ex:
        assert str(ex) == "unknown node"
import ast
src = open(e.__file__).read()
assert "isinstance" not in src
''',
         replace={"expr.py": r'''
class Num:
    def __init__(self, value):
        self.value = value

    def evaluate(self, env):
        return self.value

    def to_str(self):
        return str(self.value)

    def depth(self):
        return 1


class Var:
    def __init__(self, name):
        self.name = name

    def evaluate(self, env):
        return env[self.name]

    def to_str(self):
        return self.name

    def depth(self):
        return 1


class BinOp:
    def __init__(self, op, left, right):
        self.op, self.left, self.right = op, left, right

    def evaluate(self, env):
        a, b = self.left.evaluate(env), self.right.evaluate(env)
        if self.op == "+":
            return a + b
        if self.op == "-":
            return a - b
        if self.op == "*":
            return a * b
        if self.op == "/":
            return a / b
        raise TypeError("unknown node")

    def to_str(self):
        return "(%s %s %s)" % (self.left.to_str(), self.op, self.right.to_str())

    def depth(self):
        return 1 + max(self.left.depth(), self.right.depth())


def _call(node, name, *args):
    method = getattr(node, name, None)
    if method is None:
        raise TypeError("unknown node")
    return method(*args)


def evaluate(node, env):
    return _call(node, "evaluate", env)


def to_str(node):
    return _call(node, "to_str")


def depth(node):
    return _call(node, "depth")
'''}),
    feat("py_ref_layered_users", "hard", "multi-file",
         {"app.py": r'''
def register(db, name, email):
    """db: dict uid -> user dict. Adds a user and returns it."""
    if not name.strip() or "@" not in email:
        raise ValueError("invalid user")
    for u in db.values():
        if u["email"] == email.strip().lower():
            raise ValueError("duplicate email")
    uid = max(db, default=0) + 1
    db[uid] = {"id": uid, "name": name.strip(), "email": email.strip().lower()}
    return db[uid]


def render(db):
    return "\n".join("%d. %s <%s>" % (u["id"], u["name"], u["email"]) for u in sorted(db.values(), key=lambda u: u["id"]))
'''},
         "Split the module into layers. `repo.py`: `class UserRepo(db=None)` wrapping a dict (creates a new dict when None) with `find_by_email(email)` (case-insensitive, returns the "
         "user dict or None), `add(name, email)` (stores an already-validated, normalised user and returns it; ids are max+1) and `all()` (users sorted by id). `service.py`: "
         "`register(repo, name, email)` doing validation (same ValueErrors) and calling the repo. `view.py`: `render(users)` taking a list of user dicts. app.py keeps `register(db, name, email)` "
         "and `render(db)` with the same behaviour by composing the new layers (no duplicated logic left in app.py).",
         "from repo import UserRepo\nr = UserRepo()\nassert r.add('a', 'a@x.io')['id'] == 1\n",
         r'''
import app, repo, service, view
r = repo.UserRepo()
assert r.all() == [] and r.find_by_email("a@x.io") is None
u = service.register(r, " Ann ", " Ann@X.io ")
assert u == {"id": 1, "name": "Ann", "email": "ann@x.io"} and r.find_by_email("ANN@x.io") == u
u2 = service.register(r, "Bo", "bo@x.io")
assert u2["id"] == 2 and r.all() == [u, u2]
for args in [("", "a@b"), ("  ", "a@b"), ("x", "nope")]:
    try:
        service.register(r, *args)
        assert False
    except ValueError as e:
        assert str(e) == "invalid user"
try:
    service.register(r, "Other", "BO@x.io")
    assert False
except ValueError as e:
    assert str(e) == "duplicate email"
assert view.render(r.all()) == "1. Ann <ann@x.io>\n2. Bo <bo@x.io>" and view.render([]) == ""
db = {}
assert app.register(db, "Cy", "cy@x.io") == {"id": 1, "name": "Cy", "email": "cy@x.io"} and 1 in db
app.register(db, "Di", "di@x.io")
assert app.render(db) == "1. Cy <cy@x.io>\n2. Di <di@x.io>"
del db[1]
assert app.register(db, "Ed", "ed@x.io")["id"] == 3
try:
    app.register(db, "Dup", "DI@x.io")
    assert False
except ValueError:
    pass
shared = {}
repo.UserRepo(shared).add("a", "a@a")
assert shared[1]["name"] == "a"
src = open(app.__file__).read()
assert "sorted(" not in src and "@" not in src and "max(" not in src
''',
         replace={"repo.py": r'''
class UserRepo:
    def __init__(self, db=None):
        self.db = {} if db is None else db

    def find_by_email(self, email):
        email = email.strip().lower()
        for u in self.db.values():
            if u["email"] == email:
                return u
        return None

    def add(self, name, email):
        uid = max(self.db, default=0) + 1
        self.db[uid] = {"id": uid, "name": name.strip(), "email": email.strip().lower()}
        return self.db[uid]

    def all(self):
        return sorted(self.db.values(), key=lambda u: u["id"])
''', "service.py": r'''
def register(repo, name, email):
    if not name.strip() or "@" not in email:
        raise ValueError("invalid user")
    if repo.find_by_email(email) is not None:
        raise ValueError("duplicate email")
    return repo.add(name, email)
''', "view.py": r'''
def render(users):
    return "\n".join("%d. %s <%s>" % (u["id"], u["name"], u["email"]) for u in users)
''', "app.py": r'''
from repo import UserRepo
from service import register as _register
from view import render as _render


def register(db, name, email):
    """db: dict uid -> user dict. Adds a user and returns it."""
    return _register(UserRepo(db), name, email)


def render(db):
    return _render(UserRepo(db).all())
'''}),
]

for _t in TASKS_EXTRA:
    if _t["id"].startswith("py_ref_"):
        _t["kind"] = "refactor"
