"""Templates 3: exception handling, return type / backward compat changes."""
TEMPLATES = {}


def T(name, difficulty, title, base, good, tests, defects, params):
    TEMPLATES[name] = (dict(difficulty=difficulty, title=title, base=base, good=good, tests=tests, defects=defects), params)


# ---------------------------------------------------------------- fallback catches too much
T("fallback", "medium", "Add @F@ to fall back to the default when a key is missing",
  base={"@M@.py": '''
def fetch(store, key):
    return store[key]
'''},
  good={"@M@.py": '''
def fetch(store, key):
    return store[key]


def @F@(store, key, default=None):
    try:
        return fetch(store, key)
    except KeyError:
        return default
'''},
  tests='''
import @M@ as m
from _rt import needs

class Broken:
    def __getitem__(self, key):
        raise RuntimeError("backend down")

def test_fetch():
    assert m.fetch({"a": 1}, "a") == 1

def test_default():
    needs(m, "@F@")
    assert m.@F@({}, "a", 5) == 5
    assert m.@F@({"a": 1}, "a", 5) == 1

def test_real_errors_propagate():
    needs(m, "@F@")
    try:
        m.@F@(Broken(), "a", 5)
    except RuntimeError:
        return
    raise AssertionError("backend failure was swallowed")
''',
  defects=[dict(file="@M@.py", old="    except KeyError:\n        return default", new="    except Exception:\n        return default", category="exception_handling",
                test="test_real_errors_propagate", line_offset=0,
                why="Catching Exception hides real failures (backend down, bugs) behind the default; only the expected KeyError should be handled.")],
  params=[dict(M="kvstore", F="fetch_or_default"), dict(M="settings_store", F="get_with_default")])

# ---------------------------------------------------------------- except order
T("except_order", "hard", "Distinguish missing files from other IO errors in @F@",
  base={"@M@.py": '''
def @F@(opener, path):
    try:
        return opener(path).read()
    except OSError:
        return None
'''},
  good={"@M@.py": '''
def @F@(opener, path):
    """Return file text; "" if the file does not exist; None for any other IO problem."""
    try:
        return opener(path).read()
    except FileNotFoundError:
        return ""
    except OSError:
        return None
'''},
  tests='''
import @M@ as m
from _rt import needs

class F:
    def __init__(self, text):
        self.text = text
    def read(self):
        return self.text

def opener_for(exc):
    def op(path):
        if exc:
            raise exc
        return F("data")
    return op

def test_ok():
    assert m.@F@(opener_for(None), "x") == "data"

def test_permission_is_none():
    assert m.@F@(opener_for(PermissionError("no")), "x") is None

def test_missing_is_empty_string():
    needs(m, "@F@")
    import inspect
    if "FileNotFoundError" not in inspect.getsource(m):
        return
    assert m.@F@(opener_for(FileNotFoundError("gone")), "x") == ""
''',
  defects=[dict(file="@M@.py", old='''    except FileNotFoundError:
        return ""
    except OSError:
        return None''', new='''    except OSError:
        return None
    except FileNotFoundError:
        return ""''', category="exception_handling", line_offset=2, test="test_missing_is_empty_string",
                why="`except OSError` is listed before `except FileNotFoundError`; FileNotFoundError is a subclass so the specific handler is unreachable and missing files return None instead of ''.")],
  params=[dict(M="readers", F="read_text"), dict(M="fileio", F="slurp", _diff="hard")])

# ---------------------------------------------------------------- finally return swallows
T("cleanup_finally", "hard", "Always record the attempt in @F@ using finally",
  base={"@M@.py": '''
def @F@(job, log):
    result = job()
    log.append("done")
    return result
'''},
  good={"@M@.py": '''
def @F@(job, log):
    try:
        return job()
    finally:
        log.append("done")
'''},
  tests='''
import @M@ as m

def test_result():
    log = []
    assert m.@F@(lambda: 7, log) == 7
    assert log == ["done"]

def test_exception_propagates():
    log = []
    def boom():
        raise ValueError("bad")
    try:
        m.@F@(boom, log)
    except ValueError:
        return
    raise AssertionError("exception was swallowed")
''',
  defects=[dict(file="@M@.py", old="    finally:\n        log.append(\"done\")", new="    finally:\n        log.append(\"done\")\n        return None",
                category="exception_handling", line_offset=2, test="test_exception_propagates",
                why="`return` inside `finally` discards any in-flight exception (and the job result), so failures are silently turned into None.")],
  params=[dict(M="jobs", F="run_job"), dict(M="tasks_runner", F="execute")])

