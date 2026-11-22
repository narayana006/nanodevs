"""Add-a-feature tasks: extend existing working code without breaking it."""

TASKS_FEATURE = [
    dict(
        id="feat_cart_coupons", kind="feature",
        files={"cart.py": r'''
class Cart:
    def __init__(self):
        self.items = {}  # name -> [price, qty]

    def add(self, name, price, qty=1):
        if qty <= 0:
            raise ValueError("qty must be positive")
        if name in self.items:
            self.items[name][1] += qty
        else:
            self.items[name] = [price, qty]

    def total(self):
        return round(sum(p * q for p, q in self.items.values()), 2)
'''},
        instruction=("Add to cart.py: `remove(name, qty=None)` removes qty units (all units when qty is None); KeyError if the item "
                     "is not in the cart; ValueError if qty is not positive or exceeds what is in the cart; the item disappears "
                     "from `items` when its quantity reaches 0. Add `apply_coupon(code)`: 'SAVE10' gives 10% off and 'SAVE25' gives "
                     "25% off; an unknown code raises ValueError and leaves the current coupon unchanged; only one coupon is "
                     "active at a time (a new valid one replaces the old one). `total()` applies the active coupon and rounds to "
                     "2 decimals."),
        visible=r'''
from cart import Cart
c = Cart()
c.add("pen", 2.0, 5)
c.remove("pen", 2)
assert c.total() == 6.0
''',
        hidden=r'''
from cart import Cart


def raises(exc, fn, *a):
    try:
        fn(*a)
    except exc:
        return True
    return False


c = Cart()
c.add("pen", 2.0, 5)
c.add("book", 10.0)
assert c.total() == 20.0
c.remove("pen", 2)
assert c.total() == 16.0
c.remove("pen")
assert c.total() == 10.0 and "pen" not in c.items
assert raises(KeyError, c.remove, "pen")
assert raises(ValueError, c.remove, "book", 2)
assert raises(ValueError, c.remove, "book", 0)
assert c.total() == 10.0
c.apply_coupon("SAVE10")
assert c.total() == 9.0
c.apply_coupon("SAVE25")
assert c.total() == 7.5
assert raises(ValueError, c.apply_coupon, "BAD")
assert c.total() == 7.5
c.add("pen", 2.0, 5)
assert c.total() == 15.0
''',
        reference={"cart.py": r'''
class Cart:
    COUPONS = {"SAVE10": 10, "SAVE25": 25}

    def __init__(self):
        self.items = {}  # name -> [price, qty]
        self._coupon = None

    def add(self, name, price, qty=1):
        if qty <= 0:
            raise ValueError("qty must be positive")
        if name in self.items:
            self.items[name][1] += qty
        else:
            self.items[name] = [price, qty]

    def remove(self, name, qty=None):
        if name not in self.items:
            raise KeyError(name)
        have = self.items[name][1]
        if qty is None:
            qty = have
        if qty <= 0 or qty > have:
            raise ValueError("bad qty")
        if qty == have:
            del self.items[name]
        else:
            self.items[name][1] -= qty

    def apply_coupon(self, code):
        if code not in self.COUPONS:
            raise ValueError("unknown coupon")
        self._coupon = code

    def total(self):
        t = sum(p * q for p, q in self.items.values())
        if self._coupon:
            t = t * (1 - self.COUPONS[self._coupon] / 100)
        return round(t, 2)
'''},
    ),
    dict(
        id="feat_retry_backoff", kind="feature",
        files={"retry.py": r'''
import time


def retry(times=3, delay=0.0):
    def deco(fn):
        def wrapper(*args, **kwargs):
            last = None
            for _ in range(times):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last = e
                    time.sleep(delay)
            raise last
        return wrapper
    return deco
'''},
        instruction=("Extend `retry` in retry.py with keyword arguments: `backoff=1.0` (the delay is multiplied by this after each "
                     "failed attempt), `exceptions=(Exception,)` (only these are retried; any other exception propagates "
                     "immediately), and `sleep=time.sleep` (an injectable function used for waiting). Do not sleep after the "
                     "final failed attempt. After all attempts fail, re-raise the last exception. Preserve the wrapped "
                     "function's name and docstring (functools.wraps). `times` below 1 raises ValueError when the decorator "
                     "is created."),
        visible=r'''
from retry import retry
slept = []
@retry(times=2, delay=1.0, sleep=slept.append)
def f():
    raise RuntimeError("x")
try:
    f()
except RuntimeError:
    pass
assert slept == [1.0]
''',
        hidden=r'''
from retry import retry

slept = []
calls = []


@retry(times=4, delay=1.0, backoff=2.0, sleep=slept.append)
def always_fails():
    """doc"""
    calls.append(1)
    raise RuntimeError("x")


try:
    always_fails()
except RuntimeError:
    pass
else:
    raise AssertionError("should raise")
assert len(calls) == 4
assert slept == [1.0, 2.0, 4.0]
assert always_fails.__name__ == "always_fails" and always_fails.__doc__ == "doc"

slept2, state = [], {"n": 0}


@retry(times=5, delay=0.5, sleep=slept2.append)
def flaky():
    state["n"] += 1
    if state["n"] < 3:
        raise ValueError("not yet")
    return "ok"


assert flaky() == "ok"
assert slept2 == [0.5, 0.5]

slept3, c3 = [], []


@retry(times=3, exceptions=(KeyError,), sleep=slept3.append)
def wrong_kind():
    c3.append(1)
    raise ValueError("not retried")


try:
    wrong_kind()
except ValueError:
    pass
else:
    raise AssertionError("should raise ValueError")
assert len(c3) == 1 and slept3 == []

try:
    retry(times=0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")


@retry()
def fine(x, y=1):
    return x + y


assert fine(1, y=2) == 3
''',
        reference={"retry.py": r'''
import functools
import time


def retry(times=3, delay=0.0, backoff=1.0, exceptions=(Exception,), sleep=time.sleep):
    if times < 1:
        raise ValueError("times must be >= 1")

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(times):
                try:
                    return fn(*args, **kwargs)
                except exceptions:
                    if attempt == times - 1:
                        raise
                    sleep(wait)
                    wait *= backoff
        return wrapper
    return deco
'''},
    ),
    dict(
        id="feat_todo_priority", kind="feature",
        files={"todo.py": r'''
class TodoList:
    def __init__(self):
        self._items = []
        self._next_id = 1

    def add(self, text):
        item = {"id": self._next_id, "text": text, "done": False}
        self._next_id += 1
        self._items.append(item)
        return item["id"]

    def pending(self):
        return [i["text"] for i in self._items if not i["done"]]
'''},
        instruction=("Extend TodoList in todo.py. `add(text, priority=2)` takes a priority of 1 (high), 2 (normal) or 3 (low); any "
                     "other value raises ValueError. Add `complete(id)` which marks an item done (KeyError for an unknown id; "
                     "completing an already completed item changes nothing). `pending()` now returns the texts of not-done "
                     "items ordered by priority (high first), and by insertion order within the same priority. Add `done()` "
                     "returning the texts of completed items in the order they were completed."),
        visible=r'''
from todo import TodoList
t = TodoList()
t.add("a", 3)
t.add("b", 1)
assert t.pending() == ["b", "a"]
''',
        hidden=r'''
from todo import TodoList

t = TodoList()
a = t.add("write")
b = t.add("test", 1)
c = t.add("deploy", 3)
d = t.add("review", 1)
assert t.pending() == ["test", "review", "write", "deploy"]
t.complete(d)
t.complete(b)
assert t.done() == ["review", "test"]
assert t.pending() == ["write", "deploy"]
t.complete(d)
assert t.done() == ["review", "test"]
for bad_call in (lambda: t.complete(99), lambda: t.add("x", 4), lambda: t.add("x", 0)):
    try:
        bad_call()
    except (KeyError, ValueError):
        pass
    else:
        raise AssertionError("expected an error")
assert t.pending() == ["write", "deploy"]
t.complete(c)
assert t.done() == ["review", "test", "deploy"]
''',
        reference={"todo.py": r'''
class TodoList:
    def __init__(self):
        self._items = []
        self._next_id = 1
        self._done_order = []

    def add(self, text, priority=2):
        if priority not in (1, 2, 3):
            raise ValueError("priority must be 1, 2 or 3")
        item = {"id": self._next_id, "text": text, "done": False, "priority": priority}
        self._next_id += 1
        self._items.append(item)
        return item["id"]

    def complete(self, item_id):
        for i in self._items:
            if i["id"] == item_id:
                if not i["done"]:
                    i["done"] = True
                    self._done_order.append(i["text"])
                return
        raise KeyError(item_id)

    def pending(self):
        todo = [i for i in self._items if not i["done"]]
        return [i["text"] for i in sorted(todo, key=lambda i: i["priority"])]

    def done(self):
        return list(self._done_order)
'''},
    ),
    dict(
        id="feat_logger_levels", kind="feature",
        files={"logger.py": r'''
class Logger:
    def __init__(self):
        self.lines = []

    def log(self, message):
        self.lines.append(message)
'''},
        instruction=("Add level support to Logger in logger.py. Levels in order: DEBUG < INFO < WARNING < ERROR. "
                     "`Logger(level='INFO')` ignores messages below its level. Add methods `debug`, `info`, `warning`, `error` "
                     "(each takes a message). Stored lines look like '[LEVEL] message'. `log(message)` keeps working and behaves "
                     "like `info`. Level names are case-insensitive; an unknown name raises ValueError (in the constructor, "
                     "`set_level` and `count`). Add `set_level(level)` and `count(level)` which returns the number of stored "
                     "lines at exactly that level."),
        visible=r'''
from logger import Logger
l = Logger()
l.debug("d")
l.info("i")
assert l.lines == ["[INFO] i"]
''',
        hidden=r'''
from logger import Logger

l = Logger()
l.debug("d")
l.info("i")
l.warning("w")
l.error("e")
l.log("x")
assert l.lines == ["[INFO] i", "[WARNING] w", "[ERROR] e", "[INFO] x"]
l.set_level("ERROR")
l.warning("no")
l.error("e2")
assert l.lines[-1] == "[ERROR] e2" and len(l.lines) == 5
assert l.count("INFO") == 2 and l.count("ERROR") == 2 and l.count("debug") == 0
l2 = Logger("debug")
l2.debug("z")
assert l2.lines == ["[DEBUG] z"]
l2.set_level("warning")
l2.info("hidden")
assert len(l2.lines) == 1
for bad_call in (lambda: Logger("LOUD"), lambda: l.set_level("x"), lambda: l.count("bogus")):
    try:
        bad_call()
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
        reference={"logger.py": r'''
LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]


def _norm(level):
    name = str(level).upper()
    if name not in LEVELS:
        raise ValueError("unknown level " + repr(level))
    return name


class Logger:
    def __init__(self, level="INFO"):
        self.level = _norm(level)
        self.lines = []

    def set_level(self, level):
        self.level = _norm(level)

    def _emit(self, level, message):
        if LEVELS.index(level) >= LEVELS.index(self.level):
            self.lines.append("[%s] %s" % (level, message))

    def debug(self, message):
        self._emit("DEBUG", message)

    def info(self, message):
        self._emit("INFO", message)

    def warning(self, message):
        self._emit("WARNING", message)

    def error(self, message):
        self._emit("ERROR", message)

    def log(self, message):
        self.info(message)

    def count(self, level):
        prefix = "[%s] " % _norm(level)
        return sum(1 for ln in self.lines if ln.startswith(prefix))
'''},
    ),
    dict(
        id="feat_matrix_ops", kind="feature",
        files={"matrix.py": r'''
class Matrix:
    def __init__(self, rows):
        if not rows or any(len(r) != len(rows[0]) for r in rows):
            raise ValueError("rows must be a non-empty rectangle")
        self.rows = [list(r) for r in rows]

    @property
    def shape(self):
        return (len(self.rows), len(self.rows[0]))

    def __eq__(self, other):
        return isinstance(other, Matrix) and self.rows == other.rows
'''},
        instruction=("Extend Matrix in matrix.py: `transpose()` returns a new Matrix; `__add__` adds two matrices element by element "
                     "(different shapes raise ValueError); `__mul__` does matrix multiplication for Matrix * Matrix (the inner "
                     "dimensions must match, otherwise ValueError) and scalar multiplication for Matrix * number; `__rmul__` "
                     "makes number * Matrix work; `__repr__` returns for example 'Matrix([[1, 2], [3, 4]])'. Operations must "
                     "never mutate their operands."),
        visible=r'''
from matrix import Matrix
assert Matrix([[1, 2], [3, 4]]).transpose() == Matrix([[1, 3], [2, 4]])
''',
        hidden=r'''
from matrix import Matrix

a = Matrix([[1, 2], [3, 4]])
b = Matrix([[5, 6], [7, 8]])
assert a.transpose() == Matrix([[1, 3], [2, 4]])
assert Matrix([[1, 2, 3]]).transpose() == Matrix([[1], [2], [3]])
assert a + b == Matrix([[6, 8], [10, 12]])
assert a * b == Matrix([[19, 22], [43, 50]])
assert a * 2 == Matrix([[2, 4], [6, 8]])
assert 3 * a == Matrix([[3, 6], [9, 12]])
assert Matrix([[1, 2, 3]]) * Matrix([[1], [2], [3]]) == Matrix([[14]])
assert Matrix([[1], [2]]) * Matrix([[3, 4]]) == Matrix([[3, 4], [6, 8]])
assert repr(a) == "Matrix([[1, 2], [3, 4]])"
assert a.rows == [[1, 2], [3, 4]] and b.rows == [[5, 6], [7, 8]]
for bad_call in (lambda: a + Matrix([[1, 2, 3]]), lambda: a * Matrix([[1, 2, 3]])):
    try:
        bad_call()
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
        reference={"matrix.py": r'''
class Matrix:
    def __init__(self, rows):
        if not rows or any(len(r) != len(rows[0]) for r in rows):
            raise ValueError("rows must be a non-empty rectangle")
        self.rows = [list(r) for r in rows]

    @property
    def shape(self):
        return (len(self.rows), len(self.rows[0]))

    def __eq__(self, other):
        return isinstance(other, Matrix) and self.rows == other.rows

    def transpose(self):
        return Matrix([list(col) for col in zip(*self.rows)])

    def __add__(self, other):
        if not isinstance(other, Matrix) or self.shape != other.shape:
            raise ValueError("shape mismatch")
        return Matrix([[x + y for x, y in zip(r1, r2)] for r1, r2 in zip(self.rows, other.rows)])

    def __mul__(self, other):
        if isinstance(other, Matrix):
            if self.shape[1] != other.shape[0]:
                raise ValueError("inner dimensions differ")
            cols = list(zip(*other.rows))
            return Matrix([[sum(x * y for x, y in zip(r, c)) for c in cols] for r in self.rows])
        return Matrix([[x * other for x in r] for r in self.rows])

    __rmul__ = __mul__

    def __repr__(self):
        return "Matrix(%r)" % (self.rows,)
'''},
    ),
    dict(
        id="feat_config_env", kind="feature",
        files={"config.py": r'''
import json


def parse_config(text):
    return json.loads(text)
'''},
        instruction=("Extend `parse_config` in config.py to `parse_config(text, env=None, prefix='APP_')`. `text` is JSON for a dict. "
                     "`env` is a dict of environment variables (default: empty). For every variable whose name starts with the "
                     "prefix, override the config key named by the rest of the variable name, lowercased; a double underscore "
                     "'__' means nesting (APP_DB__PORT sets config['db']['port'], creating the nested dict if needed). Convert "
                     "the string to the type of the existing value: bool ('true'/'false' in any case, anything else raises "
                     "ValueError), int, float, otherwise keep a string. A key that does not exist yet is stored as a string. "
                     "Variables without the prefix are ignored. `env` must not be modified."),
        visible=r'''
from config import parse_config
assert parse_config('{"port": 80}', {"APP_PORT": "81"}) == {"port": 81}
''',
        hidden=r'''
import json
from config import parse_config

text = '{"debug": false, "port": 8080, "ratio": 0.5, "name": "x", "db": {"host": "h", "port": 5432}}'
env = {"APP_DEBUG": "TRUE", "APP_PORT": "9000", "APP_RATIO": "0.25", "APP_NAME": "y",
       "APP_DB__PORT": "5433", "APP_NEW": "v", "OTHER": "ignored", "APP_DB__USER": "bob"}
env_copy = dict(env)
cfg = parse_config(text, env)
assert cfg["debug"] is True
assert cfg["port"] == 9000 and isinstance(cfg["port"], int)
assert cfg["ratio"] == 0.25
assert cfg["name"] == "y"
assert cfg["db"] == {"host": "h", "port": 5433, "user": "bob"}
assert cfg["new"] == "v"
assert "other" not in cfg
assert env == env_copy
assert parse_config(text) == json.loads(text)
assert parse_config(text, {}) == json.loads(text)
assert parse_config(text, {"APP_DEBUG": "false"})["debug"] is False
try:
    parse_config(text, {"APP_DEBUG": "maybe"})
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert parse_config('{"a": 1}', {"X_A": "5"}, prefix="X_") == {"a": 5}
assert parse_config('{"deep": {}}', {"APP_DEEP__A__B": "1"}) == {"deep": {"a": {"b": "1"}}}
''',
        reference={"config.py": r'''
import json


def _coerce(value, old):
    if isinstance(old, bool):
        low = value.lower()
        if low in ("true", "false"):
            return low == "true"
        raise ValueError("not a bool: " + value)
    if isinstance(old, int):
        return int(value)
    if isinstance(old, float):
        return float(value)
    return value


def parse_config(text, env=None, prefix="APP_"):
    cfg = json.loads(text)
    for name, val in (env or {}).items():
        if not name.startswith(prefix):
            continue
        parts = name[len(prefix):].lower().split("__")
        cur = cfg
        for p in parts[:-1]:
            nxt = cur.get(p)
            if not isinstance(nxt, dict):
                nxt = {}
                cur[p] = nxt
            cur = nxt
        key = parts[-1]
        cur[key] = _coerce(val, cur[key]) if key in cur else val
    return cfg
'''},
    ),
]
