"""Seeded incident-scenario generator -> structured triage tasks (kind=triage). Stdlib only, deterministic."""
import json
import random

from common import iso, epoch_of, seeded_hex

CATEGORIES = ["bad_deploy", "resource_exhaustion", "dependency_timeout", "config_drift",
              "certificate_expiry", "noisy_neighbor", "dns_failure", "cascading_failure"]
ACTIONS = ["rollback_deploy", "restart_service", "scale_out", "free_disk_space", "enable_circuit_breaker",
           "revert_config", "renew_certificate", "evict_noisy_workload", "failover_dns_resolver",
           "enable_load_shedding"]
SEVERITIES = ["sev1", "sev2", "sev3", "sev4"]

EDGE = "api-gateway"
FRONT = ["checkout", "search", "user-profile", "cart", "web-bff"]
BACK = ["payments", "inventory", "auth", "catalog", "pricing", "notifications", "recommendations", "shipping",
        "orders", "ledger"]
DATA = ["postgres-main", "redis-cache", "kafka", "elasticsearch", "object-store"]
DNS = ["coredns", "kube-dns", "internal-dns"]
BATCH = ["reporting-batch", "ml-trainer", "image-resizer", "etl-nightly"]

SEV_BANDS = {"sev1": (27.0, 60.0), "sev2": (11.0, 23.0), "sev3": (2.8, 8.5), "sev4": (0.7, 1.6)}
N_DECOYS = {"easy": 1, "medium": 2, "hard": 3}
N_NOISE = {"easy": 8, "medium": 11, "hard": 15}
N_SYMP = {"easy": 2, "medium": 3, "hard": 4}
SIZES = {"easy": (1, 1, 1), "medium": (2, 2, 1), "hard": (2, 3, 2)}
WINDOW = 1800
BASE_METRIC = {  # tier -> (rps lo, hi, p99 lo, hi, cpu lo, hi, mem lo, hi)
    "edge": (800, 2500, 180, 300, 25, 45, 40, 60), "front": (300, 900, 200, 400, 25, 50, 40, 65),
    "back": (200, 700, 120, 300, 25, 50, 40, 65), "data": (500, 3000, 8, 40, 20, 50, 45, 70),
    "dns": (2000, 6000, 3, 9, 10, 25, 30, 45), "batch": (1, 5, 50, 90, 15, 30, 30, 50)}


def sev_of(e):
    return "sev1" if e >= 25 else "sev2" if e >= 10 else "sev3" if e >= 2 else "sev4"


# ---------------------------------------------------------------- topology
def build_topology(rng, diff):
    nf, nb, nd = SIZES[diff]
    front, back, data = rng.sample(FRONT, nf), rng.sample(BACK, nb), rng.sample(DATA, nd)
    calls = {EDGE: list(front)}
    for f in front:
        calls[f] = []
    for b in back:
        calls[b] = []
    for j, b in enumerate(back):
        calls[front[j % nf]].append(b)
    for f in front:
        extra = [b for b in back if b not in calls[f]]
        if extra and (not calls[f] or rng.random() < 0.5):
            calls[f].append(rng.choice(extra))
    for j, d in enumerate(data):
        calls[back[j % nb]].append(d)
    for b in back:
        extra = [d for d in data if d not in calls[b]]
        if extra and (not calls[b] or rng.random() < 0.5):
            calls[b].append(rng.choice(extra))
    services = [EDGE] + front + back + data
    tier = {EDGE: "edge", **{s: "front" for s in front}, **{s: "back" for s in back}, **{s: "data" for s in data}}
    return dict(front=front, back=back, data=data, calls=calls, services=services, tier=tier,
                nodes={s: "n%d" % rng.randint(1, 6) for s in services},
                versions={s: "v%d.%d.%d" % (rng.randint(1, 4), rng.randint(0, 40), rng.randint(0, 9)) for s in services})


def ancestors(topo, x):
    """BFS up the call graph: [(ancestor, callee_toward_x)]."""
    out, seen, queue = [], {x}, [x]
    while queue:
        cur = queue.pop(0)
        for p in topo["services"]:
            if cur in topo["calls"].get(p, []) and p not in seen:
                seen.add(p)
                out.append((p, cur))
                queue.append(p)
    return out


