"""Kind `runbook`: pick the applicable runbook steps, in the order the runbook's prerequisites and ID tie-break rule dictate."""
import heapq
import json
import random

FACTS = {
    "primary_reachable": ("the primary database is reachable", "bool"),
    "replica_lag_s": ("replication lag of the freshest replica (seconds)", "num", (2, 120)),
    "recent_migration": ("a schema migration shipped in the last 24h", "bool"),
    "impact": ("customer impact level", "enum", ["high", "low"]),
    "deploy_age_min": ("age of the suspect release (minutes)", "num", (10, 300)),
    "canary_available": ("a canary slice is serving the new release", "bool"),
    "db_migration_in_release": ("the suspect release included a database migration", "bool"),
    "error_rate_pct": ("api error rate (percent)", "num", (1, 60)),
    "cert_managed_by_acme": ("the certificate is managed by ACME auto-renewal", "bool"),
    "wildcard_cert": ("the certificate is a wildcard shared by several services", "bool"),
    "load_balancer_terminates": ("TLS is terminated at the load balancer", "bool"),
    "security_exception_approved": ("a signed security exception exists for disabling TLS verification", "bool"),
    "logs_dominant": ("log files are the largest consumer of the full disk", "bool"),
    "filesystem_is_lvm": ("the full filesystem sits on LVM", "bool"),
    "data_dir_is_database": ("the full filesystem holds a database data directory", "bool"),
    "free_pct": ("free space on the disk (percent)", "num", (1, 30)),
    "service_crashed": ("the service crashed with ENOSPC", "bool"),
    "lag_growing": ("consumer lag is still growing", "bool"),
    "consumers_healthy": ("all consumer pods are Running and Ready", "bool"),
    "poison_message": ("a single poison message is blocking a partition", "bool"),
    "producer_burst": ("a producer burst caused the lag", "bool"),
    "coredns_pods_ready": ("all CoreDNS pods are Ready", "bool"),
    "upstream_resolver_reachable": ("the upstream resolver answers queries", "bool"),
    "recent_corefile_change": ("the Corefile was changed in the last hour", "bool"),
    "severity": ("incident severity (1 = worst, 4 = mildest)", "num", (1, 4)),
    "business_hours": ("it is currently business hours", "bool"),
    "customer_data_at_risk": ("customer data may be exposed", "bool"),
    "deploy_freeze_active": ("a change freeze is active", "bool"),
}
A, N = ["always"], None


def IS(k, v=True):
    return ["is", k, v]


def AND(*c):
    return c[0] if len(c) == 1 else ["and"] + list(c)


