"""Medium families."""
from fam_a import fam

# 9 ---------------------------------------------------------------- off-by-one: window; traceback in report.py
fam(key="moving_avg", cat="off-by-one", diff="medium", tags=["red_herring"],
    files={
        "stats.py": r'''
def moving_average(values, window):
    """Average of every run of `window` consecutive values."""
    out = []
    for i in range(len(values) - window):
        out.append(sum(values[i:i + window]) / window)
    return out


def chunks(values, size):
    """Non-overlapping chunks; the last one may be shorter."""
    return [values[i:i + size] for i in range(0, len(values), size)]
''',
        "report.py": r'''
from stats import moving_average


def smooth_peak(series, window):
    return max(moving_average(series, window))


def smooth_range(series, window):
    avg = moving_average(series, window)
    return min(avg), max(avg)
''',
        "@mod@.py": r'''
from report import smooth_peak
from stats import chunks


def @fn@(@vals@, window=@w@):
    return {"peak": smooth_peak(@vals@, window), "blocks": len(chunks(@vals@, window))}
''',
    },
    fix=[("stats.py", "for i in range(len(values) - window):", "for i in range(len(values) - window + 1):")],
    test=r'''
from report import smooth_peak
from @mod@ import @fn@

V = @V@
assert smooth_peak(V, len(V)) == sum(V) / len(V)
''',
    extra=r'''
from stats import moving_average, chunks
from report import smooth_range
w = @w@
exp = [sum(V[i:i + w]) / w for i in range(len(V) - w + 1)]
assert moving_average(V, w) == exp
assert smooth_range(V, w) == (min(exp), max(exp))
assert chunks(V, w)[-1] == V[(len(V) - 1) // w * w:]
assert @fn@(V)["blocks"] == (len(V) + w - 1) // w
''',
    gt=dict(file="stats.py", func="moving_average", cause="range(len(values) - window) stops one window early, dropping the final window"),
    variants=[
        dict(mod="sensors", fn="summarize_temps", vals="temps", w="3", V="[4, 6, 8, 5, 9, 7]"),
        dict(mod="traffic", fn="summarize_hits", vals="hits", w="2", V="[10, 20, 15, 40, 35]"),
        dict(mod="latency", fn="summarize_ms", vals="samples", w="4", V="[1.5, 2.5, 2.0, 3.0, 8.0, 2.0, 2.5]"),
        dict(mod="sales", fn="summarize_week", vals="daily", w="7", V="[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]"),
    ])

# 10 ---------------------------------------------------------------- wrong type: qty parsed as str
fam(key="csv_qty_str", cat="wrong type/None handling", diff="medium", tags=["red_herring"],
    files={
        "ingest.py": r'''
def parse_row(line):
    name, qty, price = line.split(",")
    return {"name": name.strip(), "qty": qty.strip(), "price": float(price)}


def parse_lines(text):
    return [parse_row(l) for l in text.strip().splitlines() if l.strip()]
''',
        "filters.py": r'''
def bulk(rows, threshold):
    """Rows whose quantity is at least `threshold`."""
    return [r for r in rows if r["qty"] >= threshold]
''',
        "summary.py": r'''
def total_value(rows):
    return sum(r["qty"] * r["price"] for r in rows)
''',
    },
    fix=[("ingest.py", '"qty": qty.strip(),', '"qty": int(qty),')],
    test=r'''
from ingest import parse_lines
from filters import bulk

rows = parse_lines("""@LINES@""")
assert [r["name"] for r in bulk(rows, @T@)] == @E@
''',
    extra=r'''
from summary import total_value
assert round(total_value(rows), 2) == @TV@
assert rows[0]["price"] == @P0@
''',
    gt=dict(file="ingest.py", func="parse_row", cause="qty stays a string, so later numeric comparison and multiplication break; it must be converted to int"),
    variants=[
        dict(LINES="bolt, 120, 0.10\nnut, 8, 0.05\nwasher, 45, 0.02", T="10", E='["bolt", "washer"]', TV="13.3", P0="0.1"),
        dict(LINES="cpu, 2, 150.0\nram, 16, 3.5\ndisk, 4, 40.0", T="3", E='["ram", "disk"]', TV="516.0", P0="150.0"),
        dict(LINES="mug, 30, 2.5\ncup, 5, 1.0\nbowl, 12, 3.0", T="10", E='["mug", "bowl"]', TV="116.0", P0="2.5"),
        dict(LINES="wire, 100, 0.25\nclip, 1000, 0.01\nstaple, 50, 0.04", T="100", E='["wire", "clip"]', TV="37.0", P0="0.25"),
    ])

