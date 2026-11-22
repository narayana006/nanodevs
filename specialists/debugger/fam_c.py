"""Hard families: 5-6 files, the traceback points at a symptom site, red herrings."""
from fam_a import fam

# 22 ---------------------------------------------------------------- stale cache: key ignores store version
fam(key="versioned_cache", cat="stale cache", diff="hard", tags=["red_herring", "flaky_looking"],
    files={
        "clock.py": r'''
class FakeClock:
    def __init__(self, now=0):
        self.now = now

    def time(self):
        return self.now

    def advance(self, secs):
        self.now += secs
''',
        "cache.py": r'''
class TTLCache:
    def __init__(self, clock, ttl):
        self.clock, self.ttl = clock, ttl
        self._data = {}

    def get(self, key):
        item = self._data.get(key)
        if item is None:
            return None
        value, born = item
        if self.clock.time() - born >= self.ttl:
            del self._data[key]
            return None
        return value

    def set(self, key, value):
        self._data[key] = (value, self.clock.time())
''',
        "store.py": r'''
class ConfigStore:
    def __init__(self, values):
        self._values = dict(values)
        self.version = 0
        self.reads = 0

    def get(self, key):
        self.reads += 1
        return self._values[key]

    def set(self, key, value):
        self._values[key] = value
        self.version += 1
''',
        "resolver.py": r'''
class Resolver:
    """Reads settings through a TTL cache. Cache entries are keyed by (key, store.version)
    so that any write to the store makes older cached values unreachable."""

    def __init__(self, store, cache):
        self.store, self.cache = store, cache

    def get(self, key):
        ck = key
        hit = self.cache.get(ck)
        if hit is not None:
            return hit
        value = self.store.get(key)
        self.cache.set(ck, value)
        return value
''',
        "app.py": r'''
from resolver import Resolver


class Settings:
    def __init__(self, store, cache):
        self.store = store
        self._resolver = Resolver(store, cache)

    def read(self, key):
        return self._resolver.get(key)

    def update(self, key, value):
        self.store.set(key, value)
''',
    },
    fix=[("resolver.py", "        ck = key\n", "        ck = (key, self.store.version)\n")],
    test=r'''
from clock import FakeClock
from cache import TTLCache
from store import ConfigStore
from app import Settings

clock = FakeClock()
store = ConfigStore({"@k@": @v1@})
s = Settings(store, TTLCache(clock, ttl=@ttl@))
assert s.read("@k@") == @v1@
s.update("@k@", @v2@)
clock.advance(1)
assert s.read("@k@") == @v2@, s.read("@k@")
''',
    extra=r'''
reads = store.reads
s.read("@k@")
s.read("@k@")
assert store.reads == reads
c = TTLCache(clock, ttl=10)
c.set("a", 1)
clock.advance(9)
assert c.get("a") == 1
clock.advance(1)
assert c.get("a") is None
''',
    gt=dict(file="resolver.py", func="Resolver.get", cause="cache key ignores store.version, so a value cached before an update is still served until the TTL expires"),
    variants=[
        dict(k="limit", v1="5", v2="9", ttl="300"),
        dict(k="theme", v1='"light"', v2='"dark"', ttl="600"),
        dict(k="region", v1='"us-east"', v2='"eu-west"', ttl="60"),
        dict(k="batch", v1="100", v2="250", ttl="3600"),
    ])