# ---------------------------------------------------------------- builder
class B:
    def __init__(self, rng, topo, diff, category, sev):
        self.rng, self.topo, self.diff, self.category, self.sev = rng, topo, diff, category, sev
        self.lines, self.over, self.victims, self.extra = [], {}, [], []
        self.onset = 1200 + rng.randint(-60, 60)
        self.E = round(rng.uniform(*SEV_BANDS[sev]), 1)
        self.root, self.anc, self.variant, self.action = None, [], None, None
        self.notes = {}
        self.base = epoch_of(2026, rng.randint(1, 11), rng.randint(1, 28), rng.randint(0, 23), rng.randint(0, 11) * 5)

    def t(self, lo, hi):
        return max(1, min(WINDOW - 5, self.onset + self.rng.randint(lo, hi)))

    def add(self, t, svc, lvl, msg, tag=None):
        self.lines.append(dict(t=int(t), svc=svc, lvl=lvl, msg=msg, tag=tag, n=len(self.lines)))

    def hit(self, svc, **kw):
        self.over.setdefault(svc, {}).update(kw)

    def symptoms(self, msgs, lvl="ERROR", tag_first=0, skip_edge_lines=False):
        """Lines on every ancestor of the root naming the callee towards the root."""
        n = N_SYMP[self.diff]
        for a, child in self.anc:
            for k in range(n):
                m = self.rng.choice(msgs)
                tag = "ev" if (tag_first and k == 0 and a != EDGE and self.notes.setdefault("ev_sym", 0) < tag_first and
                               not self.notes.update(ev_sym=self.notes["ev_sym"] + 1)) else None
                self.add(self.t(10, 420), a, lvl, m.format(callee=child, root=self.root, k=self.rng.randint(1, 3),
                                                           ms=self.rng.choice([1000, 2000, 3000, 5000])), tag)


def ids_of(b, tag):
    return [l["id"] for l in b.lines if l["tag"] == tag]


# ---------------------------------------------------------------- categories
def c_bad_deploy(b):
    r, rng = b.root, b.rng
    v0 = b.topo["versions"][r]
    p = v0[1:].split(".")
    v1 = "v%s.%d.0" % (p[0], int(p[1]) + 1)
    b.add(b.onset - rng.randint(40, 90), r, "INFO", f"deploy: rolling out {r} {v0} -> {v1} (build {seeded_hex(rng, 7)}) by ci-bot", "ev")
    exc = rng.choice(["NullPointerException in OrderMapper.map", "KeyError: 'currency_code' in handle_request",
                      "SchemaMismatch: column 'discount_v2' not found", "panic: nil pointer dereference in handlers.Serve"])
    b.add(b.t(5, 30), r, "ERROR", f"unhandled exception {exc} (release {v1})", "ev")
    b.add(b.t(40, 90), r, "ERROR", f"unhandled exception {exc} x{rng.randint(80, 900)} in last 60s (release {v1})", "ev")
    b.add(b.t(60, 120), r, "WARN", f"canary analysis failed for {v1}: error rate {rng.randint(20, 70)}% vs baseline 0.3%", "ev")
    b.symptoms(["upstream {callee} returned HTTP 500 (attempt {k}/3)", "call to {callee} failed: 500 Internal Server Error"])
    b.hit(r, err=min(95, b.E * 1.6), p99=rng.randint(600, 1500), cpu=rng.randint(40, 70))
    b.action = "rollback_deploy"