# 11 ---------------------------------------------------------------- mutated shared state: sort in place (no_collateral)
fam(key="median_inplace", cat="mutated shared state", diff="medium", tags=["no_collateral", "red_herring"],
    files={
        "stats.py": r'''
def median(values):
    values.sort()
    n = len(values)
    mid = n // 2
    if n % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2


def mean(values):
    return sum(values) / len(values)
''',
        "summary.py": r'''
from stats import median, mean


def summarize(series):
    return {"first": series[0], "median": median(series), "mean": mean(series), "last": series[-1]}
''',
    },
    fix=[("stats.py", "    values.sort()\n", "    values = sorted(values)\n")],
    bad=[("stats.py", "    values.sort()\n", "    values = sorted(values)\n"),
         ("stats.py", "    n = len(values)\n", "    n = len(values)\n    if not n:\n        return 0.0\n")],
    test=r'''
from summary import summarize

assert summarize(@S@) == @E@
''',
    extra=r'''
from stats import median, mean
assert median([1, 2, 3, 4]) == 2.5
assert median([7]) == 7
x = [3, 1, 2]
assert median(x) == 2 and x == [3, 1, 2]
assert mean([2, 4]) == 3
try:
    median([])
    raise SystemExit("median of an empty list must raise IndexError")
except IndexError:
    pass
''',
    gt=dict(file="stats.py", func="median", cause="values.sort() sorts the caller's list in place, so the series is reordered after median() is called"),
    variants=[
        dict(S="[5, 3, 9, 1, 7]", E='{"first": 5, "median": 5, "mean": 5.0, "last": 7}'),
        dict(S="[8, 2, 6, 4]", E='{"first": 8, "median": 5.0, "mean": 5.0, "last": 4}'),
        dict(S="[10, 30, 20]", E='{"first": 10, "median": 20, "mean": 20.0, "last": 20}'),
        dict(S="[2.5, 0.5, 4.0, 1.0, 3.0]", E='{"first": 2.5, "median": 2.5, "mean": 2.2, "last": 3.0}'),
    ])

# 12 ---------------------------------------------------------------- stale cache: put does not invalidate
fam(key="cache_put", cat="stale cache", diff="medium", tags=["red_herring"],
    files={
        "repo.py": r'''
class Repo:
    def __init__(self):
        self._rows = {}
        self.reads = 0

    def put(self, key, value):
        self._rows[key] = value

    def get(self, key):
        self.reads += 1
        return self._rows.get(key)

    def delete(self, key):
        self._rows.pop(key, None)
''',
        "cache.py": r'''
class CachedRepo:
    def __init__(self, repo):
        self.repo = repo
        self._cache = {}

    def get(self, key):
        if key not in self._cache:
            self._cache[key] = self.repo.get(key)
        return self._cache[key]

    def put(self, key, value):
        self.repo.put(key, value)

    def delete(self, key):
        self.repo.delete(key)
        self._cache.pop(key, None)
''',
        "service.py": r'''
def rename(store, @id@, name):
    rec = dict(store.get(@id@) or {})
    rec["name"] = name
    store.put(@id@, rec)


def label(store, @id@):
    rec = store.get(@id@)
    return rec["name"] if rec else "?"
''',
    },
    fix=[("cache.py", "        self.repo.put(key, value)\n", "        self.repo.put(key, value)\n        self._cache.pop(key, None)\n")],
    test=r'''
from repo import Repo
from cache import CachedRepo
from service import rename, label

s = CachedRepo(Repo())
s.put(@K@, {"name": "@a@"})
assert label(s, @K@) == "@a@"
rename(s, @K@, "@b@")
assert label(s, @K@) == "@b@", label(s, @K@)
''',
    extra=r'''
before = s.repo.reads
label(s, @K@)
label(s, @K@)
assert s.repo.reads == before
s.delete(@K@)
assert label(s, @K@) == "?"
''',
    gt=dict(file="cache.py", func="CachedRepo.put", cause="put writes through to the repo but leaves the old value in the read cache, so later reads are stale"),
    variants=[
        dict(id="uid", K="1", a="Ada", b="Ada L."),
        dict(id="team_id", K='"t-7"', a="Blue", b="Navy"),
        dict(id="sku", K='"sku9"', a="Mug", b="Large Mug"),
        dict(id="pid", K="42", a="draft", b="final"),
    ])

