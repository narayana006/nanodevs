"""Kind `script`: write a log-analysis script from spec; graded on hidden log fixtures. Expected outputs come from the
reference script (run at generation time), so reference == ground truth by construction."""
import json
import os
import random
import subprocess
import sys
import tempfile

from common import iso, epoch_of

HERE = os.path.dirname(os.path.abspath(__file__))
SVCS = ["checkout", "payments", "search", "auth", "catalog", "inventory"]
MSG_ERR = ["timeout after {n}ms calling payments", "connection refused to 10.0.{a}.{b}:5432", "retry {a} of 5 failed for order {n}",
           "upstream returned 502 for request req-{n}", "pool exhausted: {a} waiters"]
MSG_OK = ["request served", "cache refreshed in {n}ms", "healthcheck ok", "config reloaded rev {a}", "worker {a} started"]

COMMON = '''import sys, json, re, math
from datetime import datetime, timezone
LEVELS = {"DEBUG", "INFO", "WARN", "ERROR"}


def to_epoch(s):
    try:
        return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
    except (ValueError, TypeError):
        return None


def iso(e):
    return datetime.fromtimestamp(e, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
'''
PARSERS = {"kv": '''
KV = re.compile(r'^(\\S+) svc=(\\S+) lvl=(\\S+)(?: status=(\\d+) latency_ms=(\\d+))? msg="(.*)"$')


def parse(line):
    m = KV.match(line)
    if not m:
        return None
    ts = to_epoch(m.group(1))
    if ts is None or m.group(3) not in LEVELS:
        return None
    return dict(ts=ts, svc=m.group(2), lvl=m.group(3), status=int(m.group(4)) if m.group(4) else None,
                lat=int(m.group(5)) if m.group(5) else None, msg=m.group(6))
''', "json": '''

def parse(line):
    try:
        o = json.loads(line)
    except ValueError:
        return None
    if not isinstance(o, dict):
        return None
    ts = to_epoch(o.get("ts"))
    if ts is None or "service" not in o or o.get("level") not in LEVELS or "message" not in o:
        return None
    return dict(ts=ts, svc=o["service"], lvl=o["level"], status=o.get("status"), lat=o.get("latency_ms"), msg=o["message"])
''', "text": '''

def parse(line):
    p = line.split(None, 5)
    if len(p) < 6:
        return None
    ts = to_epoch(p[0])
    if ts is None or p[2] not in LEVELS:
        return None
    for x in (p[3], p[4]):
        if x != "-" and not x.isdigit():
            return None
    return dict(ts=ts, svc=p[1], lvl=p[2], status=None if p[3] == "-" else int(p[3]),
                lat=None if p[4] == "-" else int(p[4]), msg=p[5])
'''}
READ = '''

def read(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\\n")
            if not line.strip():
                continue
            r = parse(line)
            if r is None:
                bad += 1
            else:
                rows.append(r)
    return rows, bad


rows, bad = read(sys.argv[1])
'''
BODIES = {
    "counts": '''
by = {}
for r in rows:
    d = by.setdefault(r["svc"], {})
    d[r["lvl"]] = d.get(r["lvl"], 0) + 1
print(json.dumps({"total": len(rows), "malformed": bad, "by_service": by}))
''',
    "percentiles": '''
lat = {}
for r in rows:
    if r["lat"] is not None:
        lat.setdefault(r["svc"], []).append(r["lat"])
out = {}
for s, v in lat.items():
    v.sort()
    n = len(v)
    pick = lambda p: v[-(-p * n // 100) - 1]
    out[s] = {"n": n, "p50": pick(50), "p95": pick(95), "p99": pick(99)}
print(json.dumps({"services": out}))
''',
    "windows": '''
ws, thr = int(sys.argv[2]), float(sys.argv[3])
w = {}
for r in rows:
    if r["status"] is None:
        continue
    k = r["ts"] // ws * ws
    t = w.setdefault(k, [0, 0])
    t[0] += 1
    t[1] += 1 if r["status"] >= 500 else 0
wins = [{"start": iso(k), "total": t[0], "errors": t[1], "error_rate": round(t[1] / t[0], 4)} for k, t in sorted(w.items())]
alerts = [iso(k) for k, t in sorted(w.items()) if t[1] / t[0] > thr]
print(json.dumps({"windows": wins, "alerts": alerts}))
''',
    "burn": '''
slo = float(sys.argv[2])
budget = 1 - slo / 100.0
reqs = [r for r in rows if r["status"] is not None]
now = max((r["ts"] for r in rows), default=None)
burn = {}
for name, secs in (("5m", 300), ("1h", 3600), ("6h", 21600)):
    sel = [r for r in reqs if now is not None and now - secs < r["ts"] <= now]
    burn[name] = (sum(1 for r in sel if r["status"] >= 500) / len(sel)) / budget if sel else 0.0
if (burn["5m"] >= 14.4 and burn["1h"] >= 14.4) or (burn["1h"] >= 6 and burn["6h"] >= 6):
    dec = "page"
elif burn["6h"] >= 1:
    dec = "ticket"
else:
    dec = "ok"
print(json.dumps({"burn_5m": round(burn["5m"], 3), "burn_1h": round(burn["1h"], 3), "burn_6h": round(burn["6h"], 3), "decision": dec}))
''',
    "incidents": '''
gap = int(sys.argv[2])
per = {}
for r in rows:
    if r["lvl"] == "ERROR":
        per.setdefault(r["svc"], []).append(r["ts"])
inc = []
for s, ts in per.items():
    ts.sort()
    cur = [ts[0], ts[0], 1]
    for t in ts[1:]:
        if t - cur[1] <= gap:
            cur[1], cur[2] = t, cur[2] + 1
        else:
            inc.append((s, cur))
            cur = [t, t, 1]
    inc.append((s, cur))
res = [{"service": s, "start": iso(c[0]), "end": iso(c[1]), "count": c[2]} for s, c in inc if c[2] >= 2]
res.sort(key=lambda x: (x["start"], x["service"]))
print(json.dumps({"incidents": res}))
''',
    "topmsgs": '''
k = int(sys.argv[2])
cnt = {}
for r in rows:
    if r["lvl"] in ("ERROR", "WARN"):
        m = re.sub(r"\\d+", "N", r["msg"].lower())
        cnt[m] = cnt.get(m, 0) + 1
top = sorted(cnt.items(), key=lambda x: (-x[1], x[0]))[:k]
print(json.dumps({"top": [{"msg": m, "count": c} for m, c in top]}))
''',
}