# 23 ---------------------------------------------------------------- shared class attribute; looks order-dependent
fam(key="class_added", cat="mutated shared state", diff="hard", tags=["red_herring", "flaky_looking"],
    files={
        "node.py": r'''
class @N@:
    added = []

    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, child):
        self.children.append(child)
        self.added.append(child.name)
        return child
''',
        "tree.py": r'''
from node import @N@


def build(spec):
    """spec: (name, [child specs]) -> @N@ tree."""
    name, kids = spec
    root = @N@(name)
    for k in kids:
        root.add(build(k))
    return root
''',
        "visit.py": r'''
def walk(n, depth=0):
    yield depth, n
    for c in n.children:
        yield from walk(c, depth + 1)


def count(n):
    return sum(1 for _ in walk(n))


def height(n):
    return max(d for d, _ in walk(n))
''',
        "audit.py": r'''
def fanout(n):
    """How many children were added to this node."""
    return len(n.added)


def report(n):
    return f"{n.name}: {fanout(n)} children"
''',
        "render.py": r'''
from visit import walk


def render(n):
    return "\n".join("  " * d + x.name for d, x in walk(n))
''',
    },
    fix=[("node.py", "        self.children = []\n", "        self.children = []\n        self.added = []\n")],
    test=r'''
from tree import build
from visit import count, height
from audit import fanout


def test_first():
    t = build(@S1@)
    assert fanout(t) == @F1@
    assert count(t) == @F1@ + 1


def test_second():
    t = build(@S2@)
    assert count(t) == @F2@ + 1
    assert height(t) == 1
    assert fanout(t) == @F2@, fanout(t)


test_first()
test_second()
''',
    extra=r'''
from render import render
from audit import report
r = build(("r", [("a", []), ("b", [("c", [])])]))
assert render(r) == "r\n  a\n  b\n    c"
assert report(r) == "r: 2 children"
assert fanout(build(("solo", []))) == 0
''',
    gt=dict(file="node.py", func="@N@", cause="`added = []` is a class attribute shared by every @N@ instance, so child names recorded by earlier trees leak into later ones"),
    variants=[
        dict(N="Node", S1='("root", [("a", []), ("b", [])])', F1="2", S2='("x", [("y", []), ("z", []), ("w", [])])', F2="3"),
        dict(N="Folder", S1='("docs", [("a", []), ("b", []), ("c", [])])', F1="3", S2='("pics", [("p", [])])', F2="1"),
        dict(N="MenuItem", S1='("file", [("open", []), ("save", [])])', F1="2", S2='("edit", [("undo", []), ("redo", [])])', F2="2"),
        dict(N="Task", S1='("t1", [("t2", [])])', F1="1", S2='("u1", [("u2", []), ("u3", []), ("u4", []), ("u5", [])])', F2="4"),
    ])

# 24 ---------------------------------------------------------------- rounding: allocation loses the remainder
fam(key="alloc_remainder", cat="timezone/rounding", diff="hard", tags=["red_herring", "flaky_looking"],
    files={
        "alloc.py": r'''
def normalize(weights):
    total = sum(weights)
    return [w / total for w in weights]


def allocate(total_cents, weights):
    """Split total_cents proportionally to weights; the shares must add up to total_cents exactly
    (leftover cents go to the largest fractional remainders, ties to the lowest index)."""
    wsum = sum(weights)
    shares = [total_cents * w // wsum for w in weights]
    return shares
''',
        "ledger.py": r'''
from alloc import allocate
from checks import assert_balanced


class Ledger:
    def __init__(self):
        self.entries = []

    def post_split(self, total_cents, accounts, weights):
        shares = allocate(total_cents, weights)
        assert_balanced(total_cents, shares)
        for acct, amount in zip(accounts, shares):
            self.entries.append((acct, amount))
        return shares
''',
        "checks.py": r'''
class LedgerError(Exception):
    pass


def assert_balanced(total_cents, shares):
    if sum(shares) != total_cents:
        raise LedgerError(f"unbalanced split: {sum(shares)} != {total_cents}")
''',
        "gen.py": r'''
import random


def scenarios(seed, n):
    """Deterministic pseudo-random (total, weights) pairs."""
    rng = random.Random(seed)
    for _ in range(n):
        k = rng.randint(2, 5)
        yield rng.randint(1, 5000), [rng.randint(1, 9) for _ in range(k)]
''',
    },
    fix=[("alloc.py", "    return shares\n", """    leftover = total_cents - sum(shares)
    order = sorted(range(len(weights)), key=lambda i: (-(total_cents * weights[i] % wsum), i))
    for i in order[:leftover]:
        shares[i] += 1
    return shares
""")],
    test=r'''
from gen import scenarios
from ledger import Ledger

led = Ledger()
for total, weights in scenarios(@seed@, 40):
    accts = [f"a{i}" for i in range(len(weights))]
    shares = led.post_split(total, accts, weights)
    assert sum(shares) == total
''',
    extra=r'''
from alloc import allocate, normalize
assert allocate(100, [1, 1, 1]) == [34, 33, 33]
assert allocate(10, [1, 1]) == [5, 5]
assert allocate(1000, [1, 3]) == [250, 750]
assert allocate(0, [1, 2]) == [0, 0]
assert abs(sum(normalize([1, 2, 3])) - 1.0) < 1e-9
assert allocate(7, [1, 2, 4]) == [1, 2, 4]
''',
    gt=dict(file="alloc.py", func="allocate", cause="floor division of each share drops the leftover cents, so the split no longer adds up to the total"),
    variants=[dict(seed="7"), dict(seed="2024"), dict(seed="31337"), dict(seed="99")])