# 13 ---------------------------------------------------------------- rounding: banker's rounding on halves
fam(key="tax_half_even", cat="timezone/rounding", diff="medium", tags=["red_herring"],
    files={
        "tax.py": r'''
def tax_cents(amount_cents, rate_bp):
    """Tax on an amount in whole cents, halves rounded up. rate_bp is basis points (500 = 5%)."""
    return round(amount_cents * rate_bp / 10000)


def split_even(total_cents, parts):
    base, extra = divmod(total_cents, parts)
    return [base + 1 if i < extra else base for i in range(parts)]
''',
        "invoice.py": r'''
from tax import tax_cents


def invoice_total(lines, rate_bp):
    """lines: (quantity, unit_price_cents) pairs."""
    subtotal = sum(q * p for q, p in lines)
    return subtotal + tax_cents(subtotal, rate_bp)
''',
    },
    fix=[("tax.py", "return round(amount_cents * rate_bp / 10000)", "return (amount_cents * rate_bp + 5000) // 10000")],
    test=r'''
from invoice import invoice_total

lines = @L@
sub = sum(q * p for q, p in lines)
assert invoice_total(lines, @BP@) == sub + (sub * @BP@ + 5000) // 10000, invoice_total(lines, @BP@)
''',
    extra=r'''
from tax import tax_cents, split_even
assert tax_cents(1000, 500) == 50
assert tax_cents(0, 500) == 0
assert sum(split_even(1001, 3)) == 1001 and split_even(10, 4) == [3, 3, 2, 2]
''',
    gt=dict(file="tax.py", func="tax_cents", cause="built-in round() rounds exact halves to the even integer, not up, so x.5 cents round down half the time"),
    variants=[
        dict(L="[(1, 250)]", BP="500"),
        dict(L="[(2, 100), (1, 90)]", BP="500"),
        dict(L="[(5, 10)]", BP="500"),
        dict(L="[(2, 200), (3, 60)]", BP="250"),
    ])

# 14 ---------------------------------------------------------------- timezone: sign of offset
fam(key="tz_sign", cat="timezone/rounding", diff="medium", tags=["red_herring"],
    files={
        "tzutil.py": r'''
from datetime import timedelta


def to_local(ts, offset_minutes):
    """Convert a naive UTC datetime to local wall time at a fixed UTC offset (minutes east of UTC)."""
    return ts - timedelta(minutes=offset_minutes)


def fmt_offset(offset_minutes):
    sign = "+" if offset_minutes >= 0 else "-"
    m = abs(offset_minutes)
    return f"{sign}{m // 60:02d}:{m % 60:02d}"
''',
        "bucket.py": r'''
from tzutil import to_local


def day_of(ts, offset_minutes):
    return to_local(ts, offset_minutes).date()


def count_by_day(timestamps, offset_minutes):
    out = {}
    for ts in timestamps:
        d = day_of(ts, offset_minutes).isoformat()
        out[d] = out.get(d, 0) + 1
    return out
''',
        "report.py": r'''
from bucket import count_by_day
from tzutil import fmt_offset


def daily_report(timestamps, offset_minutes):
    counts = count_by_day(timestamps, offset_minutes)
    return [f"{day} ({fmt_offset(offset_minutes)}): {n}" for day, n in sorted(counts.items())]
''',
    },
    fix=[("tzutil.py", "return ts - timedelta(minutes=offset_minutes)", "return ts + timedelta(minutes=offset_minutes)")],
    test=r'''
from datetime import datetime
from bucket import count_by_day

ts = [datetime(@T1@), datetime(@T2@), datetime(@T3@)]
assert count_by_day(ts, @OFF@) == @E@, count_by_day(ts, @OFF@)
''',
    extra=r'''
from tzutil import fmt_offset
from report import daily_report
assert fmt_offset(330) == "+05:30" and fmt_offset(-300) == "-05:00" and fmt_offset(0) == "+00:00"
assert len(daily_report(ts, @OFF@)) == len(@E@)
''',
    gt=dict(file="tzutil.py", func="to_local", cause="the offset is subtracted instead of added, so local time is computed on the wrong side of UTC"),
    variants=[
        dict(T1="2026, 3, 1, 20, 0", T2="2026, 3, 1, 2, 0", T3="2026, 3, 1, 19, 0", OFF="330", E='{"2026-03-02": 2, "2026-03-01": 1}'),
        dict(T1="2026, 3, 1, 2, 0", T2="2026, 3, 1, 12, 0", T3="2026, 3, 1, 4, 30", OFF="-300", E='{"2026-02-28": 2, "2026-03-01": 1}'),
        dict(T1="2026, 3, 1, 14, 59", T2="2026, 3, 1, 15, 0", T3="2026, 2, 28, 16, 0", OFF="540", E='{"2026-03-01": 2, "2026-03-02": 1}'),
        dict(T1="2026, 3, 1, 7, 59", T2="2026, 3, 1, 8, 0", T3="2026, 3, 2, 7, 59", OFF="-480", E='{"2026-02-28": 1, "2026-03-01": 2}'),
    ])

