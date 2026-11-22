# debugger task factory

Training/eval tasks for the `debugger` specialist: read a multi-file project, a failing test and its real
traceback, find the **root cause** (which is usually *not* where the traceback points), name it, and fix it.

Nothing here calls a model. Tasks are generated from hand-written bug families, and every task is validated by
running real code in the phase0 sandbox (python:3.12-slim, `--network none --read-only --cap-drop ALL
--user 65534:65534 --memory 256m --cpus 1 --pids-limit 64`, one container at a time; `sandbox.py` is a copy of
`phase0/harness2.py::run_files` with `PYTHONHASHSEED=0` added).

## Files

| file | purpose |
|---|---|
| `tasks.jsonl` | the 124 tasks (one JSON object per line) |
| `fam_a.py` `fam_b.py` `fam_c.py` `fam_x.py` | the 31 bug families (easy / medium / hard / helper files); each has 4 variants |
| `build.py` | expands families into `tasks.jsonl`; runs each failing test once to capture the real traceback |
| `grade.py` | prompt builder, response parser and grader (`make_prompt`, `grade`) |
| `validate.py` | validates every task in the sandbox |
| `sandbox.py` | sandbox runner (temp dirs under `./.tmp`) |

Rebuild: `python build.py` (needs docker). Validate: `python validate.py [--only SUBSTRING]` (about 8 s per task).

## Schema (tasks.jsonl)

| field | meaning |
|---|---|
| `id` | `dbg_<family>_<n>` |
| `kind` | always `"debug"` |
| `difficulty` | `easy` / `medium` / `hard` |
| `category` | the planted root-cause category (same as `ground_truth.category`) |
| `tags` | subset of `red_herring`, `minimal_diff`, `no_collateral`, `flaky_looking` |
| `files` | `{filename: source}`, 3-6 small modules, flat directory, no tests included |
| `failing_test` | `{name, code}` visible test (plain asserts, run as `python test_failing.py`) |
| `traceback` | real stdout+stderr of running the failing test on the starting files in the sandbox |
| `traceback_mentions_root_cause_file` | bool, whether the traceback has a frame inside the root-cause file |
| `ground_truth` | `{file, function, category, cause, function_aliases}` |
| `hidden_tests` | `{name, code}` = the visible test plus extra assertions (red-herring guards, unrelated behaviour) |
| `reference` | `{files: {changed files, full contents}, root_cause: {file, function, category, cause}}` |
| `max_changed_lines` | only on `minimal_diff` tasks: cap on changed lines (+/-) summed over returned files (reference size + 2) |
| `negative_references` | only on `no_collateral` tasks: fixes that pass the visible test but break unrelated behaviour; hidden tests must reject them |

`function` conventions: bare function name, `Class.method` for methods, the constant name for module-level data
(`DEFAULTS`, `FACTORS`, `ORDER`; `<module>` also accepted), the class name when the bug is in the class body.
The grader accepts the full name or the last dotted component.

Categories (fixed list, 12): off-by-one, wrong type/None handling, mutated shared state, wrong default, stale
cache, incorrect ordering, timezone/rounding, encoding, mis-wired config, wrong unit, incorrect exception
handling, aliasing.

## Expected model output and grading

`grade.make_prompt(task)` builds the prompt. The response has two parts:

1. one ```json block with exactly the string keys `file`, `function`, `category`, `cause`
   (category from the list, file must exist in the project, cause non-empty and <= 300 chars);
2. each changed file complete, in a ```python block whose first line is `# file: name.py`.

`grade.grade(task, response_text)` returns:

* `root_cause`: 1 only if the JSON is strictly valid and `file`, `function` and `category` all equal the planted
  ground truth (the free-text `cause` is checked only for presence/length; `root_cause_parts` shows which fields matched);
* `fix`: 1 if the starting files overlaid with the returned files pass `hidden_tests` in the sandbox (returned
  `test_*.py` files are ignored; for `minimal_diff` tasks the total changed lines must be <= `max_changed_lines`);
* `score = 0.5*root_cause + 0.5*fix`; `full` = both.

## What the tasks contain

* 31 bug families x 4 variants (different domain, names, data, sometimes a different faulty entry) = 124 tasks.
* Root cause is one or more hops from the traceback: failures surface as an `AssertionError` in the test, or as
  `max()`/`sum()`/`KeyError`/`UnboundLocalError`/`ValueError`/`TypeError` in a downstream module; only a few
  tracebacks contain a frame inside the root-cause file (`traceback_mentions_root_cause_file`).
* `red_herring` (120 tasks): code that looks suspicious but is correct (e.g. `(total + per - 1) // per`,
  `attempts = retries + 1`, `>=` in TTL expiry, a duplicate-looking factor table); hidden tests pin its behaviour.
* `flaky_looking` (16): seeded `random`, injected fake clock, tests that "pass alone but fail after another test"
  (class-level shared list), lexicographic-vs-numeric ordering that works for some inputs. All are deterministic;
  validate re-runs them.
* `minimal_diff` (16): one-token fixes with a diff-size cap. `no_collateral` (16): hidden tests pin unrelated
  behaviour; `negative_references` contain an over-reaching fix that must fail.
* Fix-location ambiguity is avoided by documenting the contract in a docstring/comment next to the planted bug
  (e.g. "cache entries are keyed by (key, store.version)").

## Validation (validate.py)

For each task: schema + 3-6 files; start fails visible and hidden tests; reference passes visible test; the
reference response (`grade.reference_response`) scores 1.0 (JSON matches ground truth and hidden tests pass);
wrong-category/no-file answer scores 0; `no_collateral` negative references pass the visible test but fail hidden
tests; `minimal_diff` cap rejects an oversized rewrite; `flaky_looking` tasks give the same outcome on a second run.

Limits: tasks are templated (4 variants per family share structure), so for training diversity they should be
supplemented with more families; hidden tests cannot rule out every alternative valid fix location, ground truth
is the planted one.
