# `data` specialist: training-task factory

134 original, validated tasks for the SQL / data-wrangling / ETL / schema / query-optimisation model.
Pattern follows `phase0/harness2.py`: every task has a reference solution and hidden checks, graded in the locked-down
container (`python:3.12-slim`, `--network none --read-only --cap-drop ALL --user 65534:65534 --memory 256m --cpus 1 --pids-limit 64`).
Grading uses only stdlib `sqlite3`, `json`, `csv` (container: Python 3.12.16, SQLite 3.46.1). Nothing is installed or downloaded; no model is called.

## Files

| file | purpose |
|---|---|
| `tasks.jsonl` | the 134 tasks, one JSON object per line (generated, deterministic) |
| `grader.py` | grader that runs inside the container: JSONL jobs on stdin, JSONL results on stdout |
| `validate.py` | proves start state FAILS and reference PASSES for every task (one container) |
| `build.sh`, `build_tasks.py` | regenerate `tasks.jsonl` (runs inside the container so expected outputs come from the grading sqlite/python) |
| `domains.py` | 6 schemas + seeded data generators (shop, hr, events, library, sensors, school) |
| `defs_sql.py`, `defs_ddl_opt.py`, `defs_etl.py` | the task definitions (specs, references, probes, test generators) |

## Counts

| kind | easy | medium | hard | total |
|---|---|---|---|---|
| `sql_write` (query from schema + English spec) | 9 | 24 | 20 | 53 |
| `sql_fix` (repair a wrong query) | 8 | 14 | 4 | 26 |
| `ddl` (migration / constraints / triggers / views) | 2 | 7 | 5 | 14 |
| `etl` (plain-Python CSV/JSON cleaning) | 5 | 15 | 6 | 26 |
| `optimize` (explain-then-fix slow query) | 2 | 7 | 6 | 15 |
| total | 26 | 67 | 41 | 134 |

## Record schema (`tasks.jsonl`)

| field | meaning |
|---|---|
| `id` | `data-<kind>-<key>`, unique |
| `kind` | `sql_write`, `sql_fix`, `ddl`, `etl`, `optimize` |
| `difficulty` | `easy` / `medium` / `hard` |
| `domain` | data domain (`shop`, `hr`, `events`, `library`, `sensors`, `school`; `migration`; `etl`) |
| `schema_sql` | DDL the task starts from (visible to the model, also used to build hidden DBs) |
| `files` | for `etl`: the worked-example input(s) as `{name: text}`, else `{}` |
| `inputs` | the structured pieces of the prompt: `spec`, `sample_sql`, `buggy_query`, `symptom`, `query`, `start_plan`, `seed_sql`, `example` |
| `prompt` | the fully rendered prompt to send to a model (ends with the answer-format instruction) |
| `hidden` | hidden checks, see below. NEVER show to the model |
| `check` | grading parameters (`ordered`, `search`/`forbid` plan regexes, ...) |
| `reference` | a known-correct answer text (query / migration / python code / index script) |
| `start_state` | the answer that represents "no work done" (stub, buggy query, no-op migration, original slow query); must fail |
| `meta` | `answer_format` (`sql` or `python`) and counts |

`hidden` by kind:
* `sql_write`, `sql_fix`, `optimize`: `datasets` = list of `{name, data: {table: [rows]}, expected: {columns, rows}}`. Three datasets per query task (6/24/60 base rows, randomly generated incl. NULLs, ties and unmatched rows); two (150/400) for optimize. `expected` was produced by running `reference` in the container.
* `ddl`: `seed_sql` and `probes`: each probe is `{label, setup[], sql, expect: ok|error|rows, err: integrity|operational, rows, ordered}`; probes run on the migrated DB with `PRAGMA foreign_keys=ON`, each in a transaction that is rolled back.
* `etl`: `tests` = list of `{args, expected}`; `solve(*args)` is called per test (first test is the worked example shown in the prompt, the rest are hidden).

## Grading rules (`grader.py`)

* Answer extraction: first fenced block if present, else the raw text.
* `sql_write` / `sql_fix`: one SELECT/WITH statement, executed under a read-only authorizer with a 6 s per-query budget, against every hidden dataset. Column count and (case-insensitive) names must match. Rows compared as a multiset (floats rounded to 6 places, 1 == 1.0, NULLs compared as NULL), or as an exact sequence when `check.ordered` is true (specs with ORDER BY give full tie-breaks).
* `ddl`: migration script run via `executescript` on schema + seed with FKs off; `foreign_key_check` must be clean; then every probe must behave as specified (constraint violations must raise `IntegrityError`, so a typo cannot fake a "rejected" probe).
* `etl`: the candidate code is `exec`'d in a separate `python -I` subprocess (12 s timeout) that receives only the test inputs; hidden expectations never enter that process. Results are compared as JSON values (floats within 1e-6).
* `optimize`: the script may contain only `CREATE [UNIQUE] INDEX` statements and at most one final SELECT/WITH (the rewritten query; if absent the original is used). After building the indexes on each dataset, results must equal the expected rows, and `EXPLAIN QUERY PLAN` must match every regex in `check.search` and none in `check.forbid` (e.g. `SEARCH orders USING INDEX`, no `SCAN orders`, no `TEMP B-TREE`, no `AUTOMATIC`). The "explain" half of explain-then-fix is requested in comments in the prompt but is not graded.
* Job data is passed over stdin (no hidden files mounted), 25 s alarm per job; any grader exception counts as a fail.

## Usage

```
./validate.py        # or: python3 validate.py   (needs Docker + the local python:3.12-slim image)
./build.sh           # regenerates tasks.jsonl 
```

To grade a model answer: send `{"job_id": ..., "task": <record>, "answer": <model text>}` as one JSON line to
`docker run --rm -i <same hardening flags> -v $PWD:/g:ro -w /g python:3.12-slim python /g/grader.py`
(see `validate.py` for the exact command) and read `{"job_id","pass","detail"}`; `detail` holds a short failure reason usable as feedback.

## Validation (what `validate.py` proves)

For all 134 tasks: `start_state` fails, `reference` passes, and `reference` wrapped in prose + a markdown fence passes.
Additionally for the 79 SQL query tasks a "match nothing" mutant fails, and for the 69 order-insensitive SQL tasks a re-ordered reference passes.
Build-time guards (build fails otherwise): every query task has a non-empty expected result on at least 2 of 3 datasets, and every `sql_fix` buggy query differs from the reference on at least one dataset.

## Known limits

* Hidden data is generated from six fixed domains; schemas repeat across tasks (specs and queries are all different).
* `etl`/`ddl` references were checked against the tests, not independently against a second implementation; ambiguity was removed from specs by stating tie/edge rules explicitly.
* Candidate code can still read `/g` (grader source) in the container; it contains no task data.
* No mutation testing of hidden datasets beyond the sanity mutants above; a clever wrong query could in principle match all three datasets.