# 15 ---------------------------------------------------------------- encoding: latin-1 encode / utf-8 decode
fam(key="codec_latin1", cat="encoding", diff="medium", tags=["red_herring"],
    files={
        "codec.py": r'''
def encode(text):
    return text.encode("latin-1", errors="replace")


def decode(data):
    return data.decode("utf-8")


def truncate_bytes(text, limit):
    """Longest prefix of text that fits in `limit` UTF-8 bytes."""
    data = text.encode("utf-8")[:limit]
    return data.decode("utf-8", errors="ignore")
''',
        "message.py": r'''
from codec import encode, decode


def pack(text):
    body = encode(text)
    return len(body).to_bytes(2, "big") + body


def unpack(blob):
    n = int.from_bytes(blob[:2], "big")
    return decode(blob[2:2 + n])
''',
    },
    fix=[("codec.py", 'return text.encode("latin-1", errors="replace")', 'return text.encode("utf-8")')],
    test=r'''
from message import pack, unpack

T = "@T@"
assert unpack(pack(T)) == T
''',
    extra=r'''
from codec import truncate_bytes
assert len(pack(T)) == 2 + len(T.encode("utf-8"))
assert truncate_bytes(T, 3) == T.encode("utf-8")[:3].decode("utf-8", errors="ignore")
assert truncate_bytes("héllo", 2) == "h"
assert unpack(pack("plain")) == "plain"
''',
    gt=dict(file="codec.py", func="encode", cause="encode() uses latin-1 with replace but decode() reads UTF-8, so non-ASCII text is corrupted or fails to decode"),
    variants=[
        dict(T="café au lait"),
        dict(T="naïve façade"),
        dict(T="日本語のテキスト"),
        dict(T="Zoë ☕ and Ångström"),
    ])

