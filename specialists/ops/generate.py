"""Materialize tasks.jsonl deterministically:  python generate.py [--out tasks.jsonl]"""
import argparse
import json
import os

import fixtasks
import runbooks
import scenarios
import scripttasks
import slo

HERE = os.path.dirname(os.path.abspath(__file__))
TIERS = [("easy", "e"), ("medium", "m"), ("hard", "h")]
SEED_BASE = {"triage": 100000, "script": 200000, "slo": 300000, "runbook": 400000, "fix": 500000}

SCRIPT_PLAN = {
    "easy": [("counts", "kv"), ("counts", "kv"), ("counts", "json"), ("counts", "text"), ("counts", "kv"),
             ("percentiles", "kv"), ("percentiles", "kv"), ("percentiles", "json"), ("percentiles", "text"), ("percentiles", "kv")],
    "medium": [("windows", "kv"), ("windows", "json"), ("windows", "text"), ("topmsgs", "kv"), ("topmsgs", "json"), ("topmsgs", "text"),
               ("percentiles", "json"), ("percentiles", "text"), ("counts", "text"), ("counts", "json")],
    "hard": [("burn", "kv"), ("burn", "json"), ("burn", "text"), ("burn", "kv"), ("incidents", "kv"), ("incidents", "json"),
             ("incidents", "text"), ("incidents", "json"), ("windows", "json"), ("windows", "text")],
}
SLO_PLAN = {"easy": ["budget"] * 5 + ["burn"] * 5, "medium": ["thresholds"] * 4 + ["policy"] * 3 + ["avail"] * 3,
            "hard": ["capacity"] * 4 + ["hist"] * 3 + ["burn2"] * 3}
N_TRIAGE, N_RUNBOOK, N_FIX = 22, 8, 8


def build():
    tasks = []

    def add(kind, diff, tag, idx, body, extra=None):
        tid = f"ops-{kind}-{tag}-{idx:03d}"
        tasks.append(dict(id=tid, kind=kind, difficulty=diff, seed=body.pop("_seed"), **body))

    for diff, tag in TIERS:
        di = {"easy": 0, "medium": 1, "hard": 2}[diff]
        for i in range(N_TRIAGE):
            seed = SEED_BASE["triage"] + di * 1000 + i
            cat = scenarios.CATEGORIES[(i + di) % 8]
            variant = ["mem", "fd", "cpu", "disk"][(i // 8 + i) % 4] if cat == "resource_exhaustion" else None
            b = scenarios.make_triage(seed, diff, cat, variant)
            b["_seed"] = seed
            add("triage", diff, tag, i + 1, b)
        for i, (tt, fmt) in enumerate(SCRIPT_PLAN[diff]):
            seed = SEED_BASE["script"] + di * 1000 + i
            b = scripttasks.make_script(seed, diff, tt, fmt)
            b["_seed"] = seed
            add("script", diff, tag, i + 1, b)
        for i, st in enumerate(SLO_PLAN[diff]):
            seed = SEED_BASE["slo"] + di * 1000 + i
            b = slo.make_slo(seed, st)
            b["_seed"] = seed
            add("slo", diff, tag, i + 1, b)
        topics = sorted(runbooks.TOPICS)
        for i in range(N_RUNBOOK):
            seed = SEED_BASE["runbook"] + di * 1000 + i
            b = runbooks.make_runbook(seed, diff, topics[(i + di) % len(topics)])
            b["_seed"] = seed
            add("runbook", diff, tag, i + 1, b)
        for i in range(N_FIX):
            seed = SEED_BASE["fix"] + di * 1000 + i
            b = fixtasks.make_fix(seed, diff)
            b["_seed"] = seed
            add("fix", diff, tag, i + 1, b)
    for t in tasks:  # normalise field order
        t["grader"] = {"triage": "graders.grade_triage", "script": "graders.grade_code[analyze.py]", "slo": "graders.grade_slo",
                       "runbook": "graders.grade_runbook", "fix": "graders.grade_code[oncall.py]"}[t["kind"]]
    return tasks


def dump(tasks):
    return "".join(json.dumps(t, sort_keys=False, separators=(",", ":")) + "\n" for t in tasks)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "tasks.jsonl"))
    a = ap.parse_args()
    ts = build()
    open(a.out, "w").write(dump(ts))
    from collections import Counter
    print(len(ts), "tasks ->", a.out)
    print(dict(Counter(t["kind"] for t in ts)), dict(Counter(t["difficulty"] for t in ts)))
