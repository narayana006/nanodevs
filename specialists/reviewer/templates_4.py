"""Templates 4: state updates, silently dropped errors, multi-defect hard tasks."""
TEMPLATES = {}


def T(name, difficulty, title, base, good, tests, defects, params):
    TEMPLATES[name] = (dict(difficulty=difficulty, title=title, base=base, good=good, tests=tests, defects=defects), params)


# ---------------------------------------------------------------- rate limiter records the call
T("rate_limiter", "medium", "Add a sliding-window limiter @C@",
  base={"@M@.py": '''
def window_start(now, window):
    return now - window
'''},
  good={"@M@.py": '''
def window_start(now, window):
    return now - window


class @C@:
    def __init__(self, max_calls, window):
        self.max_calls = max_calls
        self.window = window
        self.hits = {}

    def allow(self, key, now):
        hits = [t for t in self.hits.get(key, []) if t > window_start(now, self.window)]
        if len(hits) >= self.max_calls:
            self.hits[key] = hits
            return False
        hits.append(now)
        self.hits[key] = hits
        return True
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_window_start():
    assert m.window_start(10, 3) == 7

def test_blocks_after_max():
    needs(m, "@C@")
    r = m.@C@(2, 10)
    assert r.allow("a", 0) and r.allow("a", 1)
    assert not r.allow("a", 2)

def test_window_expires():
    needs(m, "@C@")
    r = m.@C@(1, 10)
    assert r.allow("a", 0)
    assert not r.allow("a", 5)
    assert r.allow("a", 11)

def test_keys_independent():
    needs(m, "@C@")
    r = m.@C@(1, 10)
    assert r.allow("a", 0) and r.allow("b", 0)
''',
  defects=[dict(file="@M@.py", old="        hits.append(now)\n        self.hits[key] = hits\n        return True", new="        self.hits[key] = hits\n        return True", category="state_update",
                line_offset=0, test="test_blocks_after_max",
                why="An allowed call is never recorded (hits.append(now) is missing), so the limiter never reaches max_calls and never blocks.")],
  params=[dict(M="limiter", C="RateLimiter"), dict(M="throttle", C="SlidingWindow")])

# ---------------------------------------------------------------- memoize stores result
T("memoize", "easy", "Add @F@ decorator-style cache wrapper",
  base={"@M@.py": '''
def square(x):
    return x * x
'''},
  good={"@M@.py": '''
def square(x):
    return x * x


def @F@(fn):
    cache = {}

    def wrapper(arg):
        if arg not in cache:
            cache[arg] = fn(arg)
        return cache[arg]
    wrapper.cache = cache
    return wrapper
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_square():
    assert m.square(4) == 16

def test_calls_once():
    needs(m, "@F@")
    calls = []
    def f(x):
        calls.append(x)
        return x + 1
    g = m.@F@(f)
    assert g(1) == 2 and g(1) == 2
    assert calls == [1]

def test_falsy_results_cached():
    needs(m, "@F@")
    calls = []
    def f(x):
        calls.append(x)
        return 0
    g = m.@F@(f)
    g(5); g(5)
    assert calls == [5]
''',
  defects=[dict(file="@M@.py", old="        if arg not in cache:\n            cache[arg] = fn(arg)\n        return cache[arg]", new="        if arg not in cache:\n            fn(arg)\n        return cache[arg]",
                category="state_update", line_offset=2, test="test_calls_once",
                why="The result of fn(arg) is never stored in the cache: the following lookup raises KeyError (and nothing is ever memoized).")],
  params=[dict(M="cachetools_lite", F="memoize"), dict(M="fastcalls", F="cached")])

# ---------------------------------------------------------------- inventory: check before mutate
T("reserve", "medium", "Add @F@ to reserve stock for an order",
  base={"@M@.py": '''
class Inventory:
    def __init__(self, stock):
        self.stock = dict(stock)

    def available(self, item):
        return self.stock.get(item, 0)
'''},
  good={"@M@.py": '''
class Inventory:
    def __init__(self, stock):
        self.stock = dict(stock)

    def available(self, item):
        return self.stock.get(item, 0)

    def @F@(self, item, qty):
        if qty > self.available(item):
            raise ValueError("insufficient stock for %s" % item)
        self.stock[item] = self.available(item) - qty
        return self.stock[item]
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_available():
    assert m.Inventory({"a": 3}).available("a") == 3
    assert m.Inventory({}).available("zzz") == 0

def test_reserve():
    needs(m.Inventory, "@F@")
    inv = m.Inventory({"a": 5})
    assert inv.@F@("a", 2) == 3
    assert inv.available("a") == 3

def test_exact_stock_allowed():
    needs(m.Inventory, "@F@")
    inv = m.Inventory({"a": 2})
    assert inv.@F@("a", 2) == 0

def test_failed_reserve_leaves_stock():
    needs(m.Inventory, "@F@")
    inv = m.Inventory({"a": 2})
    try:
        inv.@F@("a", 5)
    except ValueError:
        assert inv.available("a") == 2
        return
    raise AssertionError
''',
  defects=[dict(file="@M@.py", old='''        if qty > self.available(item):
            raise ValueError("insufficient stock for %s" % item)
        self.stock[item] = self.available(item) - qty
        return self.stock[item]''', new='''        self.stock[item] = self.available(item) - qty
        if self.stock[item] < 0:
            raise ValueError("insufficient stock for %s" % item)
        return self.stock[item]''', category="state_update", line_offset=0, test="test_failed_reserve_leaves_stock",
                why="Stock is decremented before the availability check, so a rejected reservation still leaves the stock negative/mutated.")],
  params=[dict(M="warehouse", F="reserve"), dict(M="seats", F="hold")])

# ---------------------------------------------------------------- LRU get refreshes recency
T("lru", "medium", "Add a tiny LRU cache @C@",
  base={"@M@.py": '''
from collections import OrderedDict
'''},
  good={"@M@.py": '''
from collections import OrderedDict


class @C@:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = OrderedDict()

    def get(self, key, default=None):
        if key not in self.data:
            return default
        self.data.move_to_end(key)
        return self.data[key]

    def put(self, key, value):
        self.data[key] = value
        self.data.move_to_end(key)
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_module_imports():
    assert m.OrderedDict

def test_put_get():
    needs(m, "@C@")
    c = m.@C@(2)
    c.put("a", 1)
    assert c.get("a") == 1 and c.get("zz", 9) == 9

def test_evicts_oldest():
    needs(m, "@C@")
    c = m.@C@(2)
    c.put("a", 1); c.put("b", 2); c.put("c", 3)
    assert c.get("a") is None and c.get("b") == 2

def test_get_refreshes():
    needs(m, "@C@")
    c = m.@C@(2)
    c.put("a", 1); c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert c.get("a") == 1 and c.get("b") is None
''',
  defects=[dict(file="@M@.py", old="        self.data.move_to_end(key)\n        return self.data[key]", new="        return self.data[key]", category="state_update", line_offset=0,
                test="test_get_refreshes", why="get() no longer marks the key as recently used (move_to_end missing), so frequently read entries are evicted as if untouched.")],
  params=[dict(M="lrucache", C="LRUCache"), dict(M="recent_items", C="RecentMap")])

# ---------------------------------------------------------------- transfer debits source
T("transfer", "medium", "Add @F@ between two accounts",
  base={"@M@.py": '''
class Account:
    def __init__(self, balance=0):
        self.balance = balance
'''},
  good={"@M@.py": '''
class Account:
    def __init__(self, balance=0):
        self.balance = balance


def @F@(src, dst, amount):
    if amount <= 0:
        raise ValueError("amount must be positive")
    if src.balance < amount:
        raise ValueError("insufficient funds")
    src.balance -= amount
    dst.balance += amount
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_account():
    assert m.Account(5).balance == 5

def test_transfer():
    needs(m, "@F@")
    a, b = m.Account(10), m.Account(1)
    m.@F@(a, b, 4)
    assert (a.balance, b.balance) == (6, 5)

def test_total_conserved():
    needs(m, "@F@")
    a, b = m.Account(10), m.Account(0)
    m.@F@(a, b, 10)
    assert a.balance + b.balance == 10 and a.balance == 0

def test_insufficient():
    needs(m, "@F@")
    a, b = m.Account(1), m.Account(0)
    try:
        m.@F@(a, b, 5)
    except ValueError:
        assert (a.balance, b.balance) == (1, 0)
        return
    raise AssertionError
''',
  defects=[dict(file="@M@.py", old="    src.balance -= amount\n    dst.balance += amount", new="    dst.balance += amount", category="state_update", line_offset=0,
                test="test_transfer", why="The source account is never debited (src.balance -= amount missing), so money is created from nothing.")],
  params=[dict(M="ledger", F="transfer"), dict(M="wallets", F="move_funds")])

# ---------------------------------------------------------------- process_all drops errors
T("process_all", "medium", "Add @F@ to run a handler over a batch and report failures",
  base={"@M@.py": '''
def run_one(handler, item):
    return handler(item)
'''},
  good={"@M@.py": '''
def run_one(handler, item):
    return handler(item)


def @F@(handler, items):
    results, errors = [], []
    for item in items:
        try:
            results.append(run_one(handler, item))
        except Exception as e:
            errors.append((item, e))
    return results, errors
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_run_one():
    assert m.run_one(lambda x: x + 1, 1) == 2

def test_results():
    needs(m, "@F@")
    res, errs = m.@F@(lambda x: x * 2, [1, 2, 3])
    assert res == [2, 4, 6] and errs == []

def test_errors_reported():
    needs(m, "@F@")
    def h(x):
        if x == 2:
            raise ValueError("two")
        return x
    res, errs = m.@F@(h, [1, 2, 3])
    assert res == [1, 3]
    assert len(errs) == 1 and errs[0][0] == 2 and isinstance(errs[0][1], ValueError)
''',
  defects=[dict(file="@M@.py", old="        except Exception as e:\n            errors.append((item, e))", new="        except Exception:\n            continue", category="dropped_error", line_offset=0,
                test="test_errors_reported", why="Failures are swallowed with `continue`; the errors list is always empty, so callers cannot tell that items failed.")],
  params=[dict(M="batch", F="process_all"), dict(M="pipeline", F="run_batch")])

# ---------------------------------------------------------------- write result ignored
T("save_record", "easy", "Add @F@ that persists a record via the store",
  base={"@M@.py": '''
class SaveError(Exception):
    pass
'''},
  good={"@M@.py": '''
class SaveError(Exception):
    pass


def @F@(store, key, value):
    ok = store.write(key, value)
    if not ok:
        raise SaveError("could not save %s" % key)
    return key
'''},
  tests='''
import @M@ as m
from _rt import needs

class Store:
    def __init__(self, ok):
        self.ok = ok
        self.data = {}
    def write(self, k, v):
        if self.ok:
            self.data[k] = v
        return self.ok

def test_exc_exists():
    assert issubclass(m.SaveError, Exception)

def test_saves():
    needs(m, "@F@")
    s = Store(True)
    assert m.@F@(s, "k", 1) == "k" and s.data == {"k": 1}

def test_failure_raises():
    needs(m, "@F@")
    try:
        m.@F@(Store(False), "k", 1)
    except m.SaveError:
        return
    raise AssertionError("failed write was reported as success")
''',
  defects=[dict(file="@M@.py", old='    ok = store.write(key, value)\n    if not ok:\n        raise SaveError("could not save %s" % key)\n    return key', new="    store.write(key, value)\n    return key",
                category="dropped_error", line_offset=0, test="test_failure_raises",
                why="The boolean result of store.write() is ignored, so failed writes are reported as successful saves.")],
  params=[dict(M="persist", F="save_record"), dict(M="docstore", F="put_document")])

# ---------------------------------------------------------------- validation: later field overwrites earlier failure
T("validate_form", "medium", "Add @F@ returning overall validity",
  base={"@M@.py": '''
def is_blank(v):
    return v is None or str(v).strip() == ""
'''},
  good={"@M@.py": '''
def is_blank(v):
    return v is None or str(v).strip() == ""


def @F@(form, required):
    ok = True
    missing = []
    for name in required:
        if is_blank(form.get(name)):
            ok = False
            missing.append(name)
    return ok, missing
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_blank():
    assert m.is_blank(" ") and m.is_blank(None) and not m.is_blank(0)

def test_all_ok():
    needs(m, "@F@")
    assert m.@F@({"a": "x", "b": "y"}, ["a", "b"]) == (True, [])

def test_first_missing_detected():
    needs(m, "@F@")
    ok, missing = m.@F@({"a": "", "b": "y"}, ["a", "b"])
    assert ok is False and missing == ["a"]
''',
  defects=[dict(file="@M@.py", old="        if is_blank(form.get(name)):\n            ok = False\n            missing.append(name)", new="        ok = not is_blank(form.get(name))\n        if not ok:\n            missing.append(name)",
                category="dropped_error", line_offset=0, test="test_first_missing_detected",
                why="ok is reassigned for every field, so an earlier failure is overwritten by a later valid field and invalid forms are reported as valid.")],
  params=[dict(M="formcheck", F="validate_required"), dict(M="signup", F="check_fields")])

# ---------------------------------------------------------------- run_step ignores rc
T("run_step", "easy", "Add @F@ wrapper for build steps",
  base={"@M@.py": '''
class StepFailed(Exception):
    pass
'''},
  good={"@M@.py": '''
class StepFailed(Exception):
    pass


def @F@(runner, cmd):
    rc, out = runner(cmd)
    if rc != 0:
        raise StepFailed("%s exited with %d: %s" % (cmd, rc, out))
    return out
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_exc():
    assert issubclass(m.StepFailed, Exception)

def test_ok():
    needs(m, "@F@")
    assert m.@F@(lambda c: (0, "fine"), "make") == "fine"

def test_nonzero_raises():
    needs(m, "@F@")
    try:
        m.@F@(lambda c: (2, "boom"), "make")
    except m.StepFailed as e:
        assert "boom" in str(e)
        return
    raise AssertionError("non-zero exit code ignored")
''',
  defects=[dict(file="@M@.py", old='    if rc != 0:\n        raise StepFailed("%s exited with %d: %s" % (cmd, rc, out))\n    return out', new="    return out",
                category="dropped_error", line_offset=0, test="test_nonzero_raises", why="The exit code is ignored: a failing build step returns its output as if it had succeeded.")],
  params=[dict(M="build_steps", F="run_step"), dict(M="deploy_tasks", F="exec_command")])

# ---------------------------------------------------------------- HARD: checkout with three defects
T("checkout", "hard", "Charge the card when placing an order in @C@",
  base={"@M@.py": '''
class OutOfStock(Exception):
    pass


class @C@:
    def __init__(self, stock):
        self.stock = dict(stock)
        self.orders = []

    def place(self, item, qty):
        have = self.stock.get(item, 0)
        if have < qty:
            raise OutOfStock(item)
        self.stock[item] = have - qty
        self.orders.append((item, qty))
'''},
  good={"@M@.py": '''
class OutOfStock(Exception):
    pass


class PaymentDeclined(Exception):
    pass


class @C@:
    def __init__(self, stock, charge):
        self.stock = dict(stock)
        self.charge = charge
        self.orders = []

    def place(self, item, qty, price):
        if qty <= 0:
            raise ValueError("qty must be positive")
        have = self.stock.get(item, 0)
        if have < qty:
            raise OutOfStock(item)
        if not self.charge(qty * price):
            raise PaymentDeclined(item)
        self.stock[item] = have - qty
        self.orders.append((item, qty))
'''},
  tests='''
import inspect
import @M@ as m
from _rt import needs_param

def make(stock, ok=True):
    sig = inspect.signature(m.@C@).parameters
    if "charge" in sig:
        return m.@C@(stock, lambda amount: ok)
    return m.@C@(stock)

def place(shop, item, qty):
    if "price" in inspect.signature(shop.place).parameters:
        return shop.place(item, qty, 10)
    return shop.place(item, qty)

def test_basic_order():
    s = make({"a": 5})
    place(s, "a", 2)
    assert s.stock["a"] == 3 and s.orders == [("a", 2)]

def test_out_of_stock():
    s = make({"a": 1})
    try:
        place(s, "a", 2)
    except m.OutOfStock:
        return
    raise AssertionError

def test_buy_all_stock():
    s = make({"a": 2})
    place(s, "a", 2)
    assert s.stock["a"] == 0

def test_nonpositive_qty_rejected():
    needs_param(m.@C@, "charge")
    s = make({"a": 5})
    for q in (0, -3):
        try:
            place(s, "a", q)
        except ValueError:
            continue
        raise AssertionError(q)
    assert s.stock["a"] == 5

def test_decline_raises():
    needs_param(m.@C@, "charge")
    s = make({"a": 5}, ok=False)
    try:
        place(s, "a", 1)
    except m.PaymentDeclined:
        return
    raise AssertionError("declined payment still produced an order")

def test_decline_keeps_stock():
    needs_param(m.@C@, "charge")
    s = make({"a": 5}, ok=False)
    try:
        place(s, "a", 1)
    except m.PaymentDeclined:
        assert s.stock["a"] == 5 and s.orders == []
''',
  defects=[
      dict(file="@M@.py", old="        if have < qty:\n", new="        if have <= qty:\n", category="off_by_one", line_offset=0,
           test="test_buy_all_stock", why="`have <= qty` rejects an order for exactly the remaining stock; only have < qty is out of stock."),
      dict(file="@M@.py", old="        if not self.charge(qty * price):\n            raise PaymentDeclined(item)\n        self.stock[item] = have - qty", new="        self.charge(qty * price)\n        self.stock[item] = have - qty",
           category="dropped_error", line_offset=0, test="test_decline_raises", why="The charge result is ignored, so a declined card still creates the order and decrements stock."),
      dict(file="@M@.py", old='        if qty <= 0:\n            raise ValueError("qty must be positive")\n        have = self.stock.get(item, 0)', new="        have = self.stock.get(item, 0)",
           category="missing_check", line_offset=-1, test="test_nonpositive_qty_rejected", why="Zero/negative quantities are no longer rejected; a negative qty would increase stock and charge a negative amount."),
  ],
  params=[dict(M="shop", C="Shop", _use=[0, 1, 2]), dict(M="ticketing", C="BoxOffice", _use=[1, 2])])

# ---------------------------------------------------------------- HARD: lockout with fake clock
T("lockout", "hard", "Lock accounts after repeated failed logins (@C@)",
  base={"@M@.py": '''
def verify(stored, supplied):
    return stored == supplied
'''},
  good={"@M@.py": '''
def verify(stored, supplied):
    return stored == supplied


class @C@:
    def __init__(self, max_failures, duration, clock):
        self.max_failures = max_failures
        self.duration = duration
        self.clock = clock
        self.fails = {}
        self.locked_until = {}

    def record_failure(self, user):
        self.fails[user] = self.fails.get(user, 0) + 1
        if self.fails[user] >= self.max_failures:
            self.locked_until[user] = self.clock() + self.duration

    def record_success(self, user):
        self.fails.pop(user, None)

    def is_locked(self, user):
        until = self.locked_until.get(user)
        if until is None:
            return False
        return self.clock() < until
'''},
  tests='''
import @M@ as m
from _rt import needs

class Clock:
    def __init__(self):
        self.t = 100
    def __call__(self):
        return self.t

def test_verify():
    assert m.verify("a", "a") and not m.verify("a", "b")

def test_locks_at_threshold():
    needs(m, "@C@")
    c = Clock(); l = m.@C@(3, 60, c)
    l.record_failure("u"); l.record_failure("u")
    assert "u" not in l.locked_until
    l.record_failure("u")
    assert "u" in l.locked_until

def test_unlocks_after_duration():
    needs(m, "@C@")
    c = Clock(); l = m.@C@(1, 60, c)
    l.record_failure("u"); l.record_failure("u")
    assert l.is_locked("u")
    c.t = 161
    assert not l.is_locked("u")

def test_never_failed_not_locked():
    needs(m, "@C@")
    assert not m.@C@(3, 60, Clock()).is_locked("nobody")

def test_success_resets_counter():
    needs(m, "@C@")
    c = Clock(); l = m.@C@(3, 60, c)
    l.record_failure("u"); l.record_failure("u")
    l.record_success("u")
    l.record_failure("u"); l.record_failure("u")
    assert "u" not in l.locked_until
''',
  defects=[
      dict(file="@M@.py", old="        if self.fails[user] >= self.max_failures:", new="        if self.fails[user] > self.max_failures:", category="off_by_one", test="test_locks_at_threshold",
           why="The account is locked one failure too late (> instead of >= max_failures)."),
      dict(file="@M@.py", old="        self.fails.pop(user, None)", new="        pass", category="state_update", test="test_success_resets_counter",
           why="A successful login no longer resets the failure counter, so failures accumulate across successes and users get locked out wrongly."),
      dict(file="@M@.py", old="        return self.clock() < until", new="        return self.clock() > until", category="inverted_condition",
           test="test_unlocks_after_duration", why="The comparison is inverted: an account is reported unlocked while the lock is active and locked once it has expired."),
  ],
  params=[dict(M="lockout", C="LoginGuard", _use=[0, 1, 2]), dict(M="bruteforce", C="AttemptTracker", _use=[1, 2])])