# 25 ---------------------------------------------------------------- mis-wired config: rate/burst swapped
fam(key="limiter_wiring", cat="mis-wired config", diff="hard", tags=["red_herring"],
    files={
        "clock.py": r'''
class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def time(self):
        return self.now

    def advance(self, secs):
        self.now += secs
''',
        "bucket.py": r'''
class TokenBucket:
    """Starts full (`burst` tokens); refills `rate` tokens per second up to `burst`."""

    def __init__(self, clock, rate, burst):
        self.clock, self.rate, self.burst = clock, rate, burst
        self.tokens = burst
        self.stamp = clock.time()

    def _refill(self):
        now = self.clock.time()
        self.tokens = min(self.burst, self.tokens + (now - self.stamp) * self.rate)
        self.stamp = now

    def allow(self):
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
''',
        "limits.py": r'''
LIMITS = {
    "@n1@": {"rate": @r1@, "burst": @b1@},
    "@n2@": {"rate": @r2@, "burst": @b2@},
}
''',
        "registry.py": r'''
from bucket import TokenBucket


def build_limiters(clock, limits):
    out = {}
    for name, cfg in limits.items():
        out[name] = TokenBucket(clock, cfg["burst"], cfg["rate"])
    return out
''',
        "middleware.py": r'''
class RateLimit:
    def __init__(self, limiters):
        self.limiters = limiters

    def check(self, name):
        return self.limiters[name].allow()
''',
    },
    fix=[("registry.py", 'TokenBucket(clock, cfg["burst"], cfg["rate"])', 'TokenBucket(clock, cfg["rate"], cfg["burst"])')],
    test=r'''
from clock import FakeClock
from limits import LIMITS
from registry import build_limiters
from middleware import RateLimit

clock = FakeClock()
mw = RateLimit(build_limiters(clock, LIMITS))
allowed = sum(mw.check("@n1@") for _ in range(@b1@ + 50))
assert allowed == @b1@, allowed
''',
    extra=r'''
clock.advance(1)
assert sum(mw.check("@n1@") for _ in range(@b1@ + 50)) == min(@r1@, @b1@)
assert sum(mw.check("@n2@") for _ in range(@b2@ + 50)) == @b2@
''',
    gt=dict(file="registry.py", func="build_limiters", cause="TokenBucket is built with rate and burst swapped (cfg['burst'] passed as rate)"),
    variants=[
        dict(n1="api", r1="5", b1="20", n2="login", r2="1", b2="3"),
        dict(n1="search", r1="2", b1="10", n2="export", r2="1", b2="2"),
        dict(n1="upload", r1="3", b1="12", n2="webhook", r2="2", b2="6"),
        dict(n1="chat", r1="4", b1="16", n2="invite", r2="1", b2="4"),
    ])