# 16 ---------------------------------------------------------------- mis-wired config
fam(key="wired_pool", cat="mis-wired config", diff="medium", tags=["red_herring"],
    files={
        "config.py": r'''
CONFIG = {
    "@s1@": {"host": "@s1@.internal", "size": @P1@},
    "@s2@": {"host": "@s2@.internal", "size": @P2@},
}
''',
        "pools.py": r'''
class Pool:
    def __init__(self, name, host, size, limit):
        if size > limit:
            raise ValueError(f"{name} pool size {size} exceeds limit {limit}")
        self.name, self.host, self.size = name, host, size
''',
        "app.py": r'''
from config import CONFIG
from pools import Pool


class App:
    pass


def build(cfg=CONFIG):
    app = App()
    app.@s1@ = Pool("@s1@", cfg["@s1@"]["host"], cfg["@s1@"]["size"], @L1@)
    app.@s2@ = Pool("@s2@", cfg["@s2@"]["host"], cfg["@s1@"]["size"], @L2@)
    return app
''',
    },
    fix=[("app.py", 'cfg["@s2@"]["host"], cfg["@s1@"]["size"]', 'cfg["@s2@"]["host"], cfg["@s2@"]["size"]')],
    test=r'''
from app import build
from config import CONFIG

app = build(CONFIG)
assert app.@s2@.size == @P2@
assert app.@s2@.host == "@s2@.internal"
''',
    extra=r'''
assert app.@s1@.size == @P1@ and app.@s1@.host == "@s1@.internal"
try:
    build({"@s1@": {"host": "h", "size": @L1@ + 1}, "@s2@": {"host": "h", "size": 1}})
    raise SystemExit("oversized pool must be rejected")
except ValueError:
    pass
''',
    gt=dict(file="app.py", func="build", cause="the @s2@ pool is wired to the @s1@ section's size setting instead of its own"),
    variants=[
        dict(s1="db", s2="cache", P1="20", P2="4", L1="32", L2="8"),
        dict(s1="primary", s2="replica", P1="50", P2="10", L1="64", L2="16"),
        dict(s1="web", s2="worker", P1="12", P2="3", L1="16", L2="4"),
        dict(s1="orders", s2="audit", P1="30", P2="2", L1="40", L2="5"),
    ])

# 17 ---------------------------------------------------------------- wrong unit: percent vs fraction (minimal diff)
fam(key="tax_percent", cat="wrong unit", diff="medium", tags=["red_herring", "minimal_diff"],
    files={
        "settings.py": r'''
# All rates in this file are PERCENT values (8 means 8%).
TAX_PERCENT = @pct@
''',
        "checkout.py": r'''
from settings import TAX_PERCENT


def apply_discount(amount, percent):
    return amount * (1 - percent / 100)


def total(subtotal, discount_percent=0):
    discounted = apply_discount(subtotal, discount_percent)
    return round(discounted * (1 + TAX_PERCENT), 2)
''',
        "cart.py": r'''
from checkout import total


def cart_total(prices, discount_percent=0):
    return total(sum(prices), discount_percent)
''',
    },
    fix=[("checkout.py", "(1 + TAX_PERCENT)", "(1 + TAX_PERCENT / 100)")],
    test=r'''
from cart import cart_total

assert cart_total([@S@]) == @E@, cart_total([@S@])
''',
    extra=r'''
from checkout import apply_discount
assert cart_total([@S@], @D@) == @E2@
assert apply_discount(200, 25) == 150.0
assert cart_total([]) == 0.0
''',
    gt=dict(file="checkout.py", func="total", cause="TAX_PERCENT is a percent (@pct@) but total() uses it as a fraction, inflating the tax by 100x"),
    variants=[
        dict(pct="8", S="100", E="108.0", D="10", E2="97.2"),
        dict(pct="10", S="250", E="275.0", D="20", E2="220.0"),
        dict(pct="12.5", S="80", E="90.0", D="50", E2="45.0"),
        dict(pct="5", S="40", E="42.0", D="25", E2="31.5"),
    ])

# 18 ---------------------------------------------------------------- exception handling: Fatal retried
fam(key="retry_fatal", cat="incorrect exception handling", diff="medium", tags=["red_herring"],
    files={
        "errors.py": r'''
class Retryable(Exception):
    pass


class Fatal(Exception):
    pass
''',
        "runner.py": r'''
from errors import Retryable, Fatal


def run_with_retry(op, attempts=@att@):
    """Retry on Retryable only; Fatal must propagate immediately."""
    last = None
    for _ in range(attempts):
        try:
            return op()
        except (Retryable, Fatal) as exc:
            last = exc
    raise last
''',
        "jobs.py": r'''
from runner import run_with_retry


def run_job(name, op, log):
    try:
        return run_with_retry(op)
    except Exception as exc:
        log.append(f"{name}: {type(exc).__name__}")
        raise
''',
    },
    fix=[("runner.py", "except (Retryable, Fatal) as exc:", "except Retryable as exc:")],
    test=r'''
from errors import Fatal, Retryable
from jobs import run_job

calls = {"n": 0}
log = []


def bad():
    calls["n"] += 1
    raise Fatal("@why@")


try:
    run_job("@job@", bad, log)
    raise SystemExit("Fatal must propagate")
except Fatal:
    pass
assert calls["n"] == 1, calls
''',
    extra=r'''
assert log == ["@job@: Fatal"]
calls["n"] = 0


def flaky():
    calls["n"] += 1
    if calls["n"] < @att@:
        raise Retryable("again")
    return "done"


assert run_job("@job@", flaky, []) == "done" and calls["n"] == @att@
calls["n"] = 0


def always():
    calls["n"] += 1
    raise Retryable("never")


try:
    run_job("@job@", always, [])
    raise SystemExit("must raise after attempts")
except Retryable:
    pass
assert calls["n"] == @att@
''',
    gt=dict(file="runner.py", func="run_with_retry", cause="Fatal is caught together with Retryable, so a non-retryable failure is retried instead of propagating immediately"),
    variants=[
        dict(att="3", why="bad credentials", job="sync"),
        dict(att="4", why="schema mismatch", job="import"),
        dict(att="2", why="disk full", job="backup"),
        dict(att="5", why="license expired", job="render"),
    ])

