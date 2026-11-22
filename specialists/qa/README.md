# qa specialist: training-task factory

Tasks for the `qa` model ("write tests that catch bugs"). Every task is graded by **mutation**, like the `tests` kind in
`phase0/harness2.py`: the candidate's `test_solution.py` (plain `assert`, no pytest/unittest) must pass on the correct code
and fail (non-zero exit) on every planted mutant. No model, GPU, network or download is used anywhere in this directory.

## Files

| file | purpose |
|---|---|
| `tasks.jsonl` | the deliverable: one JSON task per line (schema below) |
| `defs/d0*.py` | hand-authored sources: module under test, reference tests, hand mutants as exact-once patches |
| `regress_defs.py` | bug reports + minimal regression tests (each points at one hand mutant) |
| `automut.py` | AST mutation generator (comparison/arithmetic/bool swaps, int +-1, True/False, min/max, negated `if`, `return None`) |
| `build.py` | defs -> `tasks.jsonl`; adds auto-mutants, derives `regression` and `improve` tasks, refuses anything inconsistent |
| `validate.py` | independent re-check of `tasks.jsonl` (see "Validation") |
| `sandbox.py` | the container sandbox (`run_files`, `run_tests`, `run_batch`) and `grade(task, tests)` |
| `prompts.py` | `render_prompt(task)`, `extract_tests(text)`, `grade_answer(task, text)` for the eventual training/eval loop |

Rebuild: `python3 build.py` (needs docker + the local `python:3.12-slim` image; results cached in `.tmp/cache.json`;
`--only SUBSTR` builds a subset without writing). Validate: `python3 validate.py [--ids SUBSTR] [--exact]`.

## Sandbox

`python:3.12-slim`, `--network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 65534:65534
--memory 256m --cpus 1 --pids-limit 64`, code mounted read-only at `/w`, `python test_solution.py` as the entry.
`run_files`/`run_tests` are exactly the `harness2.run_files` setup, one container per run. `run_batch` (used by `build.py` and by
default in `validate.py`, because the host runs many containers at once and one-per-run took ~5 s each) runs many variants
inside **one** container with the same limits plus `--tmpfs /tmp:size=64m` (needed to lay out each variant); every variant still gets a
fresh `python test_solution.py` subprocess with an 8 s timeout. `validate.py --exact` uses one container per run to prove both paths agree.

## Schema (`tasks.jsonl`, one object per line)

| field | type | meaning |
|---|---|---|
| `id` | str | unique; `qa_<name>`, `qa_<name>_regressN`, `qa_<name>_improve` |
| `kind` | str | `tests` (write tests from spec), `regression` (bug report -> minimal regression test), `improve` (strengthen a weak test file) |
| `difficulty` | str | `easy` / `medium` / `hard` (by logic depth: simple pure functions < stateful classes/parsers < multi-file, time/rounding/ordering subtleties) |
| `files` | {name: source} | the code the model sees (the module under test; for `regression` the BUGGY version). 1-3 files for multi-file tasks |
| `reference_files` | {name: source} | the correct code the tests must pass on (equals `files` except for `regression`, where it is the fixed code) |
| `instruction` | str | task text including output format; `prompts.render_prompt` adds the code (and the starting test file for `improve`) |
| `mutants` | list | broken variants, each `{id, origin: "hand"\|"auto", tag, desc, files}`; `files` holds only the changed files (overlay on `reference_files`: `{**reference_files, **mutant.files}`) |
| `reference_tests` | str | a test file that passes on `reference_files` and kills every mutant |
| `starting_tests` | str | (`improve` only) the weak test file shown to the model; passes on the correct code |
| `surviving` | [id] | (`improve` only) mutants that survive `starting_tests` (>= 2, never all) |

`tag` is the mutation family: off-by-one, boundary, comparison, swapped-args, missing-edge-case, wrong-default, exception-type,
ordering, rounding, mutable-default, empty-input, logic, ast (auto). Grading: `sandbox.grade(task, tests)`; passes iff
the tests pass on `reference_files` and fail on all `mutants` (hand and auto).

### Kinds
1. **tests**: spec = docstrings of the module (+ one-line instruction); mutants = 4-8 hand-designed (+ up to 4 auto).
2. **regression**: the buggy version + a short bug report; the candidate must fail on the buggy code and pass on the fixed one.
   The bug is one of the hand mutants of the base task; the reference test is <= 12 non-blank lines (enforced).
3. **improve**: same code and mutants as the base task; `starting_tests` = the first k top-level statements of the reference tests
   (k chosen per task so that >= 2 mutants survive); the candidate must return a complete file that kills all.

## Auto-mutants and equivalence

`automut.candidates()` yields every single-site AST mutation. `build.py` shuffles them deterministically (seeded by task id), runs the
first 14 against the task's reference tests, and **keeps at most 4 that the reference tests kill**. Candidates that survive are
dropped (equivalent mutants, or reference tests too weak to tell; counted in the build summary); ones that time out, don't
import, or raise NameError are dropped too. So every kept auto-mutant is demonstrably behaviour-changing and detectable. Hand mutants
are not auto-filtered: `build.py` refuses a task if a hand mutant survives the reference tests (this caught ~10 equivalent
mutants during authoring, which were replaced). Note `ast.unparse` normalises formatting of auto-mutant files (comments dropped).

## Validation (`validate.py`)

Per task: reference tests pass on the correct code; every mutant killed (and not merely by a `SyntaxError`/`ImportError`);
trivial candidates (empty file, `pass`, `assert True`, import-only) all fail the grade, and no mutant dies on a bare import;
regression: buggy == fixed + bug, test minimal; improve: starting tests pass and `surviving` is exact and meaningful.

## Contents (current `tasks.jsonl`)

* 183 tasks: 73 `tests`, 37 `regression`, 73 `improve`
  (the 6 phase0 tasks are not included; all 73 modules here are new).
* difficulty (tests/regression/improve): easy 16/20/16,
  medium 35/9/35, hard 22/8/22.
* 20 tasks are multi-file (2-3 modules: inventory, cart+pricing, calculator lexer+evaluator, RBAC, dependency planner, library loans,
  undo/redo editor, rule engine, text stats).
* mutants over the 73 base modules: 560 hand-designed + 290 auto (AST) = 850 unique; `regression`/`improve` tasks reuse them.
  Hand mutant tags: {'logic': 238, 'missing-edge-case': 107, 'boundary': 93, 'off-by-one': 40, 'ordering': 27, 'comparison': 17, 'rounding': 12, 'exception-type': 10, 'wrong-default': 6, 'swapped-args': 5, 'empty-input': 4, 'mutable-default': 1}.
* Last full validation: `python3 validate.py` -> `183/183 tasks valid`, including a second pass under a different
  `PYTHONHASHSEED` to prove the kill vector is not order-flaky.


## Caveats
* Mutants and tests are all authored here; difficulty labels are heuristic, not measured against a model.
* Timing-dependent behaviour is avoided: all clocks are injected (`now` arguments).
* Hand mutant count per base task is 4-8 (most have 8); the same mutants are reused by that task's `regression` and `improve` variants,
  so training on all kinds for one module sees the same code several times (split by module, not by task, when making dev sets).