# 26 ---------------------------------------------------------------- off-by-one: chunk overlap tail
fam(key="chunk_tail", cat="off-by-one", diff="hard", tags=["red_herring"],
    files={
        "chunker.py": r'''
def chunk(items, size, overlap):
    """Windows of `size` items; consecutive windows share `overlap` items; the last window ends at the last item."""
    step = size - overlap
    out = []
    start = 0
    while start < len(items):
        out.append(items[start:start + size])
        if start + size > len(items):
            break
        start += step
    return out
''',
        "tokens.py": r'''
def split_words(text):
    return text.split()


def batches(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]
''',
        "checks.py": r'''
def check_chunks(chunks, overlap):
    for i, c in enumerate(chunks):
        if i > 0 and len(c) <= overlap:
            raise ValueError(f"chunk {i} has only {len(c)} item(s), nothing beyond the overlap")
''',
        "pipeline.py": r'''
from chunker import chunk
from checks import check_chunks
from tokens import split_words


def index_text(text, size, overlap):
    chunks = chunk(split_words(text), size, overlap)
    check_chunks(chunks, overlap)
    return chunks
''',
    },
    fix=[("chunker.py", "if start + size > len(items):", "if start + size >= len(items):")],
    test=r'''
from pipeline import index_text

N, SIZE, OV = @N@, @SIZE@, @OV@
text = " ".join(str(i) for i in range(N))
got = index_text(text, SIZE, OV)
exp = [[str(i) for i in range(a, b)] for a, b in @SPANS@]
assert got == exp, got
''',
    extra=r'''
from chunker import chunk
from tokens import batches
assert chunk(list(range(3)), 5, 1) == [[0, 1, 2]]
assert chunk([], 3, 1) == []
assert len(chunk(list(range(20)), 6, 2)) == 5
assert batches([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
''',
    gt=dict(file="chunker.py", func="chunk", cause="the stop test `start + size > len(items)` misses the case where a window ends exactly at the last item, producing an extra tail window"),
    variants=[
        dict(N="10", SIZE="4", OV="1", SPANS="[(0, 4), (3, 7), (6, 10)]"),
        dict(N="11", SIZE="5", OV="2", SPANS="[(0, 5), (3, 8), (6, 11)]"),
        dict(N="7", SIZE="3", OV="1", SPANS="[(0, 3), (2, 5), (4, 7)]"),
        dict(N="13", SIZE="7", OV="1", SPANS="[(0, 7), (6, 13)]"),
    ])

# 27 ---------------------------------------------------------------- None handling: falsy zero treated as missing
fam(key="falsy_zero", cat="wrong type/None handling", diff="hard", tags=["red_herring"],
    files={
        "parse.py": r'''
def to_number(raw):
    """float for numbers and numeric strings, None for None or blank strings."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    raw = raw.strip()
    if not raw:
        return None
    return float(raw)
''',
        "sources.py": r'''
FIELDS = ("@f1@", "@f2@")


def drop_blank(rows):
    """Remove rows where any numeric field is an empty string (zero is a legitimate value)."""
    return [r for r in rows if all(r.get(f) != "" for f in FIELDS)]
''',
        "normalize.py": r'''
from parse import to_number
from sources import FIELDS


def clean(record):
    out = dict(record)
    for f in FIELDS:
        v = record.get(f)
        out[f] = to_number(v) if v else None
    return out


def clean_all(rows):
    return [clean(r) for r in rows]
''',
        "aggregate.py": r'''
def totals(rows):
    return {
        "@f1@": sum(r["@f1@"] for r in rows),
        "@f2@": sum(r["@f2@"] for r in rows),
        "n": len(rows),
    }
''',
        "report.py": r'''
from sources import drop_blank
from normalize import clean_all
from aggregate import totals


def run(rows):
    return totals(clean_all(drop_blank(rows)))
''',
    },
    fix=[("normalize.py", "to_number(v) if v else None", "to_number(v)")],
    test=r'''
from report import run

rows = @ROWS@
assert run(rows) == @E@, run(rows)
''',
    extra=r'''
from parse import to_number
from sources import drop_blank
assert to_number("  ") is None and to_number(None) is None and to_number(0) == 0.0
assert len(drop_blank(rows + [{"@f1@": "", "@f2@": "1"}])) == len(rows)
assert run([]) == {"@f1@": 0, "@f2@": 0, "n": 0}
''',
    gt=dict(file="normalize.py", func="clean", cause="`if v` treats a legitimate numeric 0 as missing and replaces it with None, which later breaks the sum"),
    variants=[
        dict(f1="qty", f2="price", ROWS='[{"qty": 0, "price": "2.5"}, {"qty": "3", "price": 1}]', E='{"qty": 3.0, "price": 3.5, "n": 2}'),
        dict(f1="views", f2="clicks", ROWS='[{"views": 10, "clicks": 0}, {"views": "5", "clicks": "2"}, {"views": 0, "clicks": 1}]', E='{"views": 15.0, "clicks": 3.0, "n": 3}'),
        dict(f1="width", f2="height", ROWS='[{"width": "0", "height": 4}, {"width": 2.5, "height": 0}]', E='{"width": 2.5, "height": 4.0, "n": 2}'),
        dict(f1="debit", f2="credit", ROWS='[{"debit": 0, "credit": 0}, {"debit": 7, "credit": "1.5"}]', E='{"debit": 7.0, "credit": 1.5, "n": 2}'),
    ])