TOPICS = {
    "Database primary failover": [
        ("a", "Open an incident channel and page the database on-call.", A, []),
        ("b", "Freeze deploys and schema migrations.", A, ["a"]),
        ("c", "Confirm the primary is really down with pg_isready from two hosts.", IS("primary_reachable", False), ["a"]),
        ("d", "Record replication lag on every replica.", A, ["a"]),
        ("e", "Promote the most up-to-date replica.", AND(IS("primary_reachable", False), ["le", "replica_lag_s", 30]), ["c", "d"]),
        ("f", "Escalate to the data lead for a data-loss decision instead of promoting.", AND(IS("primary_reachable", False), ["gt", "replica_lag_s", 30]), ["c", "d"]),
        ("g", "Repoint application connection strings to the new primary.", AND(IS("primary_reachable", False), ["le", "replica_lag_s", 30]), ["e"]),
        ("h", "Revert the latest schema migration.", IS("recent_migration"), ["b"]),
        ("i", "Run the synthetic checkout transaction and confirm it succeeds.", A, ["d", "g", "h"]),
        ("j", "Post a customer-facing status page update.", ["eq", "impact", "high"], ["a"]),
        ("k", "Schedule the postmortem.", A, ["i"])],
    "Bad deploy rollback": [
        ("a", "Declare the incident and assign an incident commander.", A, []),
        ("b", "Pause the deploy pipeline for all services.", A, ["a"]),
        ("c", "Identify the suspect release from the deploy log.", A, ["a"]),
        ("d", "Shift canary traffic back to 0%.", IS("canary_available"), ["c"]),
        ("e", "Roll back the release to the previous version.", AND(IS("canary_available", False), ["le", "deploy_age_min", 120]), ["b", "c", "f"]),
        ("f", "Run the down-migration script before rolling back.", IS("db_migration_in_release"), ["c"]),
        ("g", "Do not roll back; ship a forward fix instead (release is older than 2 hours).", AND(IS("canary_available", False), ["gt", "deploy_age_min", 120]), ["c"]),
        ("h", "Verify the error rate is back under 1%.", A, ["d", "e", "g"]),
        ("i", "Unpause the deploy pipeline.", A, ["h"]),
        ("j", "Notify support leads about customer impact.", ["gt", "error_rate_pct", 20], ["a"])],
    "Certificate expiry": [
        ("a", "Page the platform on-call and open an incident.", A, []),
        ("b", "Identify every host serving the expired certificate with openssl s_client.", A, ["a"]),
        ("c", "Trigger ACME renewal for the certificate.", IS("cert_managed_by_acme"), ["b"]),
        ("d", "Issue a replacement certificate manually from the internal CA.", IS("cert_managed_by_acme", False), ["b"]),
        ("e", "Re-issue the wildcard certificate and update the secret of every dependent service.", IS("wildcard_cert"), ["c", "d"]),
        ("f", "Install the new certificate on the load balancer.", IS("load_balancer_terminates"), ["c", "d", "e"]),
        ("g", "Rolling-restart the services that terminate TLS themselves.", IS("load_balancer_terminates", False), ["c", "d", "e"]),
        ("h", "Verify the chain with openssl s_client from outside the cluster.", A, ["f", "g"]),
        ("i", "Disable TLS verification on callers as a stopgap.", IS("security_exception_approved"), ["b"]),
        ("j", "Add a certificate-expiry alert at 21 days.", A, ["h"])],
    "Disk full": [
        ("a", "Open an incident and notify the service owner.", A, []),
        ("b", "Find the largest directories with du -xh.", A, ["a"]),
        ("c", "Rotate and compress oversized logs.", IS("logs_dominant"), ["b"]),
        ("d", "Delete logs older than 7 days after confirming they are shipped to central logging.", IS("logs_dominant"), ["c"]),
        ("e", "Expand the volume with lvextend and resize the filesystem.", AND(IS("logs_dominant", False), IS("filesystem_is_lvm")), ["b", "g"]),
        ("f", "Request a larger cloud disk and schedule a resize.", AND(IS("logs_dominant", False), IS("filesystem_is_lvm", False)), ["b", "g"]),
        ("g", "Stop writes to the database before touching its data directory.", AND(IS("data_dir_is_database"), IS("logs_dominant", False)), ["b"]),
        ("h", "Confirm free space is above 20%.", A, ["c", "d", "e", "f"]),
        ("i", "Raise the disk-usage alert to page at 85%.", ["le", "free_pct", 10], ["h"]),
        ("j", "Restart the affected service.", IS("service_crashed"), ["h"])],
    "Kafka consumer lag": [
        ("a", "Notify the data-platform on-call.", A, []),
        ("b", "Check per-partition lag with kafka-consumer-groups.", A, ["a"]),
        ("c", "Save the poison message to the dead-letter topic and skip it.", IS("poison_message"), ["b"]),
        ("d", "Restart the stuck consumer pods.", AND(IS("consumers_healthy", False), IS("poison_message", False)), ["b"]),
        ("e", "Scale consumers up to the partition count.", AND(IS("consumers_healthy"), IS("lag_growing"), IS("poison_message", False)), ["b"]),
        ("f", "Throttle the upstream producer.", IS("producer_burst"), ["b"]),
        ("g", "Verify lag is decreasing for 10 minutes.", A, ["c", "d", "e", "f"]),
        ("h", "Remove the producer throttle.", IS("producer_burst"), ["g"]),
        ("i", "Add a lag-age alert, not only a lag-count alert.", A, ["g"])],
    "DNS resolution failures": [
        ("a", "Declare an incident and page network on-call.", A, []),
        ("b", "Run dig against CoreDNS and against the upstream resolver directly to isolate the failing hop.", A, ["a"]),
        ("c", "Roll back the last Corefile change.", IS("recent_corefile_change"), ["b"]),
        ("d", "Restart the CoreDNS pods.", IS("coredns_pods_ready", False), ["b", "c"]),
        ("e", "Switch forwarders to the secondary upstream resolver.", IS("upstream_resolver_reachable", False), ["b"]),
        ("f", "Flush the CoreDNS cache.", A, ["c", "d", "e"]),
        ("g", "Resolve one internal and one external name from a test pod.", A, ["f"]),
        ("h", "Open a ticket with the DNS provider.", IS("upstream_resolver_reachable", False), ["e"])],
}
GLOBALS = [
    ("G1", "Page the incident commander.", ["le", "severity", 2], ["a"]),
    ("G2", "Call the secondary on-call by phone.", IS("business_hours", False), ["a"]),
    ("G3", "Notify the security team and legal.", IS("customer_data_at_risk"), ["a"]),
    ("G4", "Request emergency change approval before touching production.", IS("deploy_freeze_active"), ["a"]),
]


def holds(c, f):
    t = c[0]
    if t == "always":
        return True
    if t == "is":
        return f[c[1]] is c[2]
    if t == "eq":
        return f[c[1]] == c[2]
    if t == "gt":
        return f[c[1]] > c[2]
    if t == "le":
        return f[c[1]] <= c[2]
    if t == "and":
        return all(holds(x, f) for x in c[1:])
    raise ValueError(t)


