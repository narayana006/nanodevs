# reviewer task factory

Training/eval tasks for the `reviewer` specialist: given a unified diff, answer strict JSON

```json
{"verdict": "approve" | "request_changes",
 "findings": [{"file": "x.py", "line": 12, "category": "off_by_one", "explanation": "..."}]}
```

Half of the diffs contain 1-3 planted, test-proven defects; the other half are clean (some deliberately contain
suspicious-looking but correct code: sliding-window loops, an f-string ORDER BY guarded by a whitelist, `lo/hi`
binary search bounds, `finally` cleanup, `>=` vs `>` boundaries...) and measure false positives.

## Files

| file | purpose |
|---|---|
| `tasks.jsonl` | the tasks (generated, committed artifact) |
| `templates_1..4.py` | task sources: 43 scenario templates, each instantiated twice (v1/v2, different names, constants and defect subsets) |
| `engine.py` / `build.py` | `python3 build.py` regenerates `tasks.jsonl` (diffs via difflib, defect lines computed, asserted to be on added lines) |
| `grader.py` | `render_prompt(task)`, `score(task, answer)`, `suite_report(tasks, answers)` |
| `validate.py` | full validation (below); `--only SUBSTR`, `--no-docker` |
| `_sandbox.py`, `_run.py`, `_rt.py` | one-container-at-a-time sandbox + test runtime (`python:3.12-slim`, `--network none --read-only --cap-drop ALL --user 65534:65534 --memory 256m --cpus 1 --pids-limit 64`, stdlib only) |

## Task schema (one JSON object per line)

| field | meaning |
|---|---|
| `id` | `rev-<template>-<v1|v2>-<clean|buggy>` |
| `kind` | `"buggy"` (1-3 planted defects) or `"clean"` (0 defects, correct diff) |
| `difficulty` | `easy` (1 obvious defect, tiny diff), `medium` (subtle/semantic or 2 defects), `hard` (suspicious-but-correct context, masked/multiple defects, multi-file or 3 defects) |
| `title` | PR title shown to the reviewer |
| `base_files` | `{filename: text}` repository before the change |
| `diff` | unified diff base -> patched (git-style `a/`, `b/` paths) |
| `patched_files` | files after applying `diff` (what the reviewer is judging; line numbers refer to these) |
| `fixed_files` | corrected version (= `patched_files` for clean tasks) |
| `hidden_tests` | `test_hidden.py` text: plain functions `test_*`, run by `_rt.run_all` (no pytest) |
| `defects` | planted defects: `{id, file, line, category, explanation, correct_text, buggy_text, proof_test}`; `line` is the 1-based line in the NEW file |
| `reference_review` | the gold answer in the output format |
| `meta` | `{template, variant}` |

Categories: `off_by_one, inverted_condition, missing_check, resource_leak, injection, exception_handling,
return_type_change, state_update, backward_compat, dropped_error`.

### Proof tests (what "proven" means here)
For every defect, `validate.py` checks in the locked-down sandbox that the hidden tests:
1. pass on `base_files`;
2. pass on `fixed_files` (the corrected version);
3. the defect's `proof_test` FAILS on `patched_files`; for multi-defect tasks it also fails when that defect alone is
   applied to the fixed code, while the other defects' proof tests still pass (independence).

Caveat: tests of *new* API (a function/parameter/constant that does not exist in the base) are guarded with
`needs(...)`/`needs_param(...)` from `_rt.py`, which skip (= pass) when the API is absent. That is how "passes on base"
holds for new-feature defects; the failing side is real (a genuine assertion/exception on the diffed code).
Defects that are *omissions* (a dropped guard) have their `line` on the nearest added line (the code that now
lacks the guard); tolerance covers the exact spot.

## Grading (`grader.score`)

* Output must be one JSON object only (strict; `strict=False` strips a single ```json fence). Invalid = fail.
* A finding matches a planted defect iff same `file`, `|line - defect.line| <= 2` (`LINE_TOLERANCE`) and same
  `category`; one-to-one greedy matching (closest first). Unmatched findings are false positives (any finding on a
  clean diff, a finding on a non-defect line, wrong category, a duplicate of an already matched defect).
* Buggy task: precision = tp/(tp+fp), recall = tp/(tp+fn), F1. **Pass iff verdict == `request_changes` and F1 >= 0.75**
  (`PASS_F1`). So 1 defect + 1 extra finding fails (F1 .67); 2 defects + 1 extra finding passes (F1 .80).
* Clean task: **pass iff verdict == `approve` and zero findings**; precision/recall/F1 are reported as 1.0/0.0 accordingly.
* `render_prompt(task)` returns `(system, user)`; the user message shows the diff with new-file line numbers in front
  of every added/context line so the model need not count hunk offsets.
* `suite_report` aggregates pass rate overall / by kind / by difficulty, mean F1 on buggy tasks, and the number of
  false-positive findings on clean tasks. Overall pass rate = a reviewer must both catch bugs and not cry wolf.

## Validation (`python3 validate.py`, runs ~180 containers sequentially, a few minutes)

Schema/uniqueness, diff round-trip with an independent patch applier, defect lines on added diff lines, sandbox
proofs (above), and grader sanity: the reference review scores F1 1.0 and passes every task; always-approve passes
0 buggy tasks (and exactly the clean half); flag-everything (every added line x every category) passes 0 tasks;
within-tolerance finding passes, out-of-tolerance / wrong-category fails, duplicates count as false positives, fenced
JSON rejected in strict mode, any finding on a clean diff fails.

## Known limits
* Variety comes from 43 hand-written scenarios x 2 parametrised variants (names, constants, which defects), so
  the diffs are original but not 150+ independent designs; hold out by `meta.template` when splitting train/eval.
* Every buggy task has a clean sibling with the same base (different diff); split siblings together.
* Tasks are single-concept Python modules (<= 2 files); no cross-repo context.