# ---------------------------------------------------------------- retry catches non-transient
T("retry", "medium", "Add a small retry helper @F@ for flaky calls",
  base={"@M@.py": '''
class TransientError(Exception):
    pass
'''},
  good={"@M@.py": '''
class TransientError(Exception):
    pass


def @F@(fn, attempts=3):
    last = None
    for _ in range(attempts):
        try:
            return fn()
        except TransientError as e:
            last = e
    raise last
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_exc_class():
    assert issubclass(m.TransientError, Exception)

def test_succeeds_after_transient():
    needs(m, "@F@")
    calls = []
    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise m.TransientError("flaky")
        return "ok"
    assert m.@F@(fn, attempts=3) == "ok"

def test_gives_up_with_last_error():
    needs(m, "@F@")
    def fn():
        raise m.TransientError("still down")
    try:
        m.@F@(fn, attempts=2)
    except m.TransientError as e:
        assert str(e) == "still down"
        return
    raise AssertionError

def test_permanent_error_not_retried():
    needs(m, "@F@")
    calls = []
    def fn():
        calls.append(1)
        raise ValueError("bad input")
    try:
        m.@F@(fn, attempts=3)
    except ValueError:
        assert len(calls) == 1
        return
    raise AssertionError
''',
  defects=[
      dict(file="@M@.py", old="        except TransientError as e:", new="        except Exception as e:", category="exception_handling", test="test_permanent_error_not_retried",
           why="Every exception is retried (and finally re-raised) - programming errors / bad input are retried and delayed instead of failing fast; only TransientError should be retried."),
  ],
  params=[dict(M="resilience", F="retry_call"), dict(M="flaky", F="with_retries")])

# ---------------------------------------------------------------- context manager swallowing
T("ctx_swallow", "hard", "Add timing context manager @F@",
  base={"@M@.py": '''
import time


def now():
    return time.monotonic()
'''},
  good={"@M@.py": '''
import time


def now():
    return time.monotonic()


class @F@:
    def __init__(self, sink, clock=now):
        self.sink = sink
        self.clock = clock

    def __enter__(self):
        self.t0 = self.clock()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.sink.append(self.clock() - self.t0)
        return False
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_now_is_float():
    assert isinstance(m.now(), float)

def test_records():
    needs(m, "@F@")
    ticks = iter([1.0, 4.0])
    sink = []
    with m.@F@(sink, clock=lambda: next(ticks)):
        pass
    assert sink == [3.0]

def test_exceptions_propagate():
    needs(m, "@F@")
    sink = []
    try:
        with m.@F@(sink, clock=lambda: 0.0):
            raise ValueError("inside")
    except ValueError:
        assert len(sink) == 1
        return
    raise AssertionError("exception swallowed by __exit__")
''',
  defects=[dict(file="@M@.py", old="        self.sink.append(self.clock() - self.t0)\n        return False", new="        self.sink.append(self.clock() - self.t0)\n        return True",
                category="exception_handling", line_offset=1, test="test_exceptions_propagate",
                why="__exit__ returns True, which suppresses every exception raised inside the with-block.")],
  params=[dict(M="timing", F="Timer"), dict(M="profiler", F="Stopwatch")])

# ---------------------------------------------------------------- return type change: None -> []
T("find_first", "easy", "Generalise @F@ to take a predicate",
  base={"@M@.py": '''
def @F@(items, value):
    for it in items:
        if it == value:
            return it
    return None
'''},
  good={"@M@.py": '''
def @F@(items, pred):
    if not callable(pred):
        value = pred
        pred = lambda it: it == value
    for it in items:
        if pred(it):
            return it
    return None
'''},
  tests='''
import @M@ as m
from _rt import needs_param

def test_value():
    assert m.@F@([1, 2, 3], 2) == 2

def test_missing_is_none():
    assert m.@F@([1, 2, 3], 9) is None

def test_predicate():
    needs_param(m.@F@, "pred")
    assert m.@F@([1, 2, 3], lambda x: x > 1) == 2
''',
  defects=[dict(file="@M@.py", old="        if pred(it):\n            return it\n    return None", new="        if pred(it):\n            return it\n    return []", category="return_type_change",
                line_offset=2, test="test_missing_is_none",
                why="The not-found result changed from None to [] - callers that test `is None` (and an empty list is falsy but not None) break; the return type is inconsistent.")],
  params=[dict(M="lookup", F="find_first"), dict(M="collections_ext", F="first_match")])

# ---------------------------------------------------------------- return type: dict -> list of tuples in a branch
T("parse_kv", "medium", "Add strict mode to @F@",
  base={"@M@.py": '''
def @F@(text):
    out = {}
    for part in text.split(";"):
        if not part.strip():
            continue
        k, _, v = part.partition("=")
        out[k.strip()] = v.strip()
    return out
'''},
  good={"@M@.py": '''
def @F@(text, strict=False):
    out = {}
    for part in text.split(";"):
        if not part.strip():
            continue
        k, sep, v = part.partition("=")
        if strict and not sep:
            raise ValueError("missing '=' in %r" % part)
        out[k.strip()] = v.strip()
    return out
'''},
  tests='''
import @M@ as m
from _rt import needs_param

def test_basic():
    assert m.@F@("a=1; b=2") == {"a": "1", "b": "2"}

def test_empty_returns_dict():
    assert m.@F@("") == {}

def test_strict_error():
    needs_param(m.@F@, "strict")
    try:
        m.@F@("a=1;oops", strict=True)
    except ValueError:
        return
    raise AssertionError

def test_strict_ok_still_dict():
    needs_param(m.@F@, "strict")
    assert m.@F@("a=1", strict=True) == {"a": "1"}
''',
  defects=[dict(file="@M@.py", old="        out[k.strip()] = v.strip()\n    return out", new="        out[k.strip()] = v.strip()\n    return out if not strict else list(out.items())",
                category="return_type_change", line_offset=1, test="test_strict_ok_still_dict",
                why="In strict mode the function returns a list of tuples instead of a dict, so the return type depends on a flag and callers indexing the result break.")],
  params=[dict(M="kvparse", F="parse_kv"), dict(M="cookie_util", F="parse_pairs")])

# ---------------------------------------------------------------- sort in place returns None
T("top_n", "easy", "Rewrite @F@ to avoid building a full sorted copy twice",
  base={"@M@.py": '''
def @F@(items, n):
    return sorted(items, reverse=True)[:n]
'''},
  good={"@M@.py": '''
import heapq


def @F@(items, n):
    return heapq.nlargest(n, items)
'''},
  tests='''
import @M@ as m

def test_top():
    assert m.@F@([5, 1, 9, 3], 2) == [9, 5]

def test_does_not_mutate():
    xs = [3, 1, 2]
    m.@F@(xs, 2)
    assert xs == [3, 1, 2]

def test_n_larger():
    assert m.@F@([1, 2], 5) == [2, 1]
''',
  defects=[dict(file="@M@.py", old="    return heapq.nlargest(n, items)", new="    items.sort(reverse=True)\n    return items[:n]",
                category="state_update", line_offset=0, test="test_does_not_mutate",
                why="items.sort() sorts the caller's list in place - a hidden side effect that the original (sorted copy) did not have.")],
  params=[dict(M="ranking", F="top_n"), dict(M="leaderboard", F="best_scores")])

# ---------------------------------------------------------------- backward compat: new required param
T("greet", "easy", "Allow customising the greeting in @F@",
  base={"@M@.py": '''
def @F@(name):
    return "Hello, " + name + "!"
'''},
  good={"@M@.py": '''
def @F@(name, greeting="Hello"):
    return greeting + ", " + name + "!"
'''},
  tests='''
import @M@ as m

def test_default():
    assert m.@F@("Ann") == "Hello, Ann!"

def test_custom():
    import inspect
    if "greeting" not in inspect.signature(m.@F@).parameters:
        return
    assert m.@F@("Ann", greeting="Hi") == "Hi, Ann!"
''',
  defects=[dict(file="@M@.py", old='def @F@(name, greeting="Hello"):', new="def @F@(name, greeting):", category="backward_compat", test="test_default",
                why="The new `greeting` parameter has no default, so every existing call @F@(name) now raises TypeError.")],
  params=[dict(M="welcome", F="greet"), dict(M="mailer_text", F="salutation")])

# ---------------------------------------------------------------- backward compat: renamed key read by another module
T("report_keys", "hard", "Tidy the summary dict returned by @F@",
  base={"@M@.py": '''
def @F@(orders):
    return {"total": sum(o["amount"] for o in orders), "count": len(orders)}
''', "@R@.py": '''
from @M@ import @F@


def headline(orders):
    s = @F@(orders)
    return "%d orders, %.2f total" % (s["count"], s["total"])
'''},
  good={"@M@.py": '''
def @F@(orders):
    amounts = [o["amount"] for o in orders]
    return {"total": sum(amounts), "count": len(amounts), "largest": max(amounts, default=0)}
'''},
  tests='''
import @M@ as m
import @R@ as r

def test_summary_keys():
    s = m.@F@([{"amount": 5}, {"amount": 7}])
    assert s["total"] == 12 and s["count"] == 2

def test_headline_still_works():
    assert r.headline([{"amount": 5}, {"amount": 7.5}]) == "2 orders, 12.50 total"

def test_largest():
    s = m.@F@([{"amount": 5}, {"amount": 7}])
    if "largest" in s:
        assert s["largest"] == 7
''',
  defects=[dict(file="@M@.py", old='return {"total": sum(amounts), "count": len(amounts), "largest": max(amounts, default=0)}',
                new='return {"sum": sum(amounts), "count": len(amounts), "largest": max(amounts, default=0)}', category="backward_compat",
                test="test_headline_still_works", why="The \"total\" key was renamed to \"sum\" but other callers (the headline module) still read s[\"total\"], which now raises KeyError.")],
  params=[dict(M="order_stats", F="summarize_orders", R="order_report"), dict(M="sales", F="rollup", R="dashboard_text")])

# ---------------------------------------------------------------- backward compat: default value silently changed
T("deadline", "medium", "Refactor deadline computation into @F@",
  base={"@M@.py": '''
def @F@(start, timeout=@T@):
    return start + timeout
'''},
  good={"@M@.py": '''
DEFAULT_TIMEOUT = @T@


def @F@(start, timeout=DEFAULT_TIMEOUT):
    if timeout < 0:
        raise ValueError("timeout must be >= 0")
    return start + timeout
'''},
  tests='''
import @M@ as m

def test_default_timeout_unchanged():
    assert m.@F@(100) == 100 + @T@

def test_explicit():
    assert m.@F@(100, 5) == 105

def test_negative():
    import inspect
    if not hasattr(m, "DEFAULT_TIMEOUT"):
        return
    try:
        m.@F@(1, -1)
    except ValueError:
        return
    raise AssertionError
''',
  defects=[dict(file="@M@.py", old="DEFAULT_TIMEOUT = @T@", new="DEFAULT_TIMEOUT = @T2@", category="backward_compat", test="test_default_timeout_unchanged",
                why="The refactor silently changes the default timeout from @T@ to @T2@ seconds; every caller relying on the default now gets a different deadline.")],
  params=[dict(M="scheduler", F="deadline_for", T=30, T2=3), dict(M="rpc_client", F="compute_deadline", T=60, T2=6)])