# 28 ---------------------------------------------------------------- exception handling: __exit__ swallows
fam(key="txn_swallow", cat="incorrect exception handling", diff="hard", tags=["red_herring"],
    files={
        "errors.py": r'''
class InsufficientFunds(Exception):
    pass
''',
        "store.py": r'''
class Store:
    def __init__(self, data):
        self.data = dict(data)
''',
        "bank.py": r'''
from errors import InsufficientFunds


class Bank:
    def __init__(self, store):
        self.store = store

    def withdraw(self, acct, amount):
        if self.store.data[acct] < amount:
            raise InsufficientFunds(acct)
        self.store.data[acct] -= amount

    def deposit(self, acct, amount):
        self.store.data[acct] += amount
''',
        "txn.py": r'''
class Transaction:
    """All-or-nothing block: on any exception the store is restored and the exception propagates."""

    def __init__(self, store):
        self.store = store
        self._snapshot = None

    def __enter__(self):
        self._snapshot = dict(self.store.data)
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.store.data = self._snapshot
        return True
''',
        "service.py": r'''
from txn import Transaction


def transfer(bank, src, dst, amount):
    with Transaction(bank.store):
        bank.withdraw(src, amount)
        bank.deposit(dst, amount)
        receipt = f"{src}->{dst}:{amount}"
    return receipt
''',
    },
    fix=[("txn.py", "        return True\n", "        return False\n")],
    test=r'''
from errors import InsufficientFunds
from store import Store
from bank import Bank
from service import transfer

bank = Bank(Store({"@a@": @ba@, "@b@": @bb@}))
try:
    transfer(bank, "@a@", "@b@", @big@)
    raise SystemExit("expected InsufficientFunds")
except InsufficientFunds:
    pass
assert bank.store.data == {"@a@": @ba@, "@b@": @bb@}
''',
    extra=r'''
assert transfer(bank, "@a@", "@b@", @small@) == "@a@->@b@:@small@"
assert bank.store.data == {"@a@": @ba@ - @small@, "@b@": @bb@ + @small@}
try:
    transfer(bank, "@a@", "ghost", 1)
    raise SystemExit("expected KeyError")
except KeyError:
    pass
assert bank.store.data == {"@a@": @ba@ - @small@, "@b@": @bb@ + @small@}
''',
    gt=dict(file="txn.py", func="Transaction.__exit__", cause="__exit__ returns True, which swallows every exception, so the with-block ends silently and the caller hits an unbound variable"),
    variants=[
        dict(a="alice", b="bob", ba="100", bb="20", big="500", small="30"),
        dict(a="acc1", b="acc2", ba="50", bb="0", big="51", small="40"),
        dict(a="savings", b="checking", ba="1000", bb="250", big="2000", small="100"),
        dict(a="x", b="y", ba="9", bb="9", big="10", small="4"),
    ])

