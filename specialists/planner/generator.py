#!/usr/bin/env python3
"""Seeded generator for planner tasks. Usage: python generator.py [--seed N] [--out tasks.jsonl]
Stdlib only, deterministic: same seed -> byte-identical output. Calls no model."""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_repo import DOMAINS, web_repo, etl_repo, mixed_repo, cli_repo
import gen_families as F

DEFAULT_SEED = 20261121

PROMPT_HEAD = """You are the PLANNER. Turn the request into a small, ordered, parallelizable plan that specialist models execute.
Specialists: python (python backend/library code), java (java/spring code), ui (frontend ts/tsx/css), data (SQL schema, migrations, queries, ETL models), devops (Docker, CI, k8s, terraform, build files), ops (runbooks, alerts, dashboards, rollout notes), qa (writes/extends tests), debugger (diagnoses and fixes a bug), reviewer (reviews changes, no new features).
Output ONLY strict JSON, no prose, no code fences:
{"steps": [{"id": "s1", "specialist": "<one of the above>", "files_to_touch": ["<path>", ...], "goal": "<one sentence>", "depends_on": ["<id>", ...], "acceptance_check": "<concrete command, test or observable condition>"}]}
Rules: use only files that exist in the repo tree or new files in existing directories; list a dependency only when a step really needs another step's output; steps that do not need each other must not depend on each other; use as few steps as the request needs (one step is fine for a one-line change)."""


def build_prompt(repo_text, request):
    return f"{PROMPT_HEAD}\n\n{repo_text}\n\nRequest:\n{request}\n"


def reach(steps_deps):
    """transitive ancestors per key."""
    anc = {}

    def go(k):
        if k in anc:
            return anc[k]
        s = set()
        for d in steps_deps[k]:
            s.add(d)
            s |= go(d)
        anc[k] = s
        return s
    for k in steps_deps:
        go(k)
    return anc


def build_task(idx, family, stack, lang, rng, dom, others, fld, scen_fn=None, single=None):
    if stack == "web":
        repo = web_repo(rng, lang, dom, others)
        ctxlang = lang
    elif stack == "etl":
        repo = etl_repo(rng, dom, others)
        ctxlang = "etl"
    elif stack == "mixed":
        repo = mixed_repo(rng, dom, others)
        ctxlang = "mixed"
    else:
        repo = cli_repo(rng, dom)
        ctxlang = "cli"
    c = F.Ctx(rng, repo, ctxlang, dom, fld)
    if single is not None:
        req, role, spec, accept, goal, acc = single
        sc = F.Sc("bug" if req.lower().startswith(("bug", "ui bug")) else "feature", req,
                  [F.S("s", spec, [role], goal, [], acc, accept=accept)], lo=1, hi=1, extra=1, tag="single")
    else:
        sc = scen_fn(c)
    steps = sc["steps"]
    keys = [s["key"] for s in steps]
    assert len(set(keys)) == len(keys), (family, keys)
    # --- required items
    items, role2id, step_files = [], {}, {}
    for s in steps:
        files = []
        for role in s["roles"]:
            assert role not in role2id, (family, role)
            iid = f"R{len(items) + 1}"
            role2id[role] = iid
            if role == "new_migration":
                items.append({"id": iid, "create": {"dir": repo.roles["new_migration_dir"], "ext": ".sql"}, "example": c.mig,
                              "specialists": s["accept"]})
                files.append(c.mig)
            else:
                path = repo.roles[role]
                items.append({"id": iid, "path": path, "specialists": s["accept"]})
                files.append(path)
        for role in s["refs"]:
            files.append(repo.roles[role])
        assert files, (family, s["key"])
        step_files[s["key"]] = files
    # --- order & parallel
    deps = {s["key"]: s["deps"] for s in steps}
    for k, ds in deps.items():
        for d in ds:
            assert d in deps and keys.index(d) < keys.index(k), (family, k, d)
    anc = reach(deps)
    own = {s["key"]: s for s in steps}
    rep = {k: role2id[own[k]["roles"][0]] for k in keys if own[k]["roles"]}
    order, parallel = [], []
    for k in keys:
        for d in deps[k]:
            if k in rep and d in rep:
                pair = [rep[d], rep[k]]
            elif k not in rep and own[k]["spec"] == "reviewer" and d in rep:
                pair = [rep[d], "@reviewer"]
            else:
                continue
            if pair not in order:
                order.append(pair)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a in rep and b in rep and a not in anc[b] and b not in anc[a]:
                parallel.append([rep[a], rep[b]])
    n = len(steps)
    required_specs = sorted({s["spec"] for s in steps if len(s["accept"]) == 1})
    optional = [p for p in (repo.roles.get("readme"), "tests/conftest.py" if "tests/conftest.py" in repo.files else None,
                            "CHANGELOG.md" if "CHANGELOG.md" in repo.files else None) if p]
    ids = {k: f"s{i + 1}" for i, k in enumerate(keys)}
    plan = {"steps": [{"id": ids[s["key"]], "specialist": s["spec"], "files_to_touch": step_files[s["key"]], "goal": s["goal"],
                       "depends_on": [ids[d] for d in s["deps"]], "acceptance_check": s["acc"]} for s in steps]}
    diff = "easy" if n <= 3 else ("medium" if n <= 6 else "hard")
    def _lang(p):
        for ext, name in ((".java", "java"), (".py", "python"), (".ts", "ts"), (".tsx", "ts"), (".sql", "sql"),
                          (".tf", "terraform"), (".yaml", "yaml"), (".yml", "yaml")):
            if p.endswith(ext):
                return name
        return ""
    langs = sorted({_lang(p) for p in sum(step_files.values(), [])} - {""})
    task = {
        "id": "",
        "family": family,
        "difficulty": diff,
        "kind": sc["kind"],
        "repo": {"name": repo.name, "stack": repo.stack, "files": dict(sorted(repo.files.items()))},
        "request": sc["request"],
        "ground_truth": {
            "required": items,
            "optional": optional,
            "required_specialists": required_specs,
            "order": order,
            "parallel": parallel,
            "min_steps": sc["lo"],
            "max_steps": sc["hi"],
            "max_extra_files": sc["extra"],
            "single_step": n == 1,
            "languages": langs,
        },
        "reference_plan": plan,
    }
    task["prompt"] = build_prompt(repo.text(), sc["request"])
    return task


