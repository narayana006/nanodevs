"""Prove the task set is sound: schema, determinism, reference answers pass, trivial/empty/random/near-miss answers fail.
  python validate.py            code-task execution on the host (fast; only trusted reference/negative code)
  python validate.py --docker   code tasks executed one at a time in the locked-down python:3.12-slim container
Exit status 1 on any violation."""
import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict

import fixtasks
import generate
import graders
import scripttasks

HERE = os.path.dirname(os.path.abspath(__file__))
REQ = ["id", "kind", "difficulty", "seed", "inputs", "hidden", "reference_answer", "grader"]
GENERIC_BAD = ["", "I do not know.", "{}", "[]", "```python\n```", "```json\n{}\n```"]

MUTANTS = {
    "counts": [('"malformed": bad', '"malformed": 0'), ('"total": len(rows)', '"total": len(rows) + bad')],
    "percentiles": [("v[-(-p * n // 100) - 1]", "v[max(0, p * n // 100 - 1)]"), ("v.sort()", "pass")],
    "windows": [("> thr]", ">= thr]"), ('r["status"] >= 500', 'r["status"] > 500'), ('k = r["ts"] // ws * ws', 'k = (r["ts"] - 1) // ws * ws')],
    "burn": [('now - secs < r["ts"] <= now', 'now - secs <= r["ts"] <= now'), ("1 - slo / 100.0", "1 - slo / 100.0 + 0.0001"), ('(burn["5m"] >= 14.4 and burn["1h"] >= 14.4)', '(burn["5m"] >= 14.4 or burn["1h"] >= 14.4)')],
    "incidents": [("t - cur[1] <= gap", "t - cur[1] < gap"), ("if c[2] >= 2", "if c[2] >= 1")],
    "topmsgs": [('r["msg"].lower()', 'r["msg"]'), ("[:k]", "[:k + 1]"), ('r["lvl"] in ("ERROR", "WARN")', 'r["lvl"] == "ERROR"')],
}


class Report:
    def __init__(self):
        self.fail, self.lines, self.checks = [], [], Counter()

    def check(self, cond, what, tid=""):
        self.checks[what.split(":")[0]] += 1
        if not cond:
            self.fail.append(f"{tid} {what}")
        return cond