def c_resource(b):
    r, rng = b.root, b.rng
    v = b.variant
    if v == "mem":
        b.add(b.t(-200, -100), r, "WARN", f"heap usage {rng.randint(88, 93)}% of limit {rng.choice([1024, 2048, 4096])}Mi, GC overhead {rng.randint(30, 45)}% of cpu time", "ev")
        b.add(b.t(10, 60), r, "ERROR", "java.lang.OutOfMemoryError: Java heap space" if rng.random() < .5 else "container OOMKilled (exit code 137)", "ev")
        b.add(b.t(80, 160), r, "WARN", f"pod restarted {rng.randint(3, 7)} times in 10m (reason: OOMKilled)", "ev")
        b.hit(r, mem=rng.randint(96, 99), cpu=rng.randint(60, 90), err=min(95, b.E * 1.2))
        b.action = "restart_service"
    elif v == "fd":
        b.add(b.t(-150, -80), r, "WARN", f"open file descriptors {rng.randint(63000, 65000)}/65536", "ev")
        b.add(b.t(10, 60), r, "ERROR", "accept: too many open files (EMFILE)", "ev")
        b.add(b.t(70, 140), r, "ERROR", "failed to open socket to upstream: too many open files", "ev")
        b.hit(r, err=min(95, b.E * 1.2), mem=rng.randint(55, 75))
        b.action = "restart_service"
    elif v == "cpu":
        b.add(b.t(-120, -60), r, "INFO", f"inbound rps {rng.choice(['3.4', '3.6', '4.1'])}x baseline (campaign flash-sale started)", "ev")
        b.add(b.t(10, 60), r, "WARN", f"cpu saturated {rng.randint(98, 100)}% run-queue {rng.randint(14, 22)} on all replicas", "ev")
        b.add(b.t(70, 130), r, "WARN", f"request queue depth {rng.randint(700, 990)} (limit 200), autoscaler headroom available (4/12 replicas)", "ev")
        b.hit(r, cpu=99, err=min(95, b.E * 1.1), rps=int(rng.randint(300, 700) * 3.5))
        b.action = "scale_out"
    else:  # disk
        b.add(b.t(-200, -100), r, "WARN", f"disk /var/lib/data usage {rng.randint(95, 98)}% (alert at 90%)", "ev")
        b.add(b.t(10, 60), r, "ERROR", "write failed: No space left on device (ENOSPC)", "ev")
        b.add(b.t(70, 140), r, "WARN", f"log rotation failed, /var/log/{r} holds {rng.randint(30, 60)}GB", "ev")
        b.hit(r, err=min(95, b.E * 1.1), mem=rng.randint(50, 65))
        b.action = "free_disk_space"
    b.symptoms(["call to {callee} failed: 503 Service Unavailable (attempt {k}/3)", "{callee} unavailable, returning degraded response"])


DEP_EV = {
    "postgres-main": ["slow query {s}ms: UPDATE orders SET status=? (lock wait on relation orders, blocked by pid 4411)",
                      "replication lag {lag}s on replica pg-r2", "active connections 480/500, 61 waiting on locks"],
    "redis-cache": ["slowlog: KEYS session:* took {s}ms", "blocked clients {lag}", "command latency p99 {s}ms (baseline 2ms)"],
    "kafka": ["produce latency p99 {s}ms, request handler idle 3%", "under-replicated partitions {lag}", "ISR shrink on topic orders-events"],
    "elasticsearch": ["slow search {s}ms: aggregation on field 'tags' over 40M docs", "shard relocation in progress, search latency p99 {s}ms", "search queue wait {lag}s"],
    "object-store": ["slow PUT {s}ms: backend throttling (SlowDown)", "list latency p99 {s}ms", "backend throttle events {lag}/min"],
}
DEP_GENERIC = ["p99 latency {s}ms (SLO 500ms) while cpu 21% mem 48%: waiting on partner API",
               "partner-api responses slow: avg {s}ms", "worker pool healthy (12/64 busy) but downstream-bound calls p99 {s}ms"]


def c_dep_timeout(b):
    r, rng = b.root, b.rng
    pool = DEP_EV.get(r, DEP_GENERIC)
    for tmpl, (lo, hi) in zip(pool, [(5, 40), (60, 120), (130, 200)]):
        b.add(b.t(lo, hi), r, "WARN", tmpl.format(s=rng.randint(3200, 6800), lag=rng.randint(30, 90)), "ev")
    b.symptoms(["timeout calling {callee} after {ms}ms (attempt {k}/3, backoff 200ms)", "deadline exceeded waiting for {callee} ({ms}ms)"])
    b.hit(r, p99=rng.randint(3500, 7000), err=rng.uniform(1, 6), cpu=rng.randint(15, 35))
    b.action = "enable_circuit_breaker"