# 19 ---------------------------------------------------------------- aliasing: shallow copy (no_collateral)
fam(key="shallow_cfg", cat="aliasing", diff="medium", tags=["no_collateral", "red_herring"],
    files={
        "settings.py": r'''
BASE = {"db": {"host": "localhost", "port": @bp@}, "cache": {"ttl": 60}, "debug": False}


def derive(overrides):
    """New config: BASE with `overrides` merged one level deep (per section)."""
    cfg = BASE.copy()
    for section, values in overrides.items():
        if isinstance(values, dict):
            cfg.setdefault(section, {}).update(values)
        else:
            cfg[section] = values
    return cfg
''',
        "env.py": r'''
from settings import derive

PROFILES = {
    "dev": {"db": {"host": "@h@"}, "debug": True},
    "prod": {"db": {"port": @p@}},
}


def for_env(name):
    return derive(PROFILES[name])
''',
    },
    fix=[("settings.py", "cfg = BASE.copy()", "cfg = copy.deepcopy(BASE)"), ("settings.py", "BASE = {", "import copy\n\nBASE = {")],
    bad=[("settings.py", "cfg = BASE.copy()", "cfg = copy.deepcopy(BASE)"), ("settings.py", "BASE = {", "import copy\n\nBASE = {"),
         ("settings.py", "            cfg[section] = values", "            continue")],
    test=r'''
import settings
from env import for_env

dev = for_env("dev")
prod = for_env("prod")
assert prod["db"] == {"host": "localhost", "port": @p@}, prod["db"]
assert settings.BASE["db"] == {"host": "localhost", "port": @bp@}
''',
    extra=r'''
from settings import derive
assert dev["db"] == {"host": "@h@", "port": @bp@} and dev["debug"] is True
assert derive({}) == settings.BASE
assert derive({"db": {"port": 1}})["db"] == {"host": "localhost", "port": 1}
assert derive({"queue": {"n": 1}})["queue"] == {"n": 1}
assert derive({"debug": True})["debug"] is True and settings.BASE["debug"] is False
''',
    gt=dict(file="settings.py", func="derive", cause="BASE.copy() is a shallow copy, so merging into a nested section mutates the shared BASE dict"),
    variants=[
        dict(bp="5432", h="dev.local", p="6432"),
        dict(bp="3306", h="127.0.0.9", p="3307"),
        dict(bp="1521", h="sandbox", p="1522"),
        dict(bp="27017", h="mongo-dev", p="27018"),
    ])

