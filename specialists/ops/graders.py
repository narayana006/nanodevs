"""Graders for every task kind. grade(task, answer_text, sandbox="docker"|"local") -> {"pass": bool, "score": float, "detail": {...}}.
Only script/fix kinds execute candidate code; they run via runner.py inside the locked-down container (sandbox="docker").
sandbox="local" runs the same runner in a host subprocess: ONLY for trusted code (reference answers, validate negatives)."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

from common import json_objects, code_blocks

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGE = "python:3.12-slim"
TMP = os.path.join(HERE, ".tmp")
TRIAGE_KEYS = ["root_cause_service", "root_cause_category", "evidence_line_ids", "first_safe_action", "severity"]


def _res(ok, score, **detail):
    return {"pass": bool(ok), "score": round(float(score), 4), "detail": detail}


# ---------------------------------------------------------------- triage
def grade_triage(task, text):
    h = task["hidden"]
    objs = [o for o in json_objects(text) if any(k in o for k in TRIAGE_KEYS)]
    if not objs:
        return _res(False, 0.0, error="no JSON object with triage keys")
    o = objs[-1]
    det = {}
    det["root_cause_service"] = o.get("root_cause_service") == h["root_cause_service"]
    det["root_cause_category"] = o.get("root_cause_category") == h["root_cause_category"]
    det["first_safe_action"] = o.get("first_safe_action") == h["first_safe_action"]
    det["severity"] = o.get("severity") == h["severity"]
    ev = o.get("evidence_line_ids")
    ok = isinstance(ev, list) and all(isinstance(x, str) and re.fullmatch(r"L\d{3}", x) and 1 <= int(x[1:]) <= h["n_lines"] for x in ev)
    if ok:
        ev = list(dict.fromkeys(ev))
        hits = len(set(ev) & set(h["evidence_ok_ids"]))
        ok = (2 <= len(ev) <= h["max_evidence"] and hits >= h["min_evidence_hits"] and not (set(ev) & set(h["decoy_ids"]))
              and hits / len(ev) >= 0.5)
    det["evidence_line_ids"] = bool(ok)
    score = sum(det.values()) / 5
    return _res(all(det.values()), score, **det)


# ---------------------------------------------------------------- slo
def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def grade_slo(task, text):
    h = task["hidden"]
    objs = [o for o in json_objects(text) if any(k in o for k in h["expected"])]
    if not objs:
        return _res(False, 0.0, error="no JSON object with expected keys")
    o = objs[-1]
    det = {}
    for k, exp in h["expected"].items():
        got = o.get(k)
        if isinstance(exp, bool):
            ok = got is exp
        elif isinstance(exp, int):
            ok = _num(got) and abs(got - exp) < 1e-9
        else:
            ok = _num(got) and abs(got - exp) <= max(h["tol_abs"], h["tol_rel"] * abs(exp))
        det[k] = bool(ok)
    return _res(all(det.values()), sum(det.values()) / len(det), **det)


# ---------------------------------------------------------------- runbook
def grade_runbook(task, text):
    exp = task["hidden"]["steps"]
    objs = [o for o in json_objects(text) if "steps" in o]
    if not objs or not isinstance(objs[-1]["steps"], list) or not all(isinstance(s, str) for s in objs[-1]["steps"]):
        return _res(False, 0.0, error="no {\"steps\": [...]} object")
    got = objs[-1]["steps"]
    if got == exp:
        return _res(True, 1.0, exact=True)
    inter = len(set(got) & set(exp))
    f1 = 2 * inter / (len(set(got)) + len(set(exp))) if got or exp else 1.0
    return _res(False, 0.5 * f1, exact=False, set_match=set(got) == set(exp))


# ---------------------------------------------------------------- code kinds
def extract_code(text, fname):
    blocks = code_blocks(text)
    for info, body in blocks:
        m = re.match(r"\s*#\s*file:\s*(\S+)[ \t]*\n", body)
        if m and m.group(1) == fname:
            return body
    py = [b for i, b in blocks if i in ("python", "py", "")]
    return py[0] if py else None


def sandbox_run(spec, files, sandbox="docker", timeout=150):
    os.makedirs(TMP, exist_ok=True)
    d = tempfile.mkdtemp(dir=TMP)
    try:
        shutil.copy(os.path.join(HERE, "runner.py"), os.path.join(d, "runner.py"))
        json.dump(spec, open(os.path.join(d, "spec.json"), "w"))
        for n, c in files.items():
            open(os.path.join(d, n), "w").write(c)
        for i, fx in enumerate(spec.get("fixtures", [])):
            os.makedirs(os.path.join(d, "fx", str(i)))
            for n, c in fx["files"].items():
                open(os.path.join(d, "fx", str(i), n), "w").write(c)
        if sandbox == "local":
            cmd, name = [sys.executable, os.path.join(d, "runner.py")], None
        else:
            name = "ops-grade-" + uuid.uuid4().hex[:10]
            cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "1", "--pids-limit", "64",
                   "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
                   "-e", "PYTHONDONTWRITEBYTECODE=1", "-v", f"{d}:/w:ro", "-w", "/w", IMAGE, "python", "/w/runner.py"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=d)
            lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
            if not lines:
                return dict(passed=0, total=1, failed=[0], errors=["runner produced no result: " + (p.stderr or p.stdout)[-200:]])
            return json.loads(lines[-1])
        except subprocess.TimeoutExpired:
            if name:
                subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return dict(passed=0, total=1, failed=[0], errors=["TIMEOUT"])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def grade_code(task, text, fname, sandbox):
    code = extract_code(text, fname)
    if not code or not code.strip():
        return _res(False, 0.0, error="no code block")
    r = sandbox_run(task["hidden"]["spec"], {fname: code.strip("\n") + "\n"}, sandbox)
    return _res(r["passed"] == r["total"], r["passed"] / r["total"], passed=r["passed"], total=r["total"], errors=r["errors"])


def grade(task, text, sandbox="docker"):
    k = task["kind"]
    if k == "triage":
        return grade_triage(task, text or "")
    if k == "slo":
        return grade_slo(task, text or "")
    if k == "runbook":
        return grade_runbook(task, text or "")
    if k == "script":
        return grade_code(task, text or "", "analyze.py", sandbox)
    if k == "fix":
        return grade_code(task, text or "", "oncall.py", sandbox)
    raise ValueError(k)