def reference_script(ttype, fmt):
    return COMMON + PARSERS[fmt] + READ + BODIES[ttype]


# ------------------------------------------------------------- fixtures
def fmt_line(fmt, r):
    if fmt == "kv":
        s = f'{iso(r["ts"])} svc={r["svc"]} lvl={r["lvl"]}'
        if r["status"] is not None:
            s += f' status={r["status"]} latency_ms={r["lat"]}'
        return s + f' msg="{r["msg"]}"'
    if fmt == "json":
        o = {"ts": iso(r["ts"]), "service": r["svc"], "level": r["lvl"]}
        if r["status"] is not None:
            o["status"], o["latency_ms"] = r["status"], r["lat"]
        o["message"] = r["msg"]
        return json.dumps(o)
    st = "-" if r["status"] is None else r["status"]
    lt = "-" if r["lat"] is None else r["lat"]
    return f'{iso(r["ts"])} {r["svc"]} {r["lvl"]} {st} {lt} {r["msg"]}'


def rec(rng, ts, svc, p_err, p_req=0.8, force_err_line=False):
    if rng.random() < p_req:
        bad = rng.random() < p_err
        status = rng.choice([500, 502, 503]) if bad else rng.choice([200] * 8 + [201, 404])
        lat = int(rng.lognormvariate(5.0, 0.7)) + 1
        return dict(ts=ts, svc=svc, lvl="ERROR" if bad and rng.random() < 0.8 else "INFO", status=status, lat=lat,
                    msg=rng.choice(MSG_ERR if bad else MSG_OK).format(n=rng.randint(10, 99999), a=rng.randint(1, 9), b=rng.randint(1, 250)))
    lvl = rng.choice(["INFO", "INFO", "WARN", "ERROR", "DEBUG"])
    pool = MSG_ERR if lvl in ("ERROR", "WARN") else MSG_OK
    return dict(ts=ts, svc=svc, lvl=lvl, status=None, lat=None,
                msg=rng.choice(pool).format(n=rng.randint(10, 99999), a=rng.randint(1, 9), b=rng.randint(1, 250)))