def cond_text(c):
    t = c[0]
    if t == "always":
        return "always applies"
    d = lambda k: FACTS[k][0]
    if t == "is":
        return f"applies only if [{d(c[1])}] is {'yes' if c[2] else 'no'}"
    if t == "eq":
        return f"applies only if [{d(c[1])}] is '{c[2]}'"
    if t == "gt":
        return f"applies only if [{d(c[1])}] is greater than {c[2]}"
    if t == "le":
        return f"applies only if [{d(c[1])}] is at most {c[2]}"
    return "applies only if " + " AND ".join(cond_text(x).replace("applies only if ", "") for x in c[1:])


def thresholds(c, out):
    if c[0] in ("gt", "le"):
        out.setdefault(c[1], []).append(c[2])
    if c[0] == "and":
        for x in c[1:]:
            thresholds(x, out)


def order(steps, facts):
    """steps: list of dict(id, cond, req). Lexicographically smallest topological order of applicable steps."""
    app = {s["id"]: s for s in steps if holds(s["cond"], facts)}
    indeg = {i: sum(1 for r in s["req"] if r in app) for i, s in app.items()}
    ready = [i for i, d in indeg.items() if d == 0]
    heapq.heapify(ready)
    out = []
    while ready:
        i = heapq.heappop(ready)
        out.append(i)
        for j, s in app.items():
            if i in s["req"]:
                indeg[j] -= 1
                if indeg[j] == 0:
                    heapq.heappush(ready, j)
    assert len(out) == len(app)
    return out


def make_runbook(seed, diff, topic=None):
    rng = random.Random(seed)
    topic = topic or rng.choice(sorted(TOPICS))
    base = list(TOPICS[topic])
    if diff == "easy":
        keep = {"a"} | set(rng.sample([s[0] for s in base[1:]], 6))
        base = [s for s in base if s[0] in keep]
    glob = rng.sample(GLOBALS, {"easy": 0, "medium": 1, "hard": 3}[diff])
    raw = [(k, t, c, r) for k, t, c, r in base] + [(k, t, c, r) for k, t, c, r in glob]
    ids = sorted(rng.sample(range(10, 100), len(raw)))
    perm = list(range(len(raw)))
    rng.shuffle(perm)
    key2id = {raw[i][0]: "R%02d" % ids[perm[n]] for n, i in enumerate(range(len(raw)))}
    steps = [dict(id=key2id[k], key=k, text=t, cond=c, req=[key2id[x] for x in r if x in key2id]) for k, t, c, r in raw]
    steps.sort(key=lambda s: s["id"])
    th = {}
    for s in steps:
        thresholds(s["cond"], th)
    used = []
    for s in steps:
        for k in _cond_keys(s["cond"]):
            if k not in used:
                used.append(k)
    for _ in range(300):
        facts = {}
        for k in used:
            spec = FACTS[k]
            if spec[1] == "bool":
                facts[k] = rng.random() < 0.5
            elif spec[1] == "enum":
                facts[k] = rng.choice(spec[2])
            else:
                lo, hi = spec[2]
                facts[k] = rng.randint(lo, hi)
        if all(abs(facts[k] - t) >= (0 if k == "severity" else 5) for k, ts in th.items() for t in ts):
            n_app = sum(holds(s["cond"], facts) for s in steps)
            if len(steps) * 0.45 <= n_app <= len(steps) * 0.85:
                break
    ans = order(steps, facts)
    fact_txt = "\n".join(f"- {FACTS[k][0]}: " + (("yes" if facts[k] else "no") if FACTS[k][1] == "bool" else str(facts[k])) for k in used)
    step_txt = "\n".join(f"{s['id']}: {s['text']}\n    [{cond_text(s['cond'])}; prerequisites: {', '.join(s['req']) if s['req'] else 'none'}]" for s in steps)
    prompt = (f"You are on call and following the runbook \"{topic}\". Decide which steps apply to this incident and in which order to run them.\n\n"
              f"Incident facts:\n{fact_txt}\n\nRunbook steps (listed by ID, not in execution order):\n{step_txt}\n\n"
              "Rules:\n1. Run only steps whose applicability condition holds for the facts above.\n"
              "2. A step runs only after all of its prerequisites that are themselves selected have run (prerequisites that are not selected are ignored).\n"
              "3. Whenever several selected steps are ready at the same time, run the one with the smallest ID first (compare IDs as strings).\n\n"
              'Answer with exactly one JSON object and nothing else: {"steps": ["R00", "R00", ...]} listing the selected step IDs in execution order.')
    return dict(inputs=dict(prompt=prompt, topic=topic, facts=facts, steps=[{k: v for k, v in s.items() if k != "key"} for s in steps]),
                hidden=dict(steps=ans), reference_answer=json.dumps({"steps": ans}))


def _cond_keys(c):
    if c[0] == "always":
        return []
    if c[0] == "and":
        return [k for x in c[1:] for k in _cond_keys(x)]
    return [c[1]]