def generate(seed=DEFAULT_SEED):
    master = random.Random(seed)
    combos = [(d, f) for d in DOMAINS for f in d[3]]
    master.shuffle(combos)
    ptr = [0]

    def nxt():
        d, f = combos[ptr[0] % len(combos)]
        ptr[0] += 1
        return d, f

    jobs = []  # (family, stack, lang, scen_fn, single_index)
    for name, fn, cnt in F.WEB_FAMILIES:
        for i in range(cnt):
            jobs.append((name, "web", "python" if i % 2 == 0 else "java", fn, None))
    for i in range(28):
        jobs.append(("single", "web", "python" if i % 2 == 0 else "java", None, i))
    for name, fn, cnt in [("etl_add_column", F.e_add_column, 6), ("etl_new_metric", F.e_new_metric, 5), ("etl_bug", F.e_bug, 5), ("etl_late", F.e_late, 5)]:
        for i in range(cnt):
            jobs.append((name, "etl", "python", fn, None))
    for i in range(4):
        jobs.append(("single", "etl", "python", None, i))
    for name, fn, cnt in [("mixed_event", F.m_event, 5), ("mixed_bug", F.m_bug, 4), ("mixed_region", F.m_region, 4), ("mixed_obs", F.m_obs, 4), ("mixed_idtype", F.m_idtype, 4)]:
        for i in range(cnt):
            jobs.append((name, "mixed", "mixed", fn, None))
    for i in range(3):
        jobs.append(("single", "mixed", "mixed", None, i))
    for name, fn, cnt in [("cli_flag", F.c_flag, 4), ("cli_format", F.c_format, 4), ("cli_bug", F.c_bug, 3), ("cli_config", F.c_config, 3)]:
        for i in range(cnt):
            jobs.append((name, "cli", "python", fn, None))
    for i in range(4):
        jobs.append(("single", "cli", "python", None, i))
    master.shuffle(jobs)
    tasks = []
    single_ptr = {}
    for n, (family, stack, lang, fn, si) in enumerate(jobs):
        rng = random.Random(f"{seed}:{n}")
        dom, fld = nxt()
        others = rng.sample([d for d in DOMAINS if d is not dom], 3)
        single = None
        if si is not None:
            # build a ctx just to enumerate the single catalogue
            tmp_repo = {"web": lambda: web_repo(rng, lang, dom, others), "etl": lambda: etl_repo(rng, dom, others),
                        "mixed": lambda: mixed_repo(rng, dom, others), "cli": lambda: cli_repo(rng, dom)}[stack]()
            tmp = F.Ctx(rng, tmp_repo, "etl" if stack == "etl" else lang if stack == "web" else stack, dom, fld)
            cat = {"web": F.singles_web, "etl": F.singles_etl, "mixed": F.singles_mixed, "cli": F.singles_cli}[stack](tmp)
            single = cat[(single_ptr.setdefault((stack, lang), 0)) % len(cat)]
            single_ptr[(stack, lang)] += 1
            family = f"single_{stack}"
        t = build_task(n, family, stack, lang, rng, dom, others, fld, scen_fn=fn, single=single)
        tasks.append(t)
    for i, t in enumerate(tasks):
        t["id"] = f"planner-{i + 1:04d}"
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.jsonl"))
    a = ap.parse_args()
    tasks = generate(a.seed)
    with open(a.out, "w") as f:
        for t in tasks:
            f.write(json.dumps(t, sort_keys=False, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"wrote {len(tasks)} tasks to {a.out}; difficulty={dict(Counter(t['difficulty'] for t in tasks))}")


if __name__ == "__main__":
    main()