def malformed(rng, fmt, valid_line):
    k = rng.randint(0, 4)
    if k == 0:
        return rng.choice(["-- MARK --", "Traceback (most recent call last):", "###", "{broken"])
    if k == 1:
        return valid_line[:rng.randint(5, 28)]
    if k == 2:
        return valid_line.replace("20", "2026-13-45T25:61:61Z ZZ", 1) if fmt != "json" else valid_line.replace('"ts": "', '"ts": "yesterday ', 1)
    if k == 3:
        return valid_line.replace("INFO", "FATALX", 1).replace("ERROR", "FATALX", 1).replace("WARN", "FATALX", 1).replace("DEBUG", "FATALX", 1)
    return valid_line[:rng.randint(5, 28)]


def make_log(rng, fmt, n, t0, span, nsv=4, p_err=0.15, n_bad=0, unsorted=False, extra=()):
    svcs = SVCS[:nsv]
    recs = [rec(rng, t0 + rng.randint(0, span), rng.choice(svcs), p_err) for _ in range(n)] + list(extra)
    recs.sort(key=lambda r: r["ts"])
    lines = [fmt_line(fmt, r) for r in recs]
    for _ in range(n_bad):
        if lines:
            i = rng.randrange(len(lines))
            lines.insert(i, malformed(rng, fmt, lines[i]))
        else:
            lines.append("-- MARK --")
    for _ in range(rng.randint(0, 2) if n else 0):
        lines.insert(rng.randrange(len(lines) + 1), rng.choice(["", "   "]))
    if unsorted and len(lines) > 4:
        for _ in range(len(lines) // 3):
            i, j = rng.randrange(len(lines)), rng.randrange(len(lines))
            lines[i], lines[j] = lines[j], lines[i]
    return "\n".join(lines) + ("\n" if lines else "")


def r_(ts, svc, lvl, status=None, lat=None, msg="x"):
    return dict(ts=ts, svc=svc, lvl=lvl, status=status, lat=lat, msg=msg)


def fixtures_for(rng, ttype, fmt, diff):
    T0 = epoch_of(2026, rng.randint(1, 11), rng.randint(1, 28), rng.randint(0, 20), 0, 0) // 21600 * 21600
    hard = diff == "hard"
    if ttype == "burn":
        return burn_fixtures(rng, fmt, T0)
    if False:
        span, big = 7 * 3600, 420
    elif ttype == "windows":
        span, big = 3600, 220
    else:
        span, big = 1800, 160
    fx = []

    def arg_sets():
        if ttype == "windows":
            return [str(rng.choice([60, 300])), rng.choice(["0.05", "0.1", "0.2"])]
        if ttype == "burn":
            return [rng.choice(["99.9", "99.5", "99.0", "99.95"])]
        if ttype == "incidents":
            return [str(rng.choice([30, 60, 120]))]
        if ttype == "topmsgs":
            return [str(rng.choice([2, 3, 5]))]
        return []

    # 1 small, 2 empty/blank, 3 big+malformed(+unsorted), 4 edge, 5 medium
    fx.append(dict(argv=arg_sets(), text=make_log(rng, fmt, rng.randint(12, 24), T0, span // 4, 3, 0.35)))
    fx.append(dict(argv=arg_sets(), text="" if rng.random() < .5 else "\n  \n"))
    fx.append(dict(argv=arg_sets(), text=make_log(rng, fmt, big, T0, span, 5, 0.18, n_bad=rng.randint(4, 9), unsorted=True)))
    fx.append(edge_fixture(rng, ttype, fmt, T0))
    fx.append(dict(argv=arg_sets(), text=make_log(rng, fmt, big // 3, T0, span, 4, 0.3 if ttype != "burn" else rng.choice([0.004, 0.02, 0.08]), n_bad=rng.randint(0, 3), unsorted=hard)))
    return fx


def make_burn_log(rng, fmt, slo, T0, scale, n_bad, mults=None):
    bud = 1 - float(slo) / 100
    now = T0 + 6 * 3600
    recs = []
    for lo, hi, n in ((0, 300, 60), (300, 3600, 100), (3600, 21600, 240)):
        m = mults[[300, 3600, 21600].index(hi)] if mults else rng.choice([0, 0.3, 1.5, 3, 8, 20])
        p = min(0.9, m * bud)
        for _ in range(max(3, int(n * scale))):
            bad = rng.random() < p
            recs.append(r_(now - rng.randint(lo, hi - 1), rng.choice(SVCS[:4]), "ERROR" if bad else "INFO", 503 if bad else 200, rng.randint(5, 300), "m"))
    recs.append(r_(now, "auth", "INFO", 200, 7, "tip"))
    recs.sort(key=lambda r: r["ts"])
    lines = [fmt_line(fmt, r) for r in recs]
    for _ in range(n_bad):
        i = rng.randrange(len(lines))
        lines.insert(i, malformed(rng, fmt, lines[i]))
    for _ in range(len(lines) // 3):
        i, j = rng.randrange(len(lines)), rng.randrange(len(lines))
        lines[i], lines[j] = lines[j], lines[i]
    return "\n".join(lines) + "\n"


def burn_fixtures(rng, fmt, T0):
    fx = []
    for scale, nb in ((0.3, 1), (None, 0), (1.0, 6), (0.0, 0), (0.6, 2)):
        if scale is None:
            fx.append(dict(argv=["99.9"], text="\n"))
            continue
        if scale == 0.0:
            fx.append(edge_fixture(rng, "burn", fmt, T0))
            continue
        for _ in range(200):
            slo = rng.choice(["99.0", "99.5", "99.9"])
            text = make_burn_log(rng, fmt, slo, T0, scale, nb)
            if burn_text_ok(text, fmt, slo):
                break
        fx.append(dict(argv=[slo], text=text))
    for mults in ((20, 0, 0), (0, 8, 8)):  # fast spike only in the 5m window / slow burn without a spike
        for _ in range(200):
            text = make_burn_log(rng, fmt, "99.0", T0, 0.8, 2, mults)
            if burn_text_ok(text, fmt, "99.0"):
                break
        fx.append(dict(argv=["99.0"], text=text))
    return fx


def burn_text_ok(text, fmt, slo):
    out = run_ref(reference_script("burn", fmt), [dict(argv=[slo], text=text)])[0]
    return all(abs(out[k] - th) / th > 0.03 for k in ("burn_5m", "burn_1h", "burn_6h") for th in (14.4, 6, 1))


def edge_fixture(rng, ttype, fmt, T0):
    recs, argv = [], []
    if ttype == "windows":
        argv = ["300", "0.25"]
        a = T0
        recs += [r_(a + 10, "checkout", "INFO", 200, 20), r_(a + 40, "checkout", "ERROR", 500, 30), r_(a + 100, "auth", "INFO", 200, 12),
                 r_(a + 299, "auth", "INFO", 201, 15)]                 # window A: 1/4 == 0.25 -> not an alert
        recs += [r_(a + 300, "auth", "ERROR", 503, 90), r_(a + 301, "auth", "INFO", 200, 8), r_(a + 330, "auth", "ERROR", 502, 90)]  # B: 2/3
        recs += [r_(a + 900, "auth", "INFO", None, None, "no status here")]                                           # no requests -> no window
    elif ttype == "incidents":
        argv = ["60"]
        recs += [r_(T0 + k, "payments", "ERROR", None, None, "e") for k in (0, 60, 120)]   # exactly gap apart -> grouped
        recs += [r_(T0 + 181, "payments", "ERROR", None, None, "e")]                       # 61 later -> new, single, dropped
        recs += [r_(T0 + 400, "auth", "ERROR", None, None, "e"), r_(T0 + 405, "auth", "WARN", None, None, "w"), r_(T0 + 470, "auth", "ERROR", None, None, "e")]
        recs += [r_(T0 + 50, "auth", "ERROR", None, None, "e"), r_(T0 + 100, "auth", "ERROR", None, None, "e")]
    elif ttype == "burn":
        argv = ["99.9"]
        for attempt in range(200):
            now = T0 + 7 * 3600
            recs = [r_(now, "checkout", "ERROR", 500, 10), r_(now - 300, "checkout", "ERROR", 500, 10)]   # now-300 excluded from 5m window
            recs += [r_(now - 299 - i, "checkout", "ERROR" if i < rng.randint(0, 3) else "INFO", 500 if i < 2 else 200, 10) for i in range(rng.randint(2, 6))]
            recs += [r_(now - 3600 + 1, "checkout", "INFO", 200, 10)] * rng.randint(1, 3)                  # inside 1h window (boundary)
            recs += [r_(now - 3600, "checkout", "ERROR", 503, 10)]                                         # excluded from 1h
            recs += [r_(now - 400 - 60 * i, "auth", "ERROR" if rng.random() < .3 else "INFO", 500 if rng.random() < .3 else 200, 9) for i in range(rng.randint(10, 60))]
            if burn_margin_ok(recs, 99.9):
                break
    elif ttype == "percentiles":
        recs += [r_(T0 + i, "auth", "INFO", 200, v) for i, v in enumerate([5, 50, 7, 90, 3, 11, 65, 20, 30, 1, 100, 2, 8, 9, 10, 12, 13, 14, 15, 16])]
        recs += [r_(T0 + 100, "search", "INFO", 200, 42), r_(T0 + 101, "cache", "INFO", None, None, "no latency")]
    elif ttype == "topmsgs":
        argv = ["3"]
        recs += [r_(T0 + i, "auth", "ERROR", None, None, f"Timeout after {100 + i}ms calling Payments") for i in range(3)]
        recs += [r_(T0 + 9, "auth", "WARN", None, None, "timeout after 7ms calling payments"), r_(T0 + 10, "auth", "INFO", None, None, "timeout after 1ms calling payments")]
        recs += [r_(T0 + 20 + i, "search", "WARN", None, None, f"retry {i} of 5") for i in range(2)]
        recs += [r_(T0 + 30, "search", "ERROR", None, None, "zeta failure"), r_(T0 + 31, "search", "ERROR", None, None, "alpha failure"), r_(T0 + 32, "search", "ERROR", None, None, "beta failure 9")]
    else:  # counts
        recs += [r_(T0, "auth", "ERROR"), r_(T0 + 1, "auth", "ERROR"), r_(T0 + 2, "auth", "DEBUG"), r_(T0 + 3, "cache", "WARN")]
    recs.sort(key=lambda r: r["ts"])
    lines = [fmt_line(fmt, r) for r in recs]
    if lines:
        lines.insert(1, "-- MARK --")
    random.Random(7).shuffle(lines)
    return dict(argv=argv or [], text="\n".join(lines) + "\n")


def burn_margin_ok(recs, slo):
    reqs = [r for r in recs if r["status"] is not None]
    now = max(r["ts"] for r in recs)
    b = 1 - slo / 100
    vals = []
    for secs in (300, 3600, 21600):
        sel = [r for r in reqs if now - secs < r["ts"] <= now]
        vals.append((sum(1 for r in sel if r["status"] >= 500) / len(sel)) / b if sel else 0.0)
    return all(abs(v - th) / th > 0.03 for v in vals for th in (14.4, 6, 1))


def run_ref(script, fixtures):
    """Run reference script on the fixtures locally; returns expected outputs (and writes nothing persistent)."""
    outs = []
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "ref.py")
        open(sp, "w").write(script)
        for f in fixtures:
            lp = os.path.join(d, "log.txt")
            open(lp, "w").write(f["text"])
            p = subprocess.run([sys.executable, "-I", sp, lp] + f["argv"], capture_output=True, text=True, timeout=20)
            assert p.returncode == 0, p.stderr
            outs.append(json.loads(p.stdout))
    return outs


FMT_DESC = {
    "kv": 'Each line: `<ts> svc=<service> lvl=<LEVEL> [status=<int> latency_ms=<int>] msg="<text>"`. The `status latency_ms` pair is present only on request lines. Example:\n`2026-03-04T10:15:03Z svc=checkout lvl=ERROR status=503 latency_ms=231 msg="upstream timeout"`',
    "json": 'Each line is a JSON object: `{"ts": "<ts>", "service": "<service>", "level": "<LEVEL>", "status": <int>, "latency_ms": <int>, "message": "<text>"}`; `status` and `latency_ms` are present only on request lines. Example:\n`{"ts": "2026-03-04T10:15:03Z", "service": "checkout", "level": "ERROR", "status": 503, "latency_ms": 231, "message": "upstream timeout"}`',
    "text": 'Each line: `<ts> <service> <LEVEL> <status|-> <latency_ms|-> <message...>` separated by whitespace; `-` means absent (request lines have both numbers). The message is everything after the 5th field. Example:\n`2026-03-04T10:15:03Z checkout ERROR 503 231 upstream timeout`',
}
MALF = {
    "kv": "A non-blank line is malformed if it does not match this format exactly, its timestamp is not a valid `%Y-%m-%dT%H:%M:%SZ` UTC time, or LEVEL is not one of DEBUG, INFO, WARN, ERROR.",
    "json": "A non-blank line is malformed if it is not a valid JSON object, lacks `ts`/`service`/`level`/`message`, has a timestamp that is not a valid `%Y-%m-%dT%H:%M:%SZ` UTC time, or a level that is not one of DEBUG, INFO, WARN, ERROR.",
    "text": "A non-blank line is malformed if it has fewer than 6 whitespace-separated fields, its timestamp is not a valid `%Y-%m-%dT%H:%M:%SZ` UTC time, its level is not one of DEBUG, INFO, WARN, ERROR, or status/latency is neither `-` nor digits.",
}
TASK_SPEC = {
    "counts": ('Usage: `python analyze.py LOGFILE`. Count lines per service per level.\nOutput: `{"total": <valid lines>, "malformed": <malformed lines>, "by_service": {"<svc>": {"<LEVEL>": <count>, ...}, ...}}` (only levels that occur).', 0),
    "percentiles": ('Usage: `python analyze.py LOGFILE`. For each service, consider only lines that have a latency value. Compute n and the p50, p95, p99 latency by the nearest-rank method on the ascending-sorted values: rank = ceil(p*n/100) computed with integer arithmetic, value = sorted[rank-1].\nOutput: `{"services": {"<svc>": {"n": int, "p50": int, "p95": int, "p99": int}, ...}}` (services without any latency are omitted).', 0),
    "windows": ('Usage: `python analyze.py LOGFILE WINDOW_SECONDS THRESHOLD`. Using only request lines (those with a status), bucket them into tumbling windows aligned to the Unix epoch (window start = floor(epoch/WINDOW_SECONDS)*WINDOW_SECONDS), all services combined. A request is an error if status >= 500. Output only windows containing at least one request, ordered by start:\n`{"windows": [{"start": "<ISO ts>", "total": int, "errors": int, "error_rate": <errors/total rounded to 4 decimals>}], "alerts": ["<ISO start>", ...]}` where alerts lists the starts of windows whose unrounded error rate is strictly greater than THRESHOLD (a float).', 0),
    "burn": ('Usage: `python analyze.py LOGFILE SLO_PERCENT` (e.g. 99.9). Use only request lines (those with a status; error = status >= 500). Let NOW be the largest timestamp among valid lines. For each window W in 5m, 1h, 6h take requests with NOW-W < ts <= NOW. burn = (errors/requests) / (1 - SLO_PERCENT/100), or 0.0 if the window has no requests. decision = "page" if (burn_5m >= 14.4 and burn_1h >= 14.4) or (burn_1h >= 6 and burn_6h >= 6); else "ticket" if burn_6h >= 1; else "ok". If there are no valid lines, all burns are 0.0 and the decision is "ok".\nOutput: `{"burn_5m": float, "burn_1h": float, "burn_6h": float, "decision": str}` with burns rounded to 3 decimals (decide using unrounded values). Lines may be out of order.', 0),
    "incidents": ('Usage: `python analyze.py LOGFILE GAP_SECONDS`. Per service, sort its ERROR-level lines by time (the file may be unsorted) and group consecutive ones into an incident while the gap to the previous ERROR line of that service is <= GAP_SECONDS (a larger gap starts a new incident). Report only incidents with at least 2 error lines.\nOutput: `{"incidents": [{"service": str, "start": "<ISO ts of first>", "end": "<ISO ts of last>", "count": int}]}` sorted by (start, service).', 0),
    "topmsgs": ('Usage: `python analyze.py LOGFILE K`. Consider lines whose level is ERROR or WARN. Normalize each message: lowercase it, then replace every run of digits with the single letter `N`. Count identical normalized messages.\nOutput: `{"top": [{"msg": <normalized>, "count": int}, ...]}` with the K most frequent, ordered by count descending then msg ascending.', 0),
}


def make_script(seed, diff, ttype, fmt):
    rng = random.Random(seed)
    ref = reference_script(ttype, fmt)
    fx = fixtures_for(rng, ttype, fmt, diff)
    outs = run_ref(ref, fx)
    # visible example: tiny sample from a separate rng
    vr = random.Random(seed + 99)
    ex = dict(argv=fx[0]["argv"], text=make_log(vr, fmt, 7, epoch_of(2026, 3, 4, 10, 0, 0), 600, 2, 0.3, n_bad=1))
    if ttype == "topmsgs":
        ex["argv"] = ["2"]
    ex_out = run_ref(ref, [ex])[0]
    spec_txt = TASK_SPEC[ttype][0]
    extra_args = " ".join(ex["argv"])
    prompt = (f"Write a Python 3 script `analyze.py` (standard library only, no network) for incident log analysis.\n\n"
              f"Log format. {FMT_DESC[fmt]}\nTimestamps are UTC. Blank lines are ignored. {MALF[fmt]} Malformed lines are skipped (and counted where the spec says so); the script must never crash on them. "
              f"Lines may be out of order.\n\n{spec_txt}\n\n"
              f"Print exactly one JSON object to stdout. Example run with `python analyze.py sample.log {extra_args}`:\n"
              f"sample.log:\n```\n{ex['text'].rstrip()}\n```\nstdout:\n```\n{json.dumps(ex_out)}\n```\n\n"
              f"Return the complete script in one ```python block whose first line is `# file: analyze.py`. No explanation.")
    spec = dict(mode="script", script="analyze.py",
                fixtures=[dict(argv=["log.txt"] + f["argv"], files={"log.txt": f["text"]}, expect=o) for f, o in zip(fx, outs)])
    return dict(inputs=dict(prompt=prompt, entry="analyze.py", sample=dict(argv=ex["argv"], log=ex["text"], stdout=ex_out)),
                hidden=dict(spec=spec, task_type=ttype, log_format=fmt),
                reference_answer="```python\n# file: analyze.py\n" + ref.strip() + "\n```")
