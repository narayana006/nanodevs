"""Templates 2: missing None/empty checks, resource leaks, injection."""
TEMPLATES = {}


def T(name, difficulty, title, base, good, tests, defects, params):
    TEMPLATES[name] = (dict(difficulty=difficulty, title=title, base=base, good=good, tests=tests, defects=defects), params)


# ---------------------------------------------------------------- summarize (empty input)
T("summarize", "easy", "Add @F@ with count/min/max/mean",
  base={"@M@.py": '''
def mean(xs):
    return sum(xs) / len(xs)
'''},
  good={"@M@.py": '''
def mean(xs):
    return sum(xs) / len(xs)


def @F@(xs):
    if not xs:
        return {"count": 0, "min": None, "max": None, "mean": None}
    lo = min(xs)
    hi = max(xs)
    return {"count": len(xs), "min": lo, "max": hi, "mean": mean(xs)}
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_mean():
    assert m.mean([2, 4]) == 3

def test_summary():
    needs(m, "@F@")
    assert m.@F@([1, 2, 6]) == {"count": 3, "min": 1, "max": 6, "mean": 3}

def test_summary_empty():
    needs(m, "@F@")
    assert m.@F@([]) == {"count": 0, "min": None, "max": None, "mean": None}
''',
  defects=[dict(file="@M@.py", old='    if not xs:\n        return {"count": 0, "min": None, "max": None, "mean": None}\n    lo = min(xs)\n',
                new="    lo = min(xs)\n", category="missing_check", test="test_summary_empty",
                why="The empty-input guard was removed: min([]) raises ValueError, so summarising an empty list crashes instead of returning the zero-count summary.")],
  params=[dict(M="stats", F="summarize"), dict(M="metrics", F="describe")])

# ---------------------------------------------------------------- mention (None lookup)
T("mention", "easy", "Add @F@ to render a user mention from the directory",
  base={"@M@.py": '''
USERS = {}


def display_name(user):
    return user.get("nick") or user["name"]
'''},
  good={"@M@.py": '''
USERS = {}


def display_name(user):
    return user.get("nick") or user["name"]


def @F@(users, uid):
    user = users.get(uid)
    if user is None:
        return "@unknown"
    return "@" + display_name(user)
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_display_name():
    assert m.display_name({"name": "Ann", "nick": "annie"}) == "annie"
    assert m.display_name({"name": "Ann"}) == "Ann"

def test_mention_known():
    needs(m, "@F@")
    assert m.@F@({1: {"name": "Ann"}}, 1) == "@Ann"

def test_mention_unknown():
    needs(m, "@F@")
    assert m.@F@({1: {"name": "Ann"}}, 2) == "@unknown"
''',
  defects=[dict(file="@M@.py", old='    user = users.get(uid)\n    if user is None:\n        return "@unknown"\n    return "@" + display_name(user)',
                new='    user = users.get(uid)\n    return "@" + display_name(user)', category="missing_check", line_offset=1,
                test="test_mention_unknown", why="users.get() can return None for an unknown id; the None check was dropped so display_name(None) raises TypeError.")],
  params=[dict(M="mentions", F="mention"), dict(M="notify_text", F="tag_user")])

# ---------------------------------------------------------------- port from config
T("config_port", "medium", "Read the listen port from config via @F@",
  base={"@M@.py": '''
DEFAULT_PORT = @DEF@
'''},
  good={"@M@.py": '''
DEFAULT_PORT = @DEF@


def @F@(cfg):
    raw = cfg.get("port")
    if raw is None or raw == "":
        return DEFAULT_PORT
    port = int(raw)
    if not 0 < port < 65536:
        raise ValueError("port out of range: %d" % port)
    return port
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_default_const():
    assert m.DEFAULT_PORT == @DEF@

def test_default_when_missing():
    needs(m, "@F@")
    assert m.@F@({}) == @DEF@
    assert m.@F@({"port": None}) == @DEF@
    assert m.@F@({"port": ""}) == @DEF@

def test_string_port():
    needs(m, "@F@")
    assert m.@F@({"port": "9000"}) == 9000

def test_range():
    needs(m, "@F@")
    for bad in (0, 70000, -1):
        try:
            m.@F@({"port": bad})
        except ValueError:
            continue
        raise AssertionError(bad)
    assert m.@F@({"port": 65535}) == 65535
''',
  defects=[
      dict(file="@M@.py", old='    if raw is None or raw == "":\n        return DEFAULT_PORT\n    port = int(raw)\n', new="    port = int(raw)\n", category="missing_check",
           test="test_default_when_missing", why="A missing/None/empty port is no longer defaulted: int(None) raises TypeError and int('') raises ValueError."),
      dict(file="@M@.py", old='    if not 0 < port < 65536:\n        raise ValueError("port out of range: %d" % port)\n    return port', new="    return port", category="missing_check",
           test="test_range", why="The range validation was removed, so 0, negative and > 65535 ports are accepted."),
  ],
  params=[dict(M="server_cfg", F="listen_port", DEF=8080, _use=[0]), dict(M="appconfig", F="get_port", DEF=5432, _use=[0, 1], _diff="medium")])

# ---------------------------------------------------------------- first token (IndexError on empty)
T("first_token", "easy", "Add @F@ to pull the leading token out of a user command",
  base={"@M@.py": '''
def normalize(line):
    return " ".join(line.split())
'''},
  good={"@M@.py": '''
def normalize(line):
    return " ".join(line.split())


def @F@(line):
    parts = normalize(line).split(" ")
    if not parts or not parts[0]:
        return None
    return parts[0].lower()
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_normalize():
    assert m.normalize("  a   b ") == "a b"

def test_first():
    needs(m, "@F@")
    assert m.@F@("  HELP me ") == "help"

def test_blank():
    needs(m, "@F@")
    assert m.@F@("   ") is None
    assert m.@F@("") is None
''',
  defects=[dict(file="@M@.py", old='    parts = normalize(line).split(" ")\n    if not parts or not parts[0]:\n        return None\n    return parts[0].lower()',
                new='    parts = normalize(line).split(" ")\n    return parts[0].lower()', category="missing_check", line_offset=1,
                test="test_blank", why="Blank input is no longer handled; the first token is '' for blank input so the function returns '' (and callers expecting None for 'no command' misbehave).")],
  params=[dict(M="cmdparse", F="command_name"), dict(M="chatbot", F="verb_of")])

# ---------------------------------------------------------------- ratio (zero denominator)
T("rate", "easy", "Add @F@ for dashboard conversion numbers",
  base={"@M@.py": '''
def pct(part, whole):
    return round(100.0 * part / whole, 1)
'''},
  good={"@M@.py": '''
def pct(part, whole):
    return round(100.0 * part / whole, 1)


def @F@(@A@, @B@):
    if @A@ == 0:
        return None
    return pct(@B@, @A@)
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_pct():
    assert m.pct(1, 4) == 25.0

def test_rate():
    needs(m, "@F@")
    assert m.@F@(200, 50) == 25.0

def test_rate_zero():
    needs(m, "@F@")
    assert m.@F@(0, 0) is None
''',
  defects=[dict(file="@M@.py", old="    if @A@ == 0:\n        return None\n    return pct(@B@, @A@)", new="    return pct(@B@, @A@)", category="missing_check", line_offset=0,
                test="test_rate_zero", why="No guard for a zero denominator: pct(0, 0) raises ZeroDivisionError where the dashboard expects None.")],
  params=[dict(M="funnel", F="conversion", A="visits", B="signups"), dict(M="kpis", F="hit_rate", A="lookups", B="hits")])

# ---------------------------------------------------------------- resource leak: file opener
T("load_rows", "medium", "Let @F@ take an injectable opener and skip blank lines",
  base={"@M@.py": '''
def parse(line):
    name, qty = line.strip().split(",")
    return name, int(qty)


def @F@(path):
    with open(path) as f:
        return [parse(l) for l in f]
'''},
  good={"@M@.py": '''
def parse(line):
    name, qty = line.strip().split(",")
    return name, int(qty)


def @F@(path, opener=open):
    f = opener(path)
    try:
        return [parse(l) for l in f if l.strip()]
    finally:
        f.close()
'''},
  tests='''
import @M@ as m
from _rt import needs_param

class FakeFile:
    def __init__(self, lines):
        self.lines = lines
        self.closed = False
    def __iter__(self):
        return iter(self.lines)
    def close(self):
        self.closed = True

def test_parse():
    assert m.parse("a,3\\n") == ("a", 3)

def test_rows_and_closed():
    needs_param(m.@F@, "opener")
    f = FakeFile(["a,1\\n", "\\n", "b,2\\n"])
    assert m.@F@("x", opener=lambda p: f) == [("a", 1), ("b", 2)]
    assert f.closed

def test_closed_on_error():
    needs_param(m.@F@, "opener")
    f = FakeFile(["a,1\\n", "garbage\\n"])
    try:
        m.@F@("x", opener=lambda p: f)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    assert f.closed
''',
  defects=[dict(file="@M@.py", old='''    f = opener(path)
    try:
        return [parse(l) for l in f if l.strip()]
    finally:
        f.close()''', new='''    f = opener(path)
    rows = [parse(l) for l in f if l.strip()]
    f.close()
    return rows''', category="resource_leak", line_offset=1, test="test_closed_on_error",
                why="The file is closed only on the success path; if parse() raises on a bad row the handle is leaked (no try/finally or with).")],
  params=[dict(M="inventory_io", F="load_rows"), dict(M="csv_loader", F="read_stock")])

# ---------------------------------------------------------------- resource leak: db connection
T("with_conn", "medium", "Add @F@ helper that runs a callback with a fresh connection",
  base={"@M@.py": '''
def connect():
    raise NotImplementedError
'''},
  good={"@M@.py": '''
def connect():
    raise NotImplementedError


def @F@(fn, factory=connect):
    conn = factory()
    try:
        return fn(conn)
    finally:
        conn.close()
'''},
  tests='''
import @M@ as m
from _rt import needs

class Conn:
    def __init__(self):
        self.closed = 0
    def close(self):
        self.closed += 1

def test_connect_stub():
    try:
        m.connect()
    except NotImplementedError:
        return
    raise AssertionError

def test_result_and_close():
    needs(m, "@F@")
    c = Conn()
    assert m.@F@(lambda conn: 42, factory=lambda: c) == 42
    assert c.closed == 1

def test_close_on_error():
    needs(m, "@F@")
    c = Conn()
    def boom(conn):
        raise RuntimeError("x")
    try:
        m.@F@(boom, factory=lambda: c)
    except RuntimeError:
        pass
    else:
        raise AssertionError
    assert c.closed == 1
''',
  defects=[dict(file="@M@.py", old='''    conn = factory()
    try:
        return fn(conn)
    finally:
        conn.close()''', new='''    conn = factory()
    result = fn(conn)
    conn.close()
    return result''', category="resource_leak", line_offset=1, test="test_close_on_error",
                why="conn.close() is skipped when the callback raises (no try/finally), leaking the connection on every failure.")],
  params=[dict(M="dbutil", F="with_connection"), dict(M="storage_helpers", F="run_in_conn")])

# ---------------------------------------------------------------- resource leak: lock on early return
T("locked_cache", "hard", "Make @F@ thread-safe with a lock",
  base={"@M@.py": '''
def @F@(cache, key, factory):
    if key in cache:
        return cache[key]
    cache[key] = factory(key)
    return cache[key]
'''},
  good={"@M@.py": '''
import threading

LOCK = threading.Lock()


def @F@(cache, key, factory, lock=LOCK):
    with lock:
        if key in cache:
            return cache[key]
        cache[key] = factory(key)
        return cache[key]
'''},
  tests='''
import threading
import @M@ as m
from _rt import needs_param

def test_basic():
    c = {}
    assert m.@F@(c, "a", lambda k: k.upper()) == "A"
    assert m.@F@(c, "a", lambda k: "other") == "A"

def test_lock_released_after_hit():
    needs_param(m.@F@, "lock")
    lk = threading.Lock()
    c = {"a": 1}
    assert m.@F@(c, "a", lambda k: 2, lock=lk) == 1
    assert not lk.locked()

def test_lock_released_after_miss_and_error():
    needs_param(m.@F@, "lock")
    lk = threading.Lock()
    m.@F@({}, "b", lambda k: 3, lock=lk)
    assert not lk.locked()
    def boom(k):
        raise KeyError(k)
    try:
        m.@F@({}, "c", boom, lock=lk)
    except KeyError:
        pass
    assert not lk.locked()
''',
  defects=[dict(file="@M@.py", old='''    with lock:
        if key in cache:
            return cache[key]
        cache[key] = factory(key)
        return cache[key]''', new='''    lock.acquire()
    if key in cache:
        return cache[key]
    cache[key] = factory(key)
    lock.release()
    return cache[key]''', category="resource_leak", line_offset=0, test="test_lock_released_after_hit",
                why="The early `return cache[key]` (and any exception from factory) leaves the lock acquired forever; acquire/release must be paired with `with lock:` or try/finally.")],
  params=[dict(M="memo", F="get_or_create"), dict(M="registry", F="lookup_or_build", _diff="hard")])

# ---------------------------------------------------------------- SQL injection: search by name
T("sql_search", "easy", "Add @F@ to search accounts by name",
  base={"@M@.py": '''
import sqlite3


def init(conn):
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")


def add(conn, name, email):
    conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
'''},
  good={"@M@.py": '''
import sqlite3


def init(conn):
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")


def add(conn, name, email):
    conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))


def @F@(conn, name):
    cur = conn.execute("SELECT id, name, email FROM users WHERE name = ?", (name,))
    return cur.fetchall()
'''},
  tests='''
import sqlite3
import @M@ as m
from _rt import needs

def make():
    conn = sqlite3.connect(":memory:")
    m.init(conn)
    m.add(conn, "ann", "ann@example.com")
    m.add(conn, "bob", "bob@example.com")
    return conn

def test_add():
    assert make().execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2

def test_find():
    needs(m, "@F@")
    rows = m.@F@(make(), "ann")
    assert [r[1] for r in rows] == ["ann"]

def test_quote_in_name():
    needs(m, "@F@")
    conn = make()
    m.add(conn, "o'neil", "o@example.com")
    assert [r[1] for r in m.@F@(conn, "o'neil")] == ["o'neil"]

def test_injection_returns_nothing():
    needs(m, "@F@")
    assert m.@F@(make(), "x' OR '1'='1") == []
''',
  defects=[dict(file="@M@.py", old='    cur = conn.execute("SELECT id, name, email FROM users WHERE name = ?", (name,))',
                new="    cur = conn.execute(f\"SELECT id, name, email FROM users WHERE name = '{name}'\")", category="injection",
                test="test_injection_returns_nothing", why="The name is interpolated into the SQL string with an f-string (SQL injection, and it breaks on quotes); use a bound parameter.")],
  params=[dict(M="accounts", F="find_by_name"), dict(M="userdb", F="search_users")])

# ---------------------------------------------------------------- SQL: whitelisted ORDER BY (f-string is fine here)
T("sql_order", "hard", "Allow sorting the user list by a chosen column",
  base={"@M@.py": '''
def init(conn):
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")


def add(conn, name, age):
    conn.execute("INSERT INTO users (name, age) VALUES (?, ?)", (name, age))


def all_users(conn):
    return conn.execute("SELECT name, age FROM users ORDER BY id").fetchall()
'''},
  good={"@M@.py": '''
SORTABLE = ("id", "name", "age")


def init(conn):
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")


def add(conn, name, age):
    conn.execute("INSERT INTO users (name, age) VALUES (?, ?)", (name, age))


def all_users(conn, sort_by="id", desc=False):
    if sort_by not in SORTABLE:
        raise ValueError("cannot sort by %r" % (sort_by,))
    direction = "DESC" if desc else "ASC"
    # identifiers cannot be bound parameters; sort_by is validated against SORTABLE above
    return conn.execute(f"SELECT name, age FROM users ORDER BY {sort_by} {direction}").fetchall()
'''},
  tests='''
import sqlite3
import @M@ as m
from _rt import needs_param

def make():
    conn = sqlite3.connect(":memory:")
    m.init(conn)
    m.add(conn, "bob", 30)
    m.add(conn, "ann", 25)
    return conn

def test_default_order():
    assert m.all_users(make()) == [("bob", 30), ("ann", 25)]

def test_sort_name():
    needs_param(m.all_users, "sort_by")
    assert m.all_users(make(), sort_by="name") == [("ann", 25), ("bob", 30)]

def test_desc():
    needs_param(m.all_users, "sort_by")
    assert m.all_users(make(), sort_by="age", desc=True) == [("bob", 30), ("ann", 25)]

def test_rejects_unknown_column():
    needs_param(m.all_users, "sort_by")
    for bad in ("password", "name; DROP TABLE users", "1"):
        try:
            m.all_users(make(), sort_by=bad)
        except ValueError:
            continue
        raise AssertionError(bad)
''',
  defects=[dict(file="@M@.py", old='    if sort_by not in SORTABLE:\n        raise ValueError("cannot sort by %r" % (sort_by,))\n    direction = "DESC" if desc else "ASC"\n',
                new='    direction = "DESC" if desc else "ASC"\n', category="injection", test="test_rejects_unknown_column",
                why="The whitelist check on sort_by was dropped while the value is still interpolated into the SQL text, allowing SQL injection through the sort parameter.")],
  params=[dict(M="userlist", _diff="hard"), dict(M="roster", _diff="hard")])

# ---------------------------------------------------------------- shell command
T("run_ping", "medium", "Add @F@ that pings a host through an injectable runner",
  base={"@M@.py": '''
import re

HOST_RE = re.compile(r"[A-Za-z0-9._-]+")
'''},
  good={"@M@.py": '''
import re
import subprocess

HOST_RE = re.compile(r"[A-Za-z0-9._-]+")


def @F@(host, runner=subprocess.run):
    if not HOST_RE.fullmatch(host) or host.startswith("-"):
        raise ValueError("invalid host: %r" % (host,))
    return runner(["ping", "-c", "1", host], shell=False, capture_output=True, text=True)
'''},
  tests='''
import @M@ as m
from _rt import needs

class Rec:
    def __init__(self):
        self.calls = []
    def __call__(self, cmd, **kw):
        self.calls.append((cmd, kw))
        return "ok"

def test_regex():
    assert m.HOST_RE.fullmatch("example.com")

def test_argv_list_no_shell():
    needs(m, "@F@")
    r = Rec()
    assert m.@F@("example.com", runner=r) == "ok"
    cmd, kw = r.calls[0]
    assert cmd == ["ping", "-c", "1", "example.com"] and not kw.get("shell")

def test_rejects_metacharacters():
    needs(m, "@F@")
    r = Rec()
    for bad in ("a; rm -rf /", "x && id", "$(id)", ""):
        try:
            m.@F@(bad, runner=r)
        except ValueError:
            continue
        raise AssertionError(bad)
    assert not r.calls

def test_rejects_option_injection():
    needs(m, "@F@")
    r = Rec()
    try:
        m.@F@("-f", runner=r)
    except ValueError:
        assert not r.calls
        return
    raise AssertionError
''',
  defects=[
      dict(file="@M@.py", old='    return runner(["ping", "-c", "1", host], shell=False, capture_output=True, text=True)',
           new='    return runner("ping -c 1 " + host, shell=True, capture_output=True, text=True)', category="injection", test="test_argv_list_no_shell",
           why="The command is built by string concatenation and run with shell=True: shell metacharacters in host are executed."),
      dict(file="@M@.py", old='    if not HOST_RE.fullmatch(host) or host.startswith("-"):', new='    if not HOST_RE.fullmatch(host):', category="injection", test="test_rejects_option_injection",
           why="A host starting with '-' passes the regex and is interpreted by ping as an option (argument injection); it must be rejected."),
  ],
  params=[dict(M="netcheck", F="ping_host", _use=[0]), dict(M="diag", F="check_reachable", _use=[1], _diff="medium")])

# ---------------------------------------------------------------- path traversal
T("safe_join", "medium", "Serve user uploads through @F@",
  base={"@M@.py": '''
import posixpath


def clean_name(name):
    return name.strip()
'''},
  good={"@M@.py": '''
import posixpath


def clean_name(name):
    return name.strip()


def @F@(root, name):
    name = clean_name(name)
    full = posixpath.normpath(posixpath.join(root, name))
    if full != root and not full.startswith(root.rstrip("/") + "/"):
        raise ValueError("path escapes root")
    return full
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_clean_name():
    assert m.clean_name(" a.txt ") == "a.txt"

def test_ok():
    needs(m, "@F@")
    assert m.@F@("/srv/@D@", "a/b.txt") == "/srv/@D@/a/b.txt"

def test_dotdot_rejected():
    needs(m, "@F@")
    for bad in ("../etc/passwd", "a/../../x", "/etc/passwd"):
        try:
            m.@F@("/srv/@D@", bad)
        except ValueError:
            continue
        raise AssertionError(bad)

def test_sibling_prefix_rejected():
    needs(m, "@F@")
    try:
        m.@F@("/srv/@D@", "../@D@-private/x")
    except ValueError:
        return
    raise AssertionError
''',
  defects=[
      dict(file="@M@.py", old='    if full != root and not full.startswith(root.rstrip("/") + "/"):\n        raise ValueError("path escapes root")\n    return full',
           new='    return full', category="injection", line_offset=0, test="test_dotdot_rejected",
           why="The containment check was dropped, so '../' sequences and absolute paths escape the upload root (path traversal)."),
      dict(file="@M@.py", old='    if full != root and not full.startswith(root.rstrip("/") + "/"):', new='    if full != root and not full.startswith(root):', category="injection",
           test="test_sibling_prefix_rejected", why="A bare startswith(root) also accepts sibling directories sharing the prefix (/srv/x-private); the check must compare against root + '/'."),
  ],
  params=[dict(M="uploads", F="safe_join", D="uploads", _use=[0]), dict(M="static_files", F="resolve_under", D="static", _use=[1], _diff="hard")])

# ---------------------------------------------------------------- HTML escaping
T("render_comment", "easy", "Render comments as HTML with @F@",
  base={"@M@.py": '''
def initials(name):
    return "".join(p[0].upper() for p in name.split())
'''},
  good={"@M@.py": '''
import html


def initials(name):
    return "".join(p[0].upper() for p in name.split())


def @F@(author, text):
    return '<div class="comment"><b>%s</b>: %s</div>' % (html.escape(author), html.escape(text))
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_initials():
    assert m.initials("ann lee") == "AL"

def test_render():
    needs(m, "@F@")
    assert m.@F@("ann", "hi") == '<div class="comment"><b>ann</b>: hi</div>'

def test_escapes_author():
    needs(m, "@F@")
    assert "<script>" not in m.@F@("<script>x</script>", "hi")

def test_escapes_text():
    needs(m, "@F@")
    out = m.@F@("ann", "<img src=x onerror=alert(1)>")
    assert "<img" not in out and "&lt;img" in out
''',
  defects=[
      dict(file="@M@.py", old="html.escape(author), html.escape(text))", new="html.escape(author), text)", category="injection", test="test_escapes_text",
           why="The comment body is inserted without html.escape, allowing stored XSS."),
      dict(file="@M@.py", old="% (html.escape(author), html.escape(text))", new="% (author, html.escape(text))", category="injection", test="test_escapes_author",
           why="The author name is inserted into HTML unescaped (XSS through the display name)."),
  ],
  params=[dict(M="comments", F="render_comment", _use=[0]), dict(M="forum_html", F="render_post", _use=[1])])

# ---------------------------------------------------------------- eval
T("parse_number", "easy", "Parse numeric form fields with @F@",
  base={"@M@.py": '''
def strip_units(s):
    return s.strip().rstrip("%").strip()
'''},
  good={"@M@.py": '''
def strip_units(s):
    return s.strip().rstrip("%").strip()


def @F@(s):
    try:
        return float(strip_units(s))
    except ValueError:
        raise ValueError("not a number: %r" % (s,)) from None
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_strip():
    assert m.strip_units(" 5 % ") == "5"

def test_number():
    needs(m, "@F@")
    assert m.@F@(" 12.5% ") == 12.5

def test_expression_rejected():
    needs(m, "@F@")
    for bad in ("2+3", "__import__('os').getcwd()", "abc", ""):
        try:
            m.@F@(bad)
        except ValueError:
            continue
        raise AssertionError(bad)
''',
  defects=[dict(file="@M@.py", old="""    try:
        return float(strip_units(s))
    except ValueError:
        raise ValueError("not a number: %r" % (s,)) from None""", new="""    try:
        return float(eval(strip_units(s)))
    except (SyntaxError, NameError):
        raise ValueError("not a number: %r" % (s,)) from None""", category="injection", line_offset=1, test="test_expression_rejected",
                why="eval() on user input executes arbitrary code (and accepts expressions like 2+3); use float().")],
  params=[dict(M="forms", F="parse_number"), dict(M="inputs", F="to_float")])
