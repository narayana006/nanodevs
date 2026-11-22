"""Sandbox-side grader runner (stdlib only). Usage: python runner.py   (cwd = directory holding spec.json + candidate files)
Prints one JSON line: {"passed": k, "total": n, "failed": [...], "errors": [...]}.
Runs identically on the host and inside the locked-down container."""
import importlib.util
import json
import math
import os
import signal
import subprocess
import sys


def deep_equal(a, b, tol=1e-6):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(deep_equal(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(deep_equal(x, y, tol) for x, y in zip(a, b))
    return a == b


def run_script(spec):
    failed, errors = [], []
    for i, fx in enumerate(spec["fixtures"]):
        try:
            p = subprocess.run([sys.executable, "-I", os.path.abspath(spec["script"])] + fx["argv"],
                               cwd=os.path.join("fx", str(i)), capture_output=True, text=True, timeout=10)
            out = json.loads(p.stdout)
            ok = p.returncode == 0 and deep_equal(out, fx["expect"])
            if not ok:
                errors.append("fx%d: %s" % (i, (p.stderr or p.stdout)[-160:].replace("\n", " ")))
        except Exception as e:  # timeout, bad json
            ok = False
            errors.append("fx%d: %s" % (i, type(e).__name__))
        if not ok:
            failed.append(i)
    return dict(passed=len(spec["fixtures"]) - len(failed), total=len(spec["fixtures"]), failed=failed, errors=errors[:5])


class _Timeout(Exception):
    pass


def _alarm(*_):
    raise _Timeout()


def run_fix(spec):
    failed, errors = [], []
    try:
        s = importlib.util.spec_from_file_location("cand", spec["module"])
        mod = importlib.util.module_from_spec(s)
        signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(5)
        s.loader.exec_module(mod)
        signal.alarm(0)
    except BaseException as e:
        signal.alarm(0)
        return dict(passed=0, total=len(spec["cases"]), failed=list(range(len(spec["cases"]))), errors=["import: %s: %s" % (type(e).__name__, str(e)[:100])])
    for i, c in enumerate(spec["cases"]):
        signal.alarm(3)
        try:
            res = getattr(mod, c["fn"])(*c["args"])
            res = json.loads(json.dumps(res))
            ok = "raises" not in c["expect"] and deep_equal(res, c["expect"]["value"])
            if not ok:
                errors.append("case%d %s: got %r" % (i, c["fn"], res))
        except _Timeout:
            ok = False
            errors.append("case%d: timeout" % i)
        except BaseException as e:
            ok = "raises" in c["expect"] and type(e).__name__ == c["expect"]["raises"]
            if not ok:
                errors.append("case%d %s: %s" % (i, c["fn"], type(e).__name__))
        finally:
            signal.alarm(0)
        if not ok:
            failed.append(i)
    return dict(passed=len(spec["cases"]) - len(failed), total=len(spec["cases"]), failed=failed, errors=errors[:5])


if __name__ == "__main__":
    spec = json.load(open("spec.json"))
    print(json.dumps(run_script(spec) if spec["mode"] == "script" else run_fix(spec)))
