#!/usr/bin/env python3
"""Validate tasks.jsonl: for every task the START STATE must FAIL and the REFERENCE must PASS (grading inside the locked-down container).
Extra self-checks of the grader: reference wrapped in a markdown fence passes; for order-insensitive SQL tasks a re-ordered reference passes.
One container, jobs streamed over stdin. Exit code 0 only if everything holds."""
import collections
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = "python:3.12-slim"


def fence(task, code):
    lang = {"etl": "python"}.get(task["kind"], "sql")
    return f"Here is my answer.\n```{lang}\n{code}\n```\nHope it helps."


def main():
    tasks = [json.loads(l) for l in (HERE / "tasks.jsonl").read_text().splitlines() if l.strip()]
    jobs, expect = [], {}

    def add(t, label, answer, want):
        jid = f"{t['id']}#{label}"
        jobs.append({"job_id": jid, "task": t, "answer": answer})
        expect[jid] = want

    for t in tasks:
        add(t, "start", t["start_state"], False)
        add(t, "reference", t["reference"], True)
        add(t, "reference-fenced", fence(t, t["reference"]), True)
        if t["kind"] in ("sql_write", "sql_fix") and not t["check"]["ordered"]:
            add(t, "reordered", f"SELECT * FROM ({t['reference'].rstrip().rstrip(';')}) ORDER BY 1 DESC", True)
        if t["kind"] in ("sql_write", "sql_fix"):
            add(t, "wrong-empty", f"SELECT * FROM ({t['reference'].rstrip().rstrip(';')}) WHERE 0", False)
    payload = "\n".join(json.dumps(j) for j in jobs) + "\n"
    cmd = ["docker", "run", "--rm", "-i", "--name", "tc-data-validate", "--network", "none", "--memory", "256m", "--cpus", "1",
           "--pids-limit", "64", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
           "-v", f"{HERE}:/g:ro", "-w", "/g", IMAGE, "python", "-c", "import sqlite3,sys;print('container: python',sys.version.split()[0],'sqlite',sqlite3.sqlite_version,file=sys.stderr);sys.path.insert(0,'/g');sys.dont_write_bytecode=True;import grader;grader.main()"]
    p = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=1500)
    sys.stderr.write(p.stderr)
    res = {}
    for line in p.stdout.splitlines():
        r = json.loads(line)
        res[r["job_id"]] = r
    bad = []
    stats = collections.defaultdict(lambda: collections.Counter())
    by_id = {t["id"]: t for t in tasks}
    for jid, want in expect.items():
        r = res.get(jid)
        tid, label = jid.split("#")
        t = by_id[tid]
        ok = r is not None and r["pass"] == want
        stats[(t["kind"], label)]["ok" if ok else "BAD"] += 1
        if not ok:
            bad.append((jid, want, r))
    print(f"{'kind':<10} {'check':<18} ok/total")
    for (k, label), c in sorted(stats.items()):
        print(f"{k:<10} {label:<18} {c['ok']}/{c['ok'] + c['BAD']}")
    print()
    kd = collections.Counter((t["kind"], t["difficulty"]) for t in tasks)
    kinds = sorted({t["kind"] for t in tasks})
    print("tasks per kind/difficulty:")
    for k in kinds:
        print(f"  {k:<10} easy={kd[(k, 'easy')]:<3} medium={kd[(k, 'medium')]:<3} hard={kd[(k, 'hard')]:<3} total={sum(kd[(k, d)] for d in ('easy', 'medium', 'hard'))}")
    print(f"  TOTAL {len(tasks)}")
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        bad.append(("duplicate ids", None, None))
    if bad:
        print(f"\nFAILURES ({len(bad)}):")
        for jid, want, r in bad[:40]:
            print(f"  {jid}: wanted pass={want}, got {r}")
        sys.exit(1)
    print("\nVALIDATION OK: every start state fails, every reference passes, grader self-checks hold.")


if __name__ == "__main__":
    main()