# 29 ---------------------------------------------------------------- aliasing: history stores references (no_collateral)
fam(key="undo_alias", cat="aliasing", diff="hard", tags=["no_collateral", "red_herring"],
    files={
        "history.py": r'''
class History:
    """Undo stack of document snapshots. push() stores a snapshot, pop() returns the latest one."""

    def __init__(self):
        self._stack = []

    def push(self, state):
        self._stack.append(state)

    def pop(self):
        if not self._stack:
            raise IndexError("nothing to undo")
        return self._stack.pop()

    def __len__(self):
        return len(self._stack)
''',
        "document.py": r'''
from history import History


class Document:
    def __init__(self):
        self.state = {"text": "", "tags": []}
        self.history = History()

    def checkpoint(self):
        self.history.push(self.state)

    def undo(self):
        self.state = self.history.pop()

    def text(self):
        return self.state["text"]
''',
        "commands.py": r'''
def type_text(doc, s):
    doc.state["text"] += s


def add_tag(doc, tag):
    doc.state["tags"].append(tag)
''',
        "render.py": r'''
def summary(doc):
    tags = ",".join(doc.state["tags"]) or "-"
    return f"{len(doc.text())} chars [{tags}]"
''',
    },
    fix=[("history.py", "        self._stack.append(state)\n", "        self._stack.append(copy.deepcopy(state))\n"),
         ("history.py", 'class History:', 'import copy\n\n\nclass History:')],
    bad=[("history.py", "        self._stack.append(state)\n", "        self._stack.append(copy.deepcopy(state))\n        self._stack = self._stack[-3:]\n"),
         ("history.py", 'class History:', 'import copy\n\n\nclass History:')],
    test=r'''
from document import Document
from commands import type_text, add_tag

d = Document()
type_text(d, "@t1@")
d.checkpoint()
type_text(d, "@t2@")
d.checkpoint()
add_tag(d, "@tag@")
d.undo()
assert d.text() == "@t1@@t2@", d.text()
d.undo()
assert d.text() == "@t1@", d.text()
''',
    extra=r'''
from render import summary
assert d.state["tags"] == []
assert summary(d) == "%d chars [-]" % len("@t1@")
e = Document()
for i in range(6):
    type_text(e, str(i))
    e.checkpoint()
for i in range(5, -1, -1):
    e.undo()
    assert e.text() == "".join(str(j) for j in range(i + 1)), (i, e.text())
try:
    e.undo()
    raise SystemExit("expected IndexError")
except IndexError:
    pass
''',
    gt=dict(file="history.py", func="History.push", cause="push() stores the live state object instead of a snapshot, so later edits rewrite every checkpoint (aliasing)"),
    variants=[
        dict(t1="hello", t2=" world", tag="draft"),
        dict(t1="def f():", t2=" pass", tag="code"),
        dict(t1="Dear all,", t2=" thanks", tag="mail"),
        dict(t1="1", t2="2", tag="n"),
    ])