def c_config(b):
    r, rng = b.root, b.rng
    key, bad, good, cons = rng.choice([
        ("db.pool.max_size", "5", "50", "connection pool exhausted (max_size=5), waited 5000ms for a connection"),
        ("upstream.timeout_ms", "100", "3000", "request to upstream aborted after 100ms (timeout_ms=100)"),
        ("payment.endpoint", "https://pay-old.internal", "https://pay.internal", "connect: pay-old.internal: no route to host")])
    b.add(b.t(-120, -60), r, "INFO", f"startup version {b.topo['versions'][r]} (unchanged), config source=configmap/{r}", None)
    b.add(b.t(-50, -20), r, "INFO", f"config reload applied: checksum 9c1e{seeded_hex(rng, 2)} != repo 4b77{seeded_hex(rng, 2)}", "ev")
    b.add(b.t(0, 30), r, "WARN", f"config drift: replica {r}-2 key '{key}' = {bad} differs from git rev a4f19c (expected {good}); modified manually by user=ops-tmp", "ev")
    b.add(b.t(40, 100), r, "ERROR", cons, "ev")
    b.symptoms(["upstream {callee} returned HTTP 503 (attempt {k}/3)", "call to {callee} failed: 503 Service Unavailable"])
    b.hit(r, err=min(95, b.E * 1.4), p99=rng.randint(700, 1800), cpu=rng.randint(10, 30))
    b.action = "revert_config"


def c_cert(b):
    r, rng = b.root, b.rng
    na = iso(b.base + b.onset - rng.randint(120, 600))
    b.add(b.t(-30, 0), r, "WARN", f"server certificate CN={r}.internal NotAfter={na} is in the past (expired)", "ev")
    callers = [a for a, c in b.anc if c == r]
    for i, a in enumerate(callers):
        b.add(b.t(5, 60), a, "ERROR", f"x509: certificate has expired or is not yet valid: {r}.internal NotAfter {na}", "ev" if i == 0 else None)
    b.add(b.t(60, 120), r, "ERROR", "TLS handshake error from clients: remote error: tls: bad certificate", "ev")
    b.symptoms(["connect to {callee} failed: tls handshake failure (attempt {k}/3)", "{callee} unreachable: TLS verification failed"])
    b.hit(r, err=rng.uniform(0.2, 0.8), rps=int(rng.randint(10, 60)), cpu=rng.randint(8, 18))
    b.action = "renew_certificate"


def c_noisy(b):
    r, v, rng = b.root, b.notes["victim"], b.rng
    node = b.topo["nodes"][v]
    b.add(b.t(-90, -40), r, "INFO", f"job {rng.choice(['nightly-reindex', 'bulk-export', 'model-retrain'])} started on node {node} (cpu request 8, no cpu limit, priority low)", "ev")
    b.add(b.t(0, 50), r, "WARN", f"node {node} cpu 99%: {r} using 7.8 of 8 cores", "ev")
    b.add(b.t(10, 60), v, "WARN", f"cpu throttled: nr_throttled={rng.randint(300, 600)}/min throttled_time={rng.randint(25, 50)}s on node {node}", "ev")
    b.add(b.t(70, 130), v, "WARN", f"p99 latency {rng.randint(2000, 3500)}ms (SLO 500ms) with request volume unchanged; no deploy or config change", None)
    b.add(b.t(60, 110), v, "INFO", f"co-located workloads on node {node}: {v}, {r}", "ev")
    b.symptoms(["timeout calling {callee} after {ms}ms (attempt {k}/3, backoff 200ms)", "{callee} slow: deadline exceeded ({ms}ms)"])
    b.hit(v, p99=rng.randint(2200, 3800), cpu=100, err=rng.uniform(2, 8))
    b.hit(r, cpu=rng.randint(94, 99), err=0.1)
    b.action = "evict_noisy_workload"


