"""Kind `fix`: fix a buggy on-call helper script. Each template = correct source + injectable bugs + case generator.
Hidden tests = JSON call/expect cases computed from the correct source; every injected bug is verified to be caught."""
import json
import random

# ---------------------------------------------------------------- templates
T = {}


def template(name, src, bugs, gen, edge):
    T[name] = dict(src=src.strip("\n") + "\n", bugs=bugs, gen=gen, edge=edge)


# 1 disk alerts ----------------------------------------------------------------
def _df(rng, rows):
    out = ["Filesystem     1024-blocks      Used Available Capacity Mounted on"]
    for i, (pct, mount) in enumerate(rows):
        out.append(f"/dev/sd{chr(97 + i)}1      {rng.randint(10**6, 10**7)}  {rng.randint(10**5, 10**6)}  {rng.randint(10**5, 10**6)}  {pct}% {mount}")
    return "\n".join(out) + "\n"


template("disk_alerts", '''
def disk_alerts(df_output, warn=80, crit=90):
    """Parse `df -P` output text. Return a list of [mount, percent, level] for filesystems at or above `warn`
    percent used; level is 'crit' if percent >= crit, else 'warn'. Sorted by percent descending, then mount ascending.
    The first line is a header."""
    out = []
    for line in df_output.strip().splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        pct = int(parts[4].rstrip('%'))
        mount = parts[5]
        if pct >= warn:
            level = 'crit' if pct >= crit else 'warn'
            out.append([mount, pct, level])
    out.sort(key=lambda x: (-x[1], x[0]))
    return out
''', [("warn_gt", "if pct >= warn:", "if pct > warn:"), ("crit_gt", "'crit' if pct >= crit", "'crit' if pct > crit"),
      ("header", "splitlines()[1:]", "splitlines()[0:]"), ("sort_asc", "(-x[1], x[0])", "(x[1], x[0])")],
    lambda rng: [("disk_alerts", [_df(rng, [(rng.randint(40, 99), m) for m in rng.sample(["/", "/var", "/data", "/boot", "/home", "/tmp"], rng.randint(2, 5))]), rng.choice([80, 85]), rng.choice([90, 95])]) for _ in range(6)],
    lambda rng: [("disk_alerts", [_df(rng, [(80, "/a"), (90, "/b"), (79, "/c"), (89, "/d"), (95, "/e"), (95, "/aa")]), 80, 90]),
                 ("disk_alerts", [_df(rng, [(85, "/z"), (85, "/m")]), 85, 95]), ("disk_alerts", [_df(rng, [(10, "/x")]), 80, 90])])

# 2 duration -------------------------------------------------------------------
template("parse_duration", '''
import re


def parse_duration(s):
    """Parse '1d2h30m15s' style durations into seconds. Units: d, h, m (minutes), s. The whole string must be
    made of <digits><unit> groups (e.g. '5mfoo', '', '5', '1h 30m' are invalid); raise ValueError otherwise."""
    if not re.fullmatch(r'(\\d+[dhms])+', s):
        raise ValueError(s)
    units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    return sum(int(n) * units[u] for n, u in re.findall(r'(\\d+)([dhms])', s))
''', [("prefix_match", "re.fullmatch(", "re.match("), ("day_secs", "'d': 86400", "'d': 84600"), ("min_secs", "'m': 60,", "'m': 600,"),
      ("last_unit_only", "return sum(int(n) * units[u] for n, u in re.findall(r'(\\d+)([dhms])', s))", "return max(int(n) * units[u] for n, u in re.findall(r'(\\d+)([dhms])', s))")],
    lambda rng: [("parse_duration", ["".join(f"{rng.randint(1, 99)}{u}" for u in rng.sample("dhms", rng.randint(1, 3)) if True)]) for _ in range(6)],
    lambda rng: [("parse_duration", [x]) for x in ["90s", "1h30m", "2d", "1d2h3m4s", "15m", "", "5", "m5", "5mfoo", "1h 30m", "abc", "10m5s"]])