# 20 ---------------------------------------------------------------- ordering: pipeline steps (no_collateral)
fam(key="step_order", cat="incorrect ordering", diff="medium", tags=["no_collateral", "red_herring"],
    files={
        "steps.py": r'''
COUPON = @F@
TAX_PERCENT = @T@
SHIPPING = @H@


def apply_discount(cents):
    return max(cents - COUPON, 0)


def apply_tax(cents):
    return cents * (100 + TAX_PERCENT) // 100


def apply_shipping(cents):
    return cents + SHIPPING
''',
        "pipeline.py": r'''
def run(cents, steps):
    for step in steps:
        cents = step(cents)
    return cents
''',
        "checkout.py": r'''
from steps import apply_discount, apply_tax, apply_shipping
from pipeline import run

ORDER = [apply_tax, apply_discount, apply_shipping]


def total(cents):
    """Coupon first, then tax on the discounted amount, shipping is added last and untaxed."""
    return run(cents, ORDER)
''',
    },
    fix=[("checkout.py", "ORDER = [apply_tax, apply_discount, apply_shipping]", "ORDER = [apply_discount, apply_tax, apply_shipping]")],
    bad=[("checkout.py", "ORDER = [apply_tax, apply_discount, apply_shipping]", "ORDER = [apply_discount, apply_tax, apply_shipping]"),
         ("steps.py", "return cents * (100 + TAX_PERCENT) // 100", "return (cents * (100 + TAX_PERCENT) + 50) // 100")],
    test=r'''
from checkout import total

S = @S@
assert total(S) == (S - @F@) * (100 + @T@) // 100 + @H@, total(S)
''',
    extra=r'''
from steps import apply_tax, apply_discount, apply_shipping
from pipeline import run
assert apply_tax(1010) == 1010 * (100 + @T@) // 100
assert run(100, [apply_shipping, apply_tax]) == (100 + @H@) * (100 + @T@) // 100
assert apply_discount(@F@ - 1) == 0 and total(@F@ - 1) == @H@
assert run(5, []) == 5
''',
    gt=dict(file="checkout.py", func="ORDER", cause="the pipeline order applies tax before the flat coupon, so the coupon is taxed away; discount must come first"),
    variants=[
        dict(S="10000", F="1000", T="8", H="500"),
        dict(S="25000", F="2000", T="6", H="700"),
        dict(S="8000", F="500", T="7", H="300"),
        dict(S="12000", F="1500", T="9", H="400"),
    ])

# 21 ---------------------------------------------------------------- wrong default (minimal diff)
fam(key="min_score_default", cat="wrong default", diff="medium", tags=["red_herring", "minimal_diff"],
    files={
        "scoring.py": r'''
DEFAULT_LIMIT = 10


def keep(rows, min_score=@bad@):
    """Rows scoring at least min_score. By default every row is kept (min_score 0)."""
    return [r for r in rows if r["score"] >= min_score]


def best(rows, n=3):
    return sorted(rows, key=lambda r: -r["score"])[:n]
''',
        "api.py": r'''
from scoring import keep, best, DEFAULT_LIMIT


def list_results(rows, min_score=None, limit=DEFAULT_LIMIT):
    kept = keep(rows) if min_score is None else keep(rows, min_score)
    return kept[:limit]


def podium(rows):
    return [r["id"] for r in best(rows)]
''',
    },
    fix=[("scoring.py", "min_score=@bad@", "min_score=0")],
    test=r'''
from api import list_results

rows = @ROWS@
assert len(list_results(rows)) == len(rows), list_results(rows)
''',
    extra=r'''
from api import podium
assert [r["id"] for r in list_results(rows, @MS@)] == @E@
assert len(list_results(rows * 8)) == 10
assert podium(rows)[0] == @TOP@
''',
    gt=dict(file="scoring.py", func="keep", cause="keep() defaults min_score to @bad@ although the documented default is 0, so low-scoring rows are silently dropped"),
    variants=[
        dict(bad="0.5", ROWS='[{"id": 1, "score": 0.2}, {"id": 2, "score": 0.9}, {"id": 3, "score": 0.0}]', MS="0.5", E="[2]", TOP="2"),
        dict(bad="50", ROWS='[{"id": 1, "score": 10}, {"id": 2, "score": 70}, {"id": 3, "score": 30}]', MS="30", E="[2, 3]", TOP="2"),
        dict(bad="1", ROWS='[{"id": 5, "score": 0}, {"id": 6, "score": 1}, {"id": 7, "score": 3}]', MS="1", E="[6, 7]", TOP="7"),
        dict(bad="0.25", ROWS='[{"id": 1, "score": 0.1}, {"id": 2, "score": 0.25}, {"id": 3, "score": 0.05}]', MS="0.25", E="[2]", TOP="2"),
    ])