def c_dns(b):
    r, rng = b.root, b.rng
    b.add(b.t(-20, 10), r, "ERROR", f"upstream resolver 10.0.0.2:53 i/o timeout; SERVFAIL rate {rng.randint(55, 85)}% over 1m", "ev")
    b.add(b.t(20, 70), r, "WARN", "cache hit ratio dropped 0.93 -> 0.12; forwarding all queries upstream", "ev")
    b.add(b.t(70, 130), r, "WARN", f"query latency p99 {rng.randint(1800, 3200)}ms (baseline 6ms)", "ev")
    n = 0
    for a, child in b.anc:
        for k in range(N_SYMP[b.diff]):
            m = rng.choice(["dial tcp: lookup {c}.svc.cluster.local: no such host (SERVFAIL)", "lookup {c}.svc.cluster.local on 10.96.0.10:53: server misbehaving"]).format(c=child)
            b.add(b.t(10, 420), a, "ERROR", m, "ev" if (n < 2 and k == 0 and a != EDGE) else None)
        n += 1 if a != EDGE else 0
    b.hit(r, p99=rng.randint(1800, 3200), err=rng.uniform(50, 80), cpu=rng.randint(30, 50))
    b.action = "failover_dns_resolver"


def c_cascade(b):
    r, c, rng = b.root, b.notes["callee"], b.rng
    b.add(b.t(-180, -140), c, "INFO", "pod restarted (node drain), ready in 12s", None)
    b.add(b.t(-100, -40), r, "WARN", f"retry storm: outbound calls to {c} at {rng.randint(11, 18)}x baseline (retries=5, backoff=0ms, jitter=off)", "ev")
    b.add(b.t(0, 50), r, "ERROR", f"{c} call failed, retrying immediately (attempt 5/5)", "ev")
    b.add(b.t(10, 70), c, "WARN", f"inbound rate from {r} {rng.randint(8000, 12000)} rps (baseline 650): request queue full, shedding", "ev")
    b.add(b.t(60, 120), c, "ERROR", "429 too many requests, queue 1000/1000", None)
    b.symptoms(["upstream {callee} returned HTTP 503 (attempt {k}/3)", "call to {callee} failed: 503 Service Unavailable"])
    b.hit(r, err=min(95, b.E * 1.2), rps=int(rng.randint(300, 700) * 12), cpu=rng.randint(70, 90))
    b.hit(c, err=min(95, b.E * 1.5), cpu=100, p99=rng.randint(2500, 6000), rps=int(rng.randint(500, 3000) * 12))
    b.action = "enable_load_shedding"


# ---------------------------------------------------------------- decoys
def d_cert_soon(b, s):
    b.add(b.rng.randint(60, 700), s, "WARN", f"tls certificate for {s}.internal expires in {b.rng.randint(12, 40)} days (renewal job scheduled)", "decoy")


def d_deploy_ok(b, s):
    t = b.rng.randint(60, b.onset - 350)
    v = b.topo["versions"].get(s, "v1.2.3")
    b.add(t, s, "INFO", f"deploy: rolling out {s} {v} -> {v[:-1]}{(int(v[-1]) + 1) % 10} (build {seeded_hex(b.rng, 7)}) by ci-bot", "decoy")
    b.add(t + 95, s, "INFO", "deploy complete, health checks green, error rate unchanged", "decoy")


def d_disk(b, s):
    b.add(b.rng.randint(60, 1500), s, "WARN", f"disk /var/lib/{s} usage {b.rng.randint(78, 84)}% (alert at 90%)", "decoy")


def d_mem(b, s):
    b.add(b.rng.randint(60, 1500), s, "WARN", f"heap usage {b.rng.randint(80, 85)}% steady for 6h (limit 1536Mi), no restarts", "decoy")


def d_third(b, s):
    b.add(b.rng.randint(60, 700), s, "WARN", "timeout calling geoip-provider (third-party) after 1500ms, using cached value", "decoy")


def d_cfg_ok(b, s):
    b.add(b.rng.randint(60, 900), s, "INFO", "config reload applied: checksum matches repo (rev a4f19c)", "decoy")


def d_cron(b, s):
    b.add(b.rng.randint(30, 500), s, "ERROR", "cron job nightly-cleanup failed: lock held by another run (will retry tomorrow)", "decoy")