# 3 budget ---------------------------------------------------------------------
template("budget_remaining_pct", '''
def budget_remaining_pct(slo_pct, total, failed):
    """Percent of the error budget left, rounded to 2 decimals; negative when overspent. slo_pct like 99.9
    (never 100). With no traffic (total <= 0) the whole budget (100.0) remains."""
    if total <= 0:
        return 100.0
    allowed = total * (100.0 - slo_pct) / 100.0
    return round((allowed - failed) / allowed * 100.0, 2)
''', [("zero_total", "if total <= 0:", "if total < 0:"),
      ("clamp", "    return round((allowed - failed) / allowed * 100.0, 2)", "    return max(0.0, round((allowed - failed) / allowed * 100.0, 2))"),
      ("denominator", "/ allowed * 100.0", "/ total * 100.0")],
    lambda rng: [("budget_remaining_pct", [rng.choice([99.0, 99.5, 99.9, 99.95]), (t := rng.randint(10**4, 10**7)), rng.randint(0, t // 100)]) for _ in range(6)],
    lambda rng: [("budget_remaining_pct", [99.9, 0, 0]), ("budget_remaining_pct", [99.9, 1000000, 5000]), ("budget_remaining_pct", [99.0, 10000, 100]), ("budget_remaining_pct", [99.5, 200000, 1000])])

# 4 on-call rotation -----------------------------------------------------------
template("oncall_for_week", '''
def oncall_for_week(engineers, week_index, overrides=None):
    """Who is on call in `week_index`? Round-robin over `engineers`, engineers[0] on week 0. Negative weeks wrap
    backwards (week -1 is the last engineer). `overrides` is a list of [week_index, name] pairs that take
    precedence, even for names that are not in `engineers`."""
    ov = dict(overrides or [])
    if week_index in ov:
        return ov[week_index]
    return engineers[week_index % len(engineers)]
''', [("off_by_one", "engineers[week_index % len(engineers)]", "engineers[(week_index + 1) % len(engineers)]"),
      ("abs_week", "engineers[week_index % len(engineers)]", "engineers[abs(week_index) % len(engineers)]"),
      ("override_known_only", "if week_index in ov:", "if week_index in ov and ov[week_index] in engineers:")],
    lambda rng: [("oncall_for_week", [(e := rng.sample(["ana", "bo", "cy", "di", "ed", "fay"], rng.randint(2, 5))), rng.randint(-8, 12), rng.choice([None, [[3, "zed"]], [[1, e[0]]]])]) for _ in range(6)],
    lambda rng: [("oncall_for_week", [["ana", "bo", "cy"], -1, None]), ("oncall_for_week", [["ana", "bo", "cy"], -4, None]), ("oncall_for_week", [["ana", "bo", "cy"], 5, None]),
                 ("oncall_for_week", [["ana", "bo", "cy"], 2, [[2, "contractor"]]]), ("oncall_for_week", [["ana", "bo"], 0, None])])

# 5 backoff --------------------------------------------------------------------
template("backoff_delays", '''
def backoff_delays(base_ms, factor, cap_ms, attempts, jitter_ms=0):
    """Delays (ms) before each retry: base_ms * factor**i for i = 0..attempts-1, each capped at cap_ms, and only
    then a fixed jitter_ms is added (so a delay may exceed cap_ms by jitter_ms). Returns a list of length `attempts`."""
    return [min(base_ms * factor ** i, cap_ms) + jitter_ms for i in range(attempts)]
''', [("jitter_before_cap", "min(base_ms * factor ** i, cap_ms) + jitter_ms", "min(base_ms * factor ** i + jitter_ms, cap_ms)"),
      ("range_start", "for i in range(attempts)", "for i in range(1, attempts + 1)"),
      ("linear", "factor ** i", "factor * i")],
    lambda rng: [("backoff_delays", [rng.choice([100, 250, 500]), rng.choice([2, 3]), rng.choice([2000, 5000, 30000]), rng.randint(1, 9), rng.choice([0, 0, 50])]) for _ in range(6)],
    lambda rng: [("backoff_delays", [100, 2, 1000, 6, 50]), ("backoff_delays", [100, 2, 100000, 4, 0]), ("backoff_delays", [200, 3, 10000, 0, 10])])

# 6 should_page ----------------------------------------------------------------
template("should_page", '''
def should_page(samples, threshold, min_breaches, window):
    """samples: metric values, oldest first. Page (True) if at least `min_breaches` of the LAST `window` samples
    are strictly greater than `threshold`. A non-positive window looks at nothing."""
    recent = samples[-window:] if window > 0 else []
    breaches = sum(1 for v in recent if v > threshold)
    return breaches >= min_breaches
''', [("ge_threshold", "v > threshold", "v >= threshold"), ("gt_breaches", "breaches >= min_breaches", "breaches > min_breaches"),
      ("first_window", "samples[-window:]", "samples[:window]")],
    lambda rng: [("should_page", [[rng.randint(0, 100) for _ in range(rng.randint(3, 15))], rng.choice([50, 70]), rng.randint(1, 4), rng.randint(2, 8)]) for _ in range(8)],
    lambda rng: [("should_page", [[1, 2, 50, 50, 3], 50, 1, 5]), ("should_page", [[60, 60, 1, 1, 1, 1], 50, 2, 3]), ("should_page", [[1, 1, 1, 60, 60], 50, 2, 2]),
                 ("should_page", [[60, 60, 60], 50, 3, 3]), ("should_page", [[60], 50, 1, 0])])

# 7 cert status ----------------------------------------------------------------
template("cert_status", '''
def cert_status(not_after_epoch, now_epoch, warn_days=30):
    """Return [days_left, status]. days_left is whole days remaining, rounded DOWN (floor), so it is negative once
    expired (expired 1 second ago -> -1). status is 'expired' if now >= not_after, 'expiring' if days_left < warn_days,
    otherwise 'ok'."""
    days_left = (not_after_epoch - now_epoch) // 86400
    if now_epoch >= not_after_epoch:
        status = 'expired'
    elif days_left < warn_days:
        status = 'expiring'
    else:
        status = 'ok'
    return [days_left, status]
''', [("trunc", "(not_after_epoch - now_epoch) // 86400", "int((not_after_epoch - now_epoch) / 86400)"),
      ("expired_gt", "now_epoch >= not_after_epoch", "now_epoch > not_after_epoch"), ("warn_le", "elif days_left < warn_days:", "elif days_left <= warn_days:")],
    lambda rng: [("cert_status", [(n := 1_700_000_000 + rng.randint(0, 10**7)), n - rng.randint(-60 * 86400, 60 * 86400), rng.choice([14, 30, 45])]) for _ in range(6)],
    lambda rng: [("cert_status", [1_700_000_000, 1_700_000_001, 30]), ("cert_status", [1_700_000_000, 1_700_000_000, 30]), ("cert_status", [1_700_000_000 + 30 * 86400, 1_700_000_000, 30]),
                 ("cert_status", [1_700_000_000 + 30 * 86400 + 5, 1_700_000_000, 30]), ("cert_status", [1_700_000_000 + 86400 * 3, 1_700_000_000 + 10, 7])])

# 8 percentile -----------------------------------------------------------------
template("percentile", '''
def percentile(values, p):
    """Nearest-rank percentile, p an integer in 1..100: rank = ceil(p * n / 100) (integer arithmetic) on the
    ascending-sorted values; return sorted[rank - 1]. Return None for an empty list."""
    if not values:
        return None
    s = sorted(values)
    rank = -(-p * len(s) // 100)
    return s[int(rank) - 1]
''', [("floor_rank", "rank = -(-p * len(s) // 100)", "rank = max(1, p * len(s) // 100)"), ("no_minus_one", "s[int(rank) - 1]", "s[min(int(rank), len(s) - 1)]"),
      ("unsorted", "s = sorted(values)", "s = list(values)"), ("empty", "if not values:", "if values is None:")],
    lambda rng: [("percentile", [[rng.randint(1, 500) for _ in range(rng.randint(1, 40))], rng.choice([50, 90, 95, 99, 100])]) for _ in range(8)],
    lambda rng: [("percentile", [[], 95]), ("percentile", [[5, 1, 9, 3, 7], 100]), ("percentile", [list(range(21, 0, -1)), 50]), ("percentile", [[4, 2, 8], 1]), ("percentile", [[3, 1, 2], 67])])

# 9 dedupe ---------------------------------------------------------------------
template("dedupe_alerts", '''
def dedupe_alerts(alerts, window_s):
    """alerts: list of [timestamp, key] sorted by timestamp. Suppress an alert when the same key was last EMITTED
    (not merely seen) less than window_s seconds earlier. Return the emitted alerts, in order, as [timestamp, key]."""
    last_emit = {}
    out = []
    for ts, key in alerts:
        if key in last_emit and ts - last_emit[key] < window_s:
            continue
        last_emit[key] = ts
        out.append([ts, key])
    return out
''', [("le_window", "ts - last_emit[key] < window_s", "ts - last_emit[key] <= window_s"),
      ("sliding", "            continue\n", "            last_emit[key] = ts\n            continue\n"),
      ("any_key", "if key in last_emit and", "if last_emit and")],
    lambda rng: [("dedupe_alerts", [sorted([[rng.randint(0, 600), rng.choice("abc")] for _ in range(rng.randint(3, 14))]), rng.choice([30, 60, 120])]) for _ in range(6)],
    lambda rng: [("dedupe_alerts", [[[0, "a"], [60, "a"], [61, "a"]], 60]), ("dedupe_alerts", [[[0, "a"], [40, "a"], [80, "a"]], 60]), ("dedupe_alerts", [[[0, "a"], [1, "b"]], 60]), ("dedupe_alerts", [[], 10])])

# 10 quorum --------------------------------------------------------------------
template("cluster_healthy", '''
def cluster_healthy(statuses, quorum=None):
    """statuses: list of booleans (True = node up). Healthy when strictly more than half of the nodes are up, unless
    `quorum` is given (any int, including 0), in which case at least `quorum` nodes must be up. An empty list is unhealthy."""
    n = len(statuses)
    if n == 0:
        return False
    up = sum(1 for s in statuses if s)
    need = quorum if quorum is not None else n // 2 + 1
    return up >= need
''', [("half_round", "n // 2 + 1", "(n + 1) // 2"), ("quorum_or", "quorum if quorum is not None else n // 2 + 1", "quorum or n // 2 + 1"), ("gt_need", "return up >= need", "return up > need")],
    lambda rng: [("cluster_healthy", [[rng.random() < 0.6 for _ in range(rng.randint(1, 7))], rng.choice([None, None, 1, 2, 3])]) for _ in range(8)],
    lambda rng: [("cluster_healthy", [[True, True, False, False], None]), ("cluster_healthy", [[True, False, False], 0]), ("cluster_healthy", [[False, False, False], 0]), ("cluster_healthy", [[True, True, False], 2]),
                 ("cluster_healthy", [[], None]), ("cluster_healthy", [[True, True, True, False, False], None])])

NAMES = sorted(T)


# ---------------------------------------------------------------- building
def apply_bugs(src, tname, bug_names):
    for bn in bug_names:
        old, new = next((o, n) for b, o, n in T[tname]["bugs"] if b == bn)
        assert src.count(old) == 1, (tname, bn, src.count(old))
        src = src.replace(old, new)
    return src


def run_case(ns, fn, args):
    try:
        return {"value": json.loads(json.dumps(ns[fn](*json.loads(json.dumps(args)))))}
    except Exception as e:
        return {"raises": type(e).__name__}


def load(src):
    ns = {}
    exec(compile(src, "<src>", "exec"), ns)
    return ns


def make_fix(seed, diff, tnames=None):
    for salt in range(50):
        try:
            return _make_fix(random.Random(seed * 1000 + salt), seed, diff, tnames)
        except AssertionError:
            continue
    raise RuntimeError("no valid bug combination for seed %d" % seed)


def _make_fix(rng, seed, diff, tnames):
    nt = 1 if diff != "hard" else 2
    tnames = tnames or rng.sample(NAMES, nt)
    nb = {"easy": [1], "medium": [2, 2, 3], "hard": [2, 2]}[diff]
    chosen = {}
    for tn in tnames:
        k = rng.choice(nb) if diff != "hard" else 2
        chosen[tn] = [b for b, _, _ in T[tn]["bugs"]]
        rng.shuffle(chosen[tn])
        chosen[tn] = chosen[tn][:k]
    fixed_src = "\n\n".join(T[tn]["src"] for tn in tnames)
    buggy_src = "\n\n".join(apply_bugs(T[tn]["src"], tn, chosen[tn]) for tn in tnames)
    if "import re" in fixed_src:  # hoist imports
        fixed_src = "import re\n\n" + fixed_src.replace("import re\n\n\n", "").replace("import re\n\n", "")
        buggy_src = "import re\n\n" + buggy_src.replace("import re\n\n\n", "").replace("import re\n\n", "")
    ns_ok, ns_bad = load(fixed_src), load(buggy_src)
    cases, nrnd = [], 0
    for tn in tnames:
        cs = T[tn]["gen"](rng) + T[tn]["edge"](rng)
        cases += cs
    # verify each bug is detected on its own by the hidden cases (re-using per-template functions)
    cases = [dict(fn=fn, args=json.loads(json.dumps(a)), expect=run_case(ns_ok, fn, a)) for fn, a in cases]
    for tn in tnames:
        for bn in chosen[tn]:
            single = load(("import re\n\n" if "import re" in T[tn]["src"] else "") + apply_bugs(T[tn]["src"].replace("import re\n\n\n", ""), tn, [bn]))
            fns = {c["fn"] for c in cases if c["fn"] in single}
            assert any(run_case(single, c["fn"], c["args"]) != c["expect"] for c in cases if c["fn"] in fns), (tn, bn)
    # visible failing examples: first failing case per function (up to 3)
    shown, seen = [], set()
    for c in cases:
        got = run_case(ns_bad, c["fn"], c["args"])
        if got != c["expect"] and c["fn"] not in seen:
            seen.add(c["fn"])
            shown.append((c, got))
    shown = shown[:3]
    vis = "\n".join(f"{c['fn']}(*{json.dumps(c['args'])})\n    expected: {json.dumps(c['expect'].get('value', 'raises ' + c['expect'].get('raises', '')))}\n    actual:   {json.dumps(g.get('value', 'raises ' + g.get('raises', '')))}" for c, g in shown)
    prompt = (f"This on-call helper module `oncall.py` contains {sum(len(v) for v in chosen.values())} bug(s). The docstrings define the intended behavior. "
              f"Fix the bugs. Do not rename functions or change signatures.\n\n```python\n# file: oncall.py\n{buggy_src.strip()}\n```\n\n"
              f"Some failing checks (call, expected, actual):\n{vis}\n\n"
              "Return the complete corrected file in one ```python block whose first line is `# file: oncall.py`. No explanation.")
    spec = dict(mode="fix", module="oncall.py", cases=cases)
    return dict(inputs=dict(prompt=prompt, buggy_file=buggy_src, entry="oncall.py"),
                hidden=dict(spec=spec, templates=tnames, bugs=chosen, fixed_file=fixed_src),
                reference_answer=f"```python\n# file: oncall.py\n{fixed_src.strip()}\n```")