def services_in(task):
    return sorted(set(re.findall(r"^([a-z][a-z0-9-]+)\s+[\d.]+\s", task["inputs"]["prompt"], re.M)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docker", action="store_true")
    ap.add_argument("--tasks", default=os.path.join(HERE, "tasks.jsonl"))
    a = ap.parse_args()
    sb = "docker" if a.docker else "local"
    R = Report()
    t0 = time.time()
    raw = open(a.tasks).read()
    tasks = [json.loads(l) for l in raw.splitlines()]
    byid = {t["id"]: t for t in tasks}
    R.check(len(byid) == len(tasks), "schema: unique ids")
    R.check(len(tasks) >= 150, "schema: >=150 tasks")
    for t in tasks:
        R.check(all(k in t for k in REQ), "schema: required fields", t["id"])
        R.check(t["difficulty"] in ("easy", "medium", "hard") and isinstance(t["reference_answer"], str) and t["inputs"].get("prompt"), "schema: field values", t["id"])
    print("tasks:", len(tasks), dict(Counter(t["kind"] for t in tasks)), dict(Counter(t["difficulty"] for t in tasks)))

    # determinism
    R.check(generate.dump(generate.build()) == raw, "determinism: regenerated tasks.jsonl is byte-identical")

    rnd = random.Random(2026)
    stats = defaultdict(lambda: Counter())
    for t in tasks:
        k, tid = t["kind"], t["id"]
        g = lambda ans: graders.grade(t, ans, sb)
        ref = g(t["reference_answer"])
        R.check(ref["pass"] and ref["score"] == 1.0, "reference passes", tid)
        stats[k]["ref_pass"] += ref["pass"]
        for bad in GENERIC_BAD:
            r = g(bad) if k in ("triage", "slo", "runbook") or bad in ("", "I do not know.") else g(bad)
            R.check(not r["pass"], f"trivial answer fails ({bad[:12]!r})", tid)
            stats[k]["trivial_fail"] += not r["pass"]
            stats[k]["trivial_n"] += 1
        if k == "triage":
            h, ref_o = t["hidden"], json.loads(t["reference_answer"])
            svcs = services_in(t)
            R.check(h["root_cause_service"] in svcs, "triage: root service appears in metrics table", tid)
            R.check(len(h["evidence_ok_ids"]) >= 3 and not set(h["evidence_ok_ids"]) & set(h["decoy_ids"]), "triage: evidence/decoy sane", tid)
            for _ in range(20):
                o = dict(root_cause_service=rnd.choice(svcs), root_cause_category=rnd.choice(t["inputs"]["categories"]),
                         evidence_line_ids=["L%03d" % rnd.randint(1, h["n_lines"]) for _ in range(rnd.randint(2, 4))],
                         first_safe_action=rnd.choice(t["inputs"]["actions"]), severity=rnd.choice(t["inputs"]["severities"]))
                r = g(json.dumps(o))
                stats[k]["rand_n"] += 1
                stats[k]["rand_pass"] += r["pass"]
                R.check(not r["pass"], "random answer fails", tid)
            for f, alt in [("root_cause_service", "api-gateway" if h["root_cause_service"] != "api-gateway" else "checkout"),
                           ("root_cause_category", "bad_deploy" if h["root_cause_category"] != "bad_deploy" else "config_drift"),
                           ("first_safe_action", "rollback_deploy" if h["first_safe_action"] != "rollback_deploy" else "revert_config"),
                           ("severity", "sev1" if h["severity"] != "sev1" else "sev4")]:
                r = g(json.dumps({**ref_o, f: alt}))
                R.check(not r["pass"] and abs(r["score"] - 0.8) < 1e-9, f"near-miss ({f}) fails with field score", tid)
            if h["decoy_ids"]:
                R.check(not g(json.dumps({**ref_o, "evidence_line_ids": ref_o["evidence_line_ids"][:2] + [h["decoy_ids"][0]]}))["pass"], "decoy evidence fails", tid)
            R.check(not g(json.dumps({**ref_o, "evidence_line_ids": ref_o["evidence_line_ids"][:1]}))["pass"], "single evidence id fails", tid)
            R.check(not g(json.dumps({**ref_o, "evidence_line_ids": ["L001", "L002"]}))["pass"] or {"L001", "L002"} & set(h["evidence_ok_ids"]), "irrelevant evidence fails", tid)
            R.check(not g(json.dumps({**ref_o, "evidence_line_ids": ["L%03d" % i for i in range(1, 7)]}))["pass"], "6 evidence ids fails", tid)
            R.check(g("Sure! Here you go:\n```json\n" + t["reference_answer"] + "\n```")["pass"], "fenced answer accepted", tid)
        elif k == "slo":
            exp = t["hidden"]["expected"]
            ref_o = json.loads(t["reference_answer"])
            for f, v in exp.items():
                if isinstance(v, bool):
                    bad = {**ref_o, f: not v}
                else:
                    bad = {**ref_o, f: v * 1.05 if v else 1.0}
                    if not isinstance(v, int):
                        R.check(g(json.dumps({**ref_o, f: v * 1.001}))["pass"], f"slo: 0.1% error tolerated ({f})", tid)
                r = g(json.dumps(bad))
                R.check(not r["pass"] and r["detail"][f] is False, f"slo: wrong {f} fails", tid)
            R.check(not g(json.dumps({k2: 0 for k2 in exp}))["pass"], "slo: all-zero fails", tid)
            R.check(not g(json.dumps({k2: str(v) for k2, v in exp.items()}))["pass"], "slo: strings fail", tid)
        elif k == "runbook":
            ans = t["hidden"]["steps"]
            R.check(len(ans) >= 4, "runbook: non-trivial answer", tid)
            R.check(not g(json.dumps({"steps": ans[::-1]}))["pass"], "runbook: reversed fails", tid)
            R.check(not g(json.dumps({"steps": ans[:-1]}))["pass"], "runbook: missing step fails", tid)
            ids = [s["id"] for s in t["inputs"]["steps"]]
            R.check(not g(json.dumps({"steps": ids}))["pass"], "runbook: all steps fails", tid)
            R.check(not g(json.dumps({"steps": sorted(ans)}))["pass"] or sorted(ans) == ans, "runbook: ID-sorted fails (order matters)", tid)
            sh = ans[:]
            rnd.shuffle(sh)
            R.check(sh == ans or not g(json.dumps({"steps": sh}))["pass"], "runbook: shuffled fails", tid)
        elif k == "script":
            spec = t["hidden"]["spec"]
            tt, fmt = t["hidden"]["task_type"], t["hidden"]["log_format"]
            R.check(len({json.dumps(f["expect"], sort_keys=True) for f in spec["fixtures"]}) >= 3, "script: fixtures have varied expected outputs", tid)
            sample = t["inputs"]["sample"]["stdout"]
            for name, code in [("print {}", "import sys\nprint('{}')"), ("crash", "raise SystemExit(1)"),
                               ("hardcoded sample output", "import json\nprint(json.dumps(%r))" % sample)]:
                r = g("```python\n# file: analyze.py\n%s\n```" % code)
                stats[k]["trivial_n"] += 1
                stats[k]["trivial_fail"] += not r["pass"]
                R.check(not r["pass"], f"script: {name} fails", tid)
            ref = scripttasks.reference_script(tt, fmt)
            for old, new in MUTANTS[tt]:
                assert old in ref, (tt, old)
                r = g("```python\n# file: analyze.py\n%s\n```" % ref.replace(old, new))
                stats[k]["mut_n"] += 1
                stats[k]["mut_caught"] += not r["pass"]
                R.check(not r["pass"], f"script: mutant caught ({old[:22]!r})", tid)
        elif k == "fix":
            bug = t["inputs"]["buggy_file"]
            r = g("```python\n# file: oncall.py\n%s\n```" % bug)
            R.check(not r["pass"], "fix: unmodified buggy file fails", tid)
            stats[k]["trivial_n"] += 1
            stats[k]["trivial_fail"] += not r["pass"]
            fixed = t["hidden"]["fixed_file"]
            for tn, bugs in t["hidden"]["bugs"].items():
                for bn in bugs:  # fixed everything except one bug
                    other = {tn2: ([bn] if tn2 == tn else []) for tn2 in t["hidden"]["templates"]}
                    src = "\n\n".join(fixtasks.apply_bugs(fixtasks.T[x]["src"], x, other[x]) for x in t["hidden"]["templates"])
                    if "import re" in src:
                        src = "import re\n\n" + src.replace("import re\n\n\n", "").replace("import re\n\n", "")
                    r = g("```python\n# file: oncall.py\n%s\n```" % src)
                    stats[k]["mut_n"] += 1
                    stats[k]["mut_caught"] += not r["pass"]
                    R.check(not r["pass"], f"fix: leaving bug {tn}/{bn} unfixed fails", tid)
            R.check(g("```python\n# file: oncall.py\nimport sys\nsys.exit(1)\n```")["pass"] is False, "fix: crashing module fails", tid)
        sys.stdout.write(".")
        sys.stdout.flush()
    print()
    print("\n== summary (sandbox for code tasks: %s) ==" % sb)
    for k in ("triage", "script", "slo", "runbook", "fix"):
        s, n = stats[k], sum(1 for t in tasks if t["kind"] == k)
        parts = [f"reference pass {s['ref_pass']}/{n}", f"trivial/empty answers failed {s['trivial_fail']}/{s['trivial_n']}"]
        if s["rand_n"]:
            parts.append(f"random answers passed {s['rand_pass']}/{s['rand_n']}")
        if s["mut_n"]:
            parts.append(f"mutant/partial-fix candidates rejected {s['mut_caught']}/{s['mut_n']}")
        print(f"{k:8s} " + "; ".join(parts))
    print("checks run:", sum(R.checks.values()), "| failures:", len(R.fail), "| %.0fs" % (time.time() - t0))
    for f in R.fail[:40]:
        print("FAIL", f)
    print("VALIDATION", "OK" if not R.fail else "FAILED")
    sys.exit(1 if R.fail else 0)


if __name__ == "__main__":
    main()