def d_restart(b, s):
    b.add(b.rng.randint(60, 700), s, "INFO", "pod restarted (planned node drain), restarts=1, ready in 14s", "decoy")


def d_batch(b, s):
    b.extra.append("etl-nightly")
    b.add(b.rng.randint(60, 600), "etl-nightly", "INFO", f"job nightly-rollup finished on node n9 in 42m, cpu peak 600% (no co-located latency-sensitive pods)", "decoy")


DECOYS = [d_cert_soon, d_deploy_ok, d_disk, d_mem, d_third, d_cfg_ok, d_cron, d_restart, d_batch]

# ---------------------------------------------------------------- noise
GEN_NOISE = [("INFO", "GET /v1/{res} 200 {ms}ms"), ("INFO", "healthcheck ok"), ("INFO", "metrics scrape ok"),
             ("INFO", "cache hit ratio 0.{hit}"), ("INFO", "gc pause {gc}ms"),
             ("WARN", "client disconnected before response (499) path=/v1/{res}"),
             ("WARN", "retry succeeded after {ms}ms"), ("ERROR", "validation failed: field=email invalid format (400, client error)"),
             ("INFO", "POST /v1/{res} 201 {ms}ms")]
DATA_NOISE = [("INFO", "checkpoint complete"), ("INFO", "connections {n}/500"), ("INFO", "background compaction finished in {ms}ms"),
              ("INFO", "metrics scrape ok"), ("WARN", "client disconnected unexpectedly")]
DNS_NOISE = [("INFO", "cache hit ratio 0.{hit}"), ("INFO", "queries {n}/s"), ("INFO", "metrics scrape ok")]


def noise(b, svc, tier, n):
    rng = b.rng
    pool = DATA_NOISE if tier == "data" else DNS_NOISE if tier == "dns" else GEN_NOISE
    for _ in range(n):
        lvl, tmpl = rng.choice(pool)
        b.add(rng.randint(1, WINDOW - 5), svc, lvl, tmpl.format(
            res=rng.choice(["items", "cart", "orders", "users", "quotes", "sessions"]), ms=rng.randint(4, 90),
            hit=rng.randint(80, 97), gc=rng.randint(5, 40), n=rng.randint(20, 400)))


# ---------------------------------------------------------------- build one scenario
def build_scenario(seed, diff, category, variant=None):
    rng = random.Random(seed)
    topo = build_topology(rng, diff)
    sev = rng.choice(SEVERITIES)
    b = B(rng, topo, diff, category, sev)
    front, back, data = topo["front"], topo["back"], topo["data"]
    tier = dict(topo["tier"])
    services = list(topo["services"])
    dns_name = rng.choice(DNS)
    if category == "resource_exhaustion":
        b.variant = variant or rng.choice(["mem", "fd", "cpu", "disk"])
        pool = {"mem": front + back + data, "fd": front + back, "cpu": front + back, "disk": back + data}[b.variant]
        b.root = rng.choice(pool)
        b.anc = ancestors(topo, b.root)
        fn = c_resource
    elif category == "dependency_timeout":
        b.root = rng.choice(back + data)
        b.anc, fn = ancestors(topo, b.root), c_dep_timeout
    elif category in ("bad_deploy", "config_drift", "certificate_expiry"):
        b.root = rng.choice(front + back)
        b.anc = ancestors(topo, b.root)
        fn = {"bad_deploy": c_bad_deploy, "config_drift": c_config, "certificate_expiry": c_cert}[category]
    elif category == "noisy_neighbor":
        v = rng.choice(back + data)
        r = rng.choice(BATCH)
        b.root, b.notes["victim"] = r, v
        services.append(r)
        tier[r] = "batch"
        topo["nodes"][r] = topo["nodes"][v]
        b.anc = ancestors(topo, v)
        b.victims = [v]
        fn = c_noisy
    elif category == "dns_failure":
        b.root = dns_name
        services.append(dns_name)
        tier[dns_name] = "dns"
        b.anc = [(s, topo["calls"][s][0]) for s in topo["services"] if topo["calls"].get(s)]
        fn = c_dns
    else:  # cascading_failure
        b.root = rng.choice(front + back)
        c = rng.choice([x for x in topo["calls"][b.root]])
        b.notes["callee"] = c
        b.anc = ancestors(topo, b.root)
        b.victims = [c]
        fn = c_cascade
    if category != "dns_failure" and diff != "easy":
        services.append(dns_name)
        tier[dns_name] = "dns"
    fn(b)
    # decoys
    cands = [s for s in services if s != b.root and tier[s] != "dns" and s != EDGE] or [EDGE]
    kinds = rng.sample(DECOYS, N_DECOYS[diff])
    for k in kinds:
        k(b, rng.choice(cands))
    for s in b.extra:
        if s not in services:
            services.append(s)
            tier[s] = "batch"
    # edge symptom lines and noise
    if category != "dns_failure" or True:
        b.add(b.t(15, 200), EDGE, "ERROR", f"5xx ratio {b.E}% over 1m (SLO 99.9%): upstream {b.anc[-1][1] if b.anc and b.anc[-1][0] == EDGE else b.root} failing", None)
    for s in services:
        noise(b, s, tier[s], N_NOISE[diff] + rng.randint(-2, 2))
    # decoy metric
    if diff != "easy":
        victims_all = {a for a, _ in b.anc} | {b.root} | set(b.victims)
        quiet = [s for s in services if s not in victims_all and tier[s] not in ("dns", "batch")]
        if quiet:
            s = rng.choice(quiet)
            b.hit(s, **rng.choice([dict(cpu=rng.randint(70, 79)), dict(mem=rng.randint(78, 84))]))
    return finalize(b, services, tier, diff, category)