# 30 ---------------------------------------------------------------- encoding: NFC vs NFD keys
fam(key="nfc_keys", cat="encoding", diff="hard", tags=["red_herring"],
    files={
        "normalize.py": r'''
import unicodedata


def collapse_spaces(s):
    return " ".join(s.split())


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def fold(s):
    """Canonical lookup key: NFC-normalised, casefolded, whitespace collapsed."""
    return collapse_spaces(s.casefold())
''',
        "index.py": r'''
from normalize import fold


def build(names):
    idx = {}
    for n in names:
        idx.setdefault(fold(n), []).append(n)
    return idx
''',
        "search.py": r'''
from normalize import fold


def lookup(idx, query):
    return idx[fold(query)]
''',
        "loader.py": r'''
def load_names(raw_bytes):
    return [line for line in raw_bytes.decode("utf-8").splitlines() if line.strip()]
''',
        "ranking.py": r'''
from normalize import strip_accents


def sort_key(name):
    return strip_accents(name).lower()
''',
    },
    fix=[("normalize.py", "return collapse_spaces(s.casefold())", 'return collapse_spaces(unicodedata.normalize("NFC", s).casefold())')],
    test=r'''
from loader import load_names
from index import build
from search import lookup

raw = "@D@\nOther Place\n".encode("utf-8")
idx = build(load_names(raw))
assert lookup(idx, "@C@") == ["@D@"]
''',
    extra=r'''
from ranking import sort_key
from normalize import fold, strip_accents
assert lookup(idx, "  other   PLACE ") == ["Other Place"]
assert fold("@C@") == fold("@D@")
assert strip_accents("@C@") == "@PLAIN@"
assert sorted(["b", "@C@", "a"], key=sort_key)[1] in ("@C@", "b")
''',
    gt=dict(file="normalize.py", func="fold", cause="fold() casefolds without Unicode normalisation, so the composed and decomposed forms of the same accented text produce different keys"),
    variants=[
        dict(D="Café Noir", C="Café Noir", PLAIN="Cafe Noir"),
        dict(D="Zürich Altstadt", C="Zürich Altstadt", PLAIN="Zurich Altstadt"),
        dict(D="Niño Perdido", C="Niño Perdido", PLAIN="Nino Perdido"),
        dict(D="Amélie Poulain", C="Amélie Poulain", PLAIN="Amelie Poulain"),
    ])

# 31 ---------------------------------------------------------------- ordering: lexicographic version sort
fam(key="version_sort", cat="incorrect ordering", diff="hard", tags=["red_herring", "flaky_looking"],
    files={
        "version.py": r'''
def parse_version(v):
    """'1.10.2' -> (1, 10, 2)"""
    return tuple(int(p) for p in v.split("."))


def is_newer(a, b):
    return parse_version(a) > parse_version(b)
''',
        "releases.py": r'''
from version import parse_version


def sorted_versions(versions):
    """Versions in ascending numeric order."""
    return sorted(versions)


def newest_in_series(versions, major):
    return [v for v in sorted_versions(versions) if parse_version(v)[0] == major][-1]
''',
        "deps.py": r'''
from releases import sorted_versions


def resolve(available, allowed):
    """Newest available version contained in `allowed`."""
    for v in reversed(sorted_versions(available)):
        if v in allowed:
            return v
    raise LookupError("no compatible version")
''',
        "changelog.py": r'''
from version import is_newer


def since(entries, base):
    return [e for e in entries if is_newer(e["v"], base)]
''',
        "main.py": r'''
from deps import resolve


def pick(available, allowed):
    return resolve(available, set(allowed))
''',
    },
    fix=[("releases.py", "    return sorted(versions)\n", "    return sorted(versions, key=parse_version)\n")],
    test=r'''
from main import pick

avail = @AV@
assert pick(avail, avail) == "@TOP@", pick(avail, avail)
''',
    extra=r'''
from releases import sorted_versions, newest_in_series
from changelog import since
assert sorted_versions(["1.2.0", "1.10.0", "1.9.1"]) == ["1.2.0", "1.9.1", "1.10.0"]
assert newest_in_series(avail, @MAJ@) == "@NS@"
assert [e["v"] for e in since([{"v": "1.9.0"}, {"v": "1.10.0"}], "1.9.5")] == ["1.10.0"]
assert pick(["1.0.0"], ["1.0.0"]) == "1.0.0"
''',
    gt=dict(file="releases.py", func="sorted_versions", cause="versions are sorted as plain strings, so '1.10.0' sorts before '1.9.0'; they must be compared as integer tuples"),
    variants=[
        dict(AV='["1.2.0", "1.9.0", "1.10.0", "1.3.4"]', TOP="1.10.0", MAJ="1", NS="1.10.0"),
        dict(AV='["2.0.9", "2.0.10", "2.0.1"]', TOP="2.0.10", MAJ="2", NS="2.0.10"),
        dict(AV='["0.9.0", "0.10.0", "0.8.7"]', TOP="0.10.0", MAJ="0", NS="0.10.0"),
        dict(AV='["3.11.0", "3.2.0", "3.9.5", "10.0.0"]', TOP="10.0.0", MAJ="3", NS="3.11.0"),
    ])
