# planner - training-task factory

Tasks for the `planner` specialist: given a small repo (file tree + one-line summaries) and a feature request or bug
ticket, emit a strict-JSON plan that other specialists execute. Everything here is stdlib Python, deterministic, and
calls no model.

    python generator.py [--seed N] [--out tasks.jsonl]   # default seed 20261121 -> tasks.jsonl (206 tasks)
    python validate.py                                   # all checks, locally
    python validate.py --docker                          # same checks in the python:3.12-slim sandbox (image must already exist)
    python grader.py tasks.jsonl predictions.jsonl       # predictions: {"id": ..., "output": "<model text>"} per line

Files: `generator.py` (driver, ground-truth derivation), `gen_repo.py` (repo builders, 20 domains x 3 fields),
`gen_families.py` (30 scenario families), `grader.py`, `validate.py`, `tasks.jsonl`.

## Output format the model must produce

Strict JSON only (no fences, no prose), top-level object with exactly one key:

    {"steps": [{"id": "s1", "specialist": "data", "files_to_touch": ["migrations/0002_x.sql"],
                "goal": "...", "depends_on": [], "acceptance_check": "..."}]}

Specialists: python, java, ui, data, devops, ops, qa, debugger, reviewer. Every step has exactly the six keys.

## tasks.jsonl schema (one JSON object per line)

| field | meaning |
|---|---|
| `id` | `planner-0001`... |
| `family` | scenario family (e.g. `add_field_full`, `bug_cross`, `mixed_event`, `single_web`) |
| `difficulty` | `easy` 1-3 reference steps, `medium` 4-6, `hard` 7-10 |
| `kind` | `feature` or `bug` |
| `repo` | `{name, stack, files: {path: summary}}`; the tree is the keys of `files` |
| `request` | the feature request / bug ticket text |
| `prompt` | ready-to-use planner prompt (instructions + rendered repo + request) |
| `ground_truth` | see below |
| `reference_plan` | a plan that scores exactly 1.0 and passes |

`ground_truth`:
- `required`: list of items `{id: "R1", path, specialists}` (existing file that must change) or
  `{id, create: {dir, ext}, example, specialists}` (a new file; any not-yet-existing path under `dir` ending in `ext` matches).
  `specialists` = acceptable specialists for the step that covers it (e.g. a bug fix accepts `debugger` or the language specialist).
- `optional`: existing files that may be touched without penalty (README, conftest, changelog).
- `required_specialists`: specialists that must appear somewhere in the plan (only those the reference makes non-interchangeable, e.g. `qa`, `ops`, `reviewer`).
- `order`: `[A, B]` pairs: a step covering A must be the same step as, or a transitive ancestor of, a step covering B. `B == "@reviewer"` means any reviewer step.
- `parallel`: `[A, B]` pairs of independent work: they must be covered by different steps with no dependency path in either direction.
- `min_steps`/`max_steps`: sensible step-count range (reference-1 .. reference+2; single-step tasks are exactly 1).
- `max_extra_files`: tolerated number of unnecessary files (1 easy, 2-3 larger).
- `single_step`, `languages`: bookkeeping.

## Grading

Gates (any failure -> score 0, `gates_ok=false`): valid strict JSON; exact schema; every `specialist` is one of the nine;
valid DAG (ids unique, `depends_on` ids exist, no self-loop, no cycle); at most 12 steps.

Components (weights): recall of required files 0.20, precision 0.10 (extra files beyond `max_extra_files` cost 1/3 each;
any absolute/`..`/`~` path -> 0 and flag `outside_repo`), specialist match 0.10, ordering constraints 0.20, parallel
constraints (independent steps not serialized) 0.15, step count in range 0.10 (off by one = 0.5), concrete
`acceptance_check` 0.15 (>= 4 words and a test/command, file path, or observable condition; "works correctly", "done" etc. fail).

`passed` = score >= 0.80 AND recall == 1 AND order == 1 AND precision == 1 AND step count in range AND all acceptance checks
concrete AND specialist >= 0.8 AND parallel == 1 (or >= 0.5 when the task has several independent pairs) AND no outside files.
The score is a smooth signal for training; `passed` is the strict gate (a plan missing one file can still score 0.97 but does not pass).

## What is validated (`validate.py`)

All 206 reference plans score 1.0 and pass; negative controls are rejected on every applicable task: empty plan, blank,
prose, fenced JSON, cyclic, hallucinated specialist, missing dependency id, everything-serial (135 tasks with independent
pairs), one giant step (149 tasks with 3+ steps), file outside repo, missing required file, hallucinated file, vague acceptance,
no/reversed dependencies, shotgun extra files, too many steps. It also checks counts, difficulty spread, that every required path
exists in the repo tree, that hard tasks mix languages and devops/ops work, and generator determinism (seed 20261121 equals the
file on disk; seed 7 also yields 206 valid tasks).

## Design notes / limits

- Ground truth is derived from the generator's reference DAG: edges are hard ordering, incomparable steps are required-parallel.
  A valid alternative plan that serializes two reference-independent steps, or merges them into one step, loses parallel credit by design.
- Repo summaries state what each file does so the required set is inferable (e.g. the repository summary says it holds the SQL).
- Create-file examples (migration names) are illustrative; matching is by directory + extension.
- Domains/fields are reused across 206 tasks (60 domain-field combos), so text variety comes from families, phrasings and distractor files.
- Acceptance checks are judged by pattern, not executed; the sandbox is used only to run the stdlib validator.