def finalize(b, services, tier, diff, category):
    rng = b.rng
    lines = sorted(b.lines, key=lambda l: (l["t"], l["n"]))
    for i, l in enumerate(lines, 1):
        l["id"] = "L%03d" % i
    # metrics
    snaps = [WINDOW - 600, WINDOW - 300, WINDOW]
    base = {}
    for s in services:
        lo = BASE_METRIC[tier[s]]
        base[s] = dict(rps=rng.randint(lo[0], lo[1]), p99=rng.randint(lo[2], lo[3]), cpu=rng.randint(lo[4], lo[5]),
                       mem=rng.randint(lo[6], lo[7]), err=round(rng.uniform(0.1, 0.5), 1))
    victims = [a for a, _ in b.anc] + list(b.victims)
    for a in victims:
        o = b.over.setdefault(a, {})
        if a == EDGE:
            o["err"] = b.E
        o.setdefault("err", min(95, b.E * rng.uniform(0.8, 1.4)))
        if b.category in ("dependency_timeout", "noisy_neighbor"):
            o.setdefault("p99", rng.randint(2800, 3600))
        else:
            o.setdefault("p99", int(base[a]["p99"] * rng.uniform(3, 9)))
    b.over.setdefault(EDGE, {})["err"] = b.E
    now = {}
    for s in services:
        v = dict(base[s])
        v.update(b.over.get(s, {}))
        now[s] = v
    tables = []
    for si, t in enumerate(snaps):
        f = [0.0, 0.45, 1.0][si]
        rows = []
        for s in services:
            row = {}
            for k in ("err", "p99", "cpu", "mem", "rps"):
                val = base[s][k] + (now[s][k] - base[s][k]) * f
                if si < 2:
                    val *= 1 + rng.uniform(-0.04, 0.04) if k != "err" else 1
                row[k] = val
            rows.append((s, row))
        hdr = "== metrics @ %s (T-%dm) ==" % (iso(b.base + t)[11:], (WINDOW - t) // 60) if t != WINDOW else "== metrics @ %s (now) ==" % iso(b.base + t)[11:]
        txt = [hdr, "%-18s %7s %7s %7s %7s %7s" % ("service", "err_pct", "p99_ms", "cpu_pct", "mem_pct", "rps")]
        for s, r in rows:
            txt.append("%-18s %7.1f %7d %7.0f %7.0f %7d" % (s, r["err"], r["p99"], r["cpu"], r["mem"], r["rps"]))
        tables.append("\n".join(txt))
    # the sev is defined from the *printed* edge error in the last snapshot
    e_now = round(now[EDGE]["err"], 1)
    sev = sev_of(e_now)
    assert sev == b.sev, (sev, b.sev, e_now)
    log_txt = "\n".join("[%s] %s %-18s %-5s %s" % (l["id"], iso(b.base + l["t"])[11:], l["svc"], l["lvl"], l["msg"]) for l in lines)
    ev = [l["id"] for l in lines if l["tag"] == "ev"]
    decoy = [l["id"] for l in lines if l["tag"] == "decoy"]
    assert len(ev) >= 3 and not (set(ev) & set(decoy))
    ref = dict(root_cause_service=b.root, root_cause_category=category, evidence_line_ids=ev[:3],
               first_safe_action=b.action, severity=sev)
    prompt = triage_prompt(iso(b.base)[:10], iso(b.base + WINDOW), log_txt, "\n\n".join(tables), len(lines))
    return dict(prompt=prompt, ref=ref, ev=ev, decoy=decoy, nlines=len(lines), services=services, variant=b.variant,
                logs=log_txt, metrics="\n\n".join(tables))


DEFS = """Root-cause categories (choose exactly one):
- bad_deploy: a release of the root service started shortly before the errors began and the new version throws new exceptions.
- resource_exhaustion: the root service itself ran out of memory, file descriptors, disk, or cpu (traffic growth), with no deploy involved.
- dependency_timeout: the root service is a dependency that became slow (lock contention, slow queries, slow backend); its callers time out.
- config_drift: a runtime configuration value on the root service differs from the version in git (manual edit, no new version deployed).
- certificate_expiry: the root service's TLS certificate expired; callers fail TLS verification.
- noisy_neighbor: a co-located workload (the root service) on the same node starves another service of cpu.
- dns_failure: the cluster DNS service (the root service) is failing to resolve names.
- cascading_failure: the root service amplifies a brief blip of a dependency with unbounded retries (retry storm) and keeps that dependency down.

first_safe_action (choose exactly one): rollback_deploy | restart_service (memory or file-descriptor exhaustion) | scale_out (cpu saturation from traffic growth) | free_disk_space | enable_circuit_breaker (slow dependency) | revert_config | renew_certificate | evict_noisy_workload | failover_dns_resolver | enable_load_shedding (retry storm / overload).

severity (from the api-gateway error_pct in the latest "now" metrics snapshot): sev1 if >= 25, sev2 if >= 10, sev3 if >= 2, otherwise sev4."""


def triage_prompt(date, end, logs, metrics, n):
    return f"""You are the on-call SRE. An alert fired: api-gateway 5xx ratio above SLO. Below are the multi-service logs for the last 30 minutes (UTC, {date}, ending {end}) and three metric snapshots. Find the root cause. Beware of red herrings: some warnings in the logs are unrelated to this incident, and the service with the most errors is not necessarily the root cause.

{DEFS}

evidence_line_ids: 2 to 5 log line ids (e.g. "L042") that directly prove the root cause; do not cite unrelated lines.

=== LOGS ({n} lines) ===
{logs}

{metrics}

Answer with exactly one JSON object and nothing else:
{{"root_cause_service": "<service name>", "root_cause_category": "<category>", "evidence_line_ids": ["L000", "L000"], "first_safe_action": "<action>", "severity": "sev1|sev2|sev3|sev4"}}"""


def make_triage(seed, diff, category, variant=None):
    sc = build_scenario(seed, diff, category, variant)
    return dict(inputs=dict(prompt=sc["prompt"], categories=CATEGORIES, actions=ACTIONS, severities=SEVERITIES),
                hidden=dict(root_cause_service=sc["ref"]["root_cause_service"], root_cause_category=category,
                            evidence_ok_ids=sc["ev"], decoy_ids=sc["decoy"], n_lines=sc["nlines"],
                            first_safe_action=sc["ref"]["first_safe_action"], severity=sc["ref"]["severity"],
                            variant=sc["variant"], min_evidence_hits=2, max_evidence=5),
                reference_answer=json.dumps(sc["ref"]))
