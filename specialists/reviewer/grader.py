"""Reviewer grader: prompt rendering + scoring (precision / recall / F1 per task) + pass threshold.

Pure stdlib, no I/O. Usage:
    from grader import render_prompt, score
    result = score(task, model_output_text)   # dict, see score()
"""
import json
import re

CATEGORIES = [
    "off_by_one", "inverted_condition", "missing_check", "resource_leak", "injection",
    "exception_handling", "return_type_change", "state_update", "backward_compat", "dropped_error",
]
LINE_TOLERANCE = 2      # |reported line - planted line| <= 2 (line numbers are NEW-file lines)
PASS_F1 = 0.75          # buggy diff passes iff verdict == request_changes and F1 >= PASS_F1
# Clean diff passes iff verdict == approve and there are zero findings (any finding is a false positive).

SYSTEM = (
    "You are a meticulous code reviewer. You are shown a pull request as a unified diff. Report only REAL bugs "
    "introduced by the diff (not style, naming or speculative concerns). If the diff is correct, approve it with no "
    "findings. Reply with strict JSON only, no prose, no code fences:\n"
    '{"verdict": "approve" | "request_changes", "findings": [{"file": str, "line": int, "category": str, '
    '"explanation": str}]}\n'
    "`line` is the line number in the NEW version of the file (shown as the number before each added/context line). "
    "`category` is one of: " + ", ".join(CATEGORIES) + ". "
    'Use "request_changes" iff you report at least one finding.'
)


def annotate_diff(diff):
    """Prefix every added/context line with its new-file line number (removed lines get blanks)."""
    out, new = [], 0
    for ln in diff.split("\n"):
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", ln)
        if m:
            new = int(m.group(1))
            out.append(ln)
        elif ln.startswith("+++") or ln.startswith("---") or ln.startswith("diff "):
            out.append(ln)
        elif ln.startswith("+"):
            out.append(f"{new:>4} {ln}")
            new += 1
        elif ln.startswith("-"):
            out.append(f"     {ln}")
        elif ln.startswith(" "):
            out.append(f"{new:>4} {ln}")
            new += 1
        else:
            out.append(ln)
    return "\n".join(out)


def render_prompt(task):
    """Return (system, user) strings for a task."""
    user = (f"Pull request: {task['title']}\n\nFiles in the repository: {', '.join(sorted(task['base_files']))}\n\n"
            f"```diff\n{annotate_diff(task['diff'])}\n```")
    return SYSTEM, user


def parse_answer(text, strict=True):
    """-> (obj | None, error). strict: the whole reply must be one JSON object (no fences / prose)."""
    t = text.strip()
    if not strict:
        m = re.match(r"^```(?:json)?\s*\n(.*)\n```$", t, re.S)
        if m:
            t = m.group(1).strip()
    try:
        obj = json.loads(t)
    except Exception as e:
        return None, f"invalid JSON: {e}"
    if not isinstance(obj, dict) or obj.get("verdict") not in ("approve", "request_changes"):
        return None, "verdict must be 'approve' or 'request_changes'"
    fs = obj.get("findings")
    if not isinstance(fs, list):
        return None, "findings must be a list"
    for f in fs:
        if not (isinstance(f, dict) and isinstance(f.get("file"), str) and isinstance(f.get("line"), int)
                and not isinstance(f.get("line"), bool) and isinstance(f.get("category"), str)
                and isinstance(f.get("explanation"), str)):
            return None, "each finding needs file:str line:int category:str explanation:str"
    return obj, ""


def match_findings(defects, findings):
    """Greedy one-to-one match; a finding matches a defect iff same file, |dline| <= tol, same category.
    Returns (matched pairs [(finding_idx, defect_idx)], unmatched finding idxs, unmatched defect idxs)."""
    used_d, used_f, pairs = set(), set(), []
    cands = []
    for fi, f in enumerate(findings):
        for di, d in enumerate(defects):
            if f["file"] == d["file"] and f["category"] == d["category"] and abs(f["line"] - d["line"]) <= LINE_TOLERANCE:
                cands.append((abs(f["line"] - d["line"]), fi, di))
    for _, fi, di in sorted(cands):
        if fi not in used_f and di not in used_d:
            used_f.add(fi); used_d.add(di); pairs.append((fi, di))
    return (pairs, [i for i in range(len(findings)) if i not in used_f],
            [i for i in range(len(defects)) if i not in used_d])


def score(task, answer, strict=True):
    """Score one answer (raw text, or an already-parsed dict) against a task.

    Returns dict: valid, verdict_ok, tp, fp, fn, precision, recall, f1, passed, error.
    Every finding that does not match a planted defect (any finding at all on a clean diff, a finding on a
    non-defect line, wrong category, duplicate of an already matched defect) is a false positive.
    Clean diff: precision/recall/f1 are 1.0 iff there are no findings, else 0.0 (precision 0).
    """
    if isinstance(answer, str):
        obj, err = parse_answer(answer, strict)
    else:
        obj, err = answer, ""
    res = dict(valid=obj is not None, verdict_ok=False, tp=0, fp=0, fn=0, precision=0.0, recall=0.0, f1=0.0,
               passed=False, error=err)
    if obj is None:
        res["fn"] = len(task["defects"])
        return res
    defects, findings = task["defects"], obj["findings"]
    want = "request_changes" if defects else "approve"
    res["verdict_ok"] = obj["verdict"] == want
    pairs, bad_f, miss_d = match_findings(defects, findings)
    tp, fp, fn = len(pairs), len(bad_f), len(miss_d)
    res.update(tp=tp, fp=fp, fn=fn)
    if not defects:
        res["precision"] = res["recall"] = res["f1"] = 1.0 if not findings else 0.0
        if findings:
            res["precision"] = 0.0
        res["passed"] = res["verdict_ok"] and not findings
        return res
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn)
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    res.update(precision=round(p, 4), recall=round(r, 4), f1=round(f1, 4))
    res["passed"] = res["verdict_ok"] and f1 >= PASS_F1
    return res


def suite_report(tasks, answers):
    """answers: {task_id: text}. Missing answer = invalid. Returns summary dict incl. per-difficulty/kind pass rate."""
    rows = {t["id"]: score(t, answers.get(t["id"], "")) for t in tasks}
    def rate(sel):
        ts = [t for t in tasks if sel(t)]
        return round(sum(rows[t["id"]]["passed"] for t in ts) / len(ts), 4) if ts else None
    return dict(
        pass_rate=rate(lambda t: True), buggy_pass=rate(lambda t: t["kind"] == "buggy"),
        clean_pass=rate(lambda t: t["kind"] == "clean"),
        by_difficulty={d: rate(lambda t, d=d: t["difficulty"] == d) for d in ("easy", "medium", "hard")},
        mean_f1_buggy=round(sum(rows[t["id"]]["f1"] for t in tasks if t["kind"] == "buggy")
                            / max(1, sum(t["kind"] == "buggy" for t in tasks)), 4),
        false_positive_findings_clean=sum(rows[t["id"]]["fp"] for t in tasks if t["kind"] == "clean"),
        per_task=rows)
