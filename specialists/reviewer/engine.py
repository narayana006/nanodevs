"""Assembles tasks from templates. A template is a dict (see templates_*.py); each (template, params) pair yields
one CLEAN task (the correct diff) and one BUGGY task (same feature with 1-3 planted defects substituted in)."""
import difflib
import re


def sub(text, P):
    return re.sub(r"@(\w+)@", lambda m: str(P[m.group(1)]), text)


def make_diff(base, new):
    out = []
    for fn in sorted(set(base) | set(new)):
        a, b = base.get(fn), new.get(fn)
        if a == b:
            continue
        out.extend(difflib.unified_diff((a or "").splitlines(), (b or "").splitlines(), f"a/{fn}" if a is not None else "/dev/null",
                                        f"b/{fn}", n=3, lineterm=""))
    return "\n".join(out) + "\n"


def apply_diff(base, diff):
    """Minimal unified-diff applier (independent of difflib) used to verify the stored diff."""
    files = dict(base)
    cur = None
    lines = diff.split("\n")
    i = 0
    per = {}
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("+++ "):
            cur = ln[4:].strip()[2:]
            per.setdefault(cur, [])
        elif ln.startswith("@@"):
            per[cur].append([])
        elif cur and per.get(cur) and per[cur] and (ln[:1] in ("+", "-", " ")) and not ln.startswith("--- "):
            per[cur][-1].append(ln)
        i += 1
    for fn, hunks in per.items():
        src = (files.get(fn, "") or "").split("\n")
        if src and src[-1] == "":
            src.pop()
        out, pos = [], 0
        for h in hunks:
            old = [l[1:] for l in h if l[0] in " -"]
            # locate hunk start by matching old lines
            for s in range(pos, len(src) - len(old) + 1):
                if src[s:s + len(old)] == old:
                    break
            else:
                if old:
                    raise ValueError("hunk does not apply in " + fn)
                s = pos
            out.extend(src[pos:s])
            out.extend(l[1:] for l in h if l[0] in " +")
            pos = s + len(old)
        out.extend(src[pos:])
        files[fn] = "\n".join(out) + "\n"
    return files


def added_lines(diff):
    """{file: set(new line numbers of added lines)}"""
    res, cur, new = {}, None, 0
    for ln in diff.split("\n"):
        if ln.startswith("+++ "):
            cur = ln[4:].strip()[2:]
            res[cur] = set()
        elif ln.startswith("--- "):
            continue
        else:
            m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)", ln)
            if m:
                new = int(m.group(1))
            elif ln.startswith("+"):
                res[cur].add(new); new += 1
            elif ln.startswith(" "):
                new += 1
    return res


def strip_files(d):
    return {k: v.strip("\n") + "\n" for k, v in d.items()}


def build(template, P, tname, variant):
    t = {k: v for k, v in template.items()}
    S = lambda x: sub(x, P)
    base = strip_files({S(k): S(v) for k, v in t["base"].items()})
    good = strip_files({S(k): S(v) for k, v in t["good"].items()})
    for fn, txt in base.items():
        good.setdefault(fn, txt)
    tests = S(t["tests"]).strip("\n") + "\n"
    use = P.get("_use", list(range(len(t["defects"]))))
    diff_level = P.get("_diff", t["difficulty"])
    title = S(t["title"])
    defs = [dict(file=S(d["file"]), old=S(d["old"]), new=S(d["new"]), category=d["category"], explanation=S(d["why"]),
                 proof_test=d["test"], line_offset=d.get("line_offset", 0)) for d in t["defects"]]
    clean = dict(id=f"rev-{tname}-{variant}-clean", kind="clean", difficulty=diff_level, title=title, base_files=base,
                 diff=make_diff(base, good), patched_files=good, fixed_files=good, hidden_tests=tests, defects=[],
                 reference_review=dict(verdict="approve", findings=[]), meta=dict(template=tname, variant=variant))
    # buggy
    bug = dict(good)
    for di in use:
        d = defs[di]
        assert bug[d["file"]].count(d["old"]) == 1, (tname, variant, di, "old not unique/found")
        bug[d["file"]] = bug[d["file"]].replace(d["old"], d["new"])
    planted = []
    for di in use:
        d = defs[di]
        txt = bug[d["file"]]
        assert txt.count(d["new"]) == 1, (tname, variant, di, "new not unique")
        line = txt[:txt.index(d["new"])].count("\n") + 1 + d["line_offset"]
        planted.append(dict(id=f"D{di + 1}", file=d["file"], line=line, category=d["category"],
                            explanation=d["explanation"], correct_text=d["old"], buggy_text=d["new"],
                            proof_test=d["proof_test"]))
    bdiff = make_diff(base, bug)
    al = added_lines(bdiff)
    for p in planted:
        assert p["line"] in al.get(p["file"], ()), (tname, variant, p["id"], "defect line not an added line")
    buggy = dict(id=f"rev-{tname}-{variant}-buggy", kind="buggy", difficulty=diff_level, title=title, base_files=base,
                 diff=bdiff, patched_files=bug, fixed_files=good, hidden_tests=tests, defects=planted,
                 reference_review=dict(verdict="request_changes", findings=[
                     dict(file=p["file"], line=p["line"], category=p["category"], explanation=p["explanation"])
                     for p in planted]), meta=dict(template=tname, variant=variant))
    assert clean["diff"].strip(), tname
    return [clean, buggy]
