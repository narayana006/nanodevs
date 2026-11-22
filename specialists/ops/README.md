# ops specialist: training-task factory

Seeded, deterministic generator + machine graders for the `ops` model (SRE: incident triage, root cause, runbooks,
SLO math, on-call scripts). Stdlib only. No model, GPU, network or install is needed to build or validate.

    python generate.py            # rebuild tasks.jsonl (byte-identical every run; 174 tasks)
    python validate.py            # schema + determinism + reference passes + negatives fail (code tasks run on host)
    python validate.py --docker   # same, code tasks executed one container at a time in the locked-down sandbox

## Files

| file | role |
|---|---|
| `tasks.jsonl` | the materialized tasks (schema below) |
| `generate.py` | plan + materialization (`build()`, `dump()`); task seeds are fixed per slot |
| `scenarios.py` | incident scenario generator (kind `triage`) |
| `scripttasks.py` | log-analysis script tasks + fixture generator (kind `script`) |
| `slo.py` | SLO / burn-rate / capacity math (kind `slo`) |
| `runbooks.py` | runbook step selection and ordering (kind `runbook`) |
| `fixtasks.py` | buggy on-call helper with injectable bugs (kind `fix`) |
| `graders.py` | `grade(task, answer_text, sandbox="docker") -> {pass, score, detail}` |
| `runner.py` | stdlib-only runner executed inside the sandbox for `script` and `fix` |
| `validate.py` | proof that references pass and trivial/random/near-miss/mutant answers fail |

## tasks.jsonl schema (one JSON object per line)

| field | meaning |
|---|---|
| `id` | `ops-<kind>-<e/m/h>-<nnn>` |
| `kind` | `triage`, `script`, `slo`, `runbook`, `fix` |
| `difficulty` | `easy`, `medium`, `hard` |
| `seed` | integer seed of the generator slot (regenerate with `generate.build()`) |
| `inputs` | what the model may see. `inputs.prompt` is the complete prompt text; other keys are structured copies (e.g. `steps`, `facts`, `buggy_file`, `sample`) |
| `hidden` | ground truth + grading payload. Never show to the model |
| `reference_answer` | the answer text a perfect model would output (grades to pass, score 1.0) |
| `grader` | grader name (informational; use `graders.grade`) |

Counts: 174 = triage 66, script 30, slo 30, runbook 24, fix 24; each kind is split evenly easy/medium/hard (58 per tier).

### kind `triage` (a)
Prompt: ~46 to ~190 log lines `[L042] 05:41:39Z checkout ERROR msg` from 4 to 10 services plus three metric snapshots
(T-10m, T-5m, now). Answer: one JSON object
`{root_cause_service, root_cause_category, evidence_line_ids, first_safe_action, severity}`.
Fixed lists: categories `bad_deploy resource_exhaustion dependency_timeout config_drift certificate_expiry noisy_neighbor dns_failure cascading_failure`;
actions `rollback_deploy restart_service scale_out free_disk_space enable_circuit_breaker revert_config renew_certificate evict_noisy_workload failover_dns_resolver enable_load_shedding`;
severity `sev1..sev4` from the api-gateway `err_pct` in the "now" snapshot (>=25 / >=10 / >=2 / else). The prompt states the category definitions.
`resource_exhaustion` has four variants (memory, fd, cpu, disk) that map to different actions (`restart_service`, `restart_service`, `scale_out`, `free_disk_space`).
`hidden`: `root_cause_service`, `root_cause_category`, `first_safe_action`, `severity`, `evidence_ok_ids` (all planted root-evidence lines), `decoy_ids`
(planted red herrings), `n_lines`, `min_evidence_hits` (2), `max_evidence` (5), `variant`.
Grading is field by field (score = fraction of 5 fields correct; pass = all). Evidence is correct when ids exist, 2 to 5 distinct ids, at least 2 are
planted evidence lines, none is a decoy, and at least half are evidence lines.
Difficulty: easy = 4 services, ~45 lines, 1 decoy; medium = 6 to 7 services, ~100 lines, 2 decoys, a healthy DNS service, a decoy metric;
hard = 8 to 10 services, ~190 lines, 3 decoys; victims often show higher error rates than the root.
Decoys: cert expiring in weeks, a healthy deploy elsewhere, 80% disk/heap warnings, third-party timeout, benign config reload, failed cron, planned restart, unrelated batch job on another node.

### kind `script` (b)
Write `analyze.py` from a spec (formats `kv`, `json`, `text`; tasks: `counts`, `percentiles` (nearest rank), `windows` (epoch-aligned error-rate windows + alerts),
`burn` (multi-window burn rates + page/ticket decision), `incidents` (error grouping with gap), `topmsgs` (normalized top-K)). Answer: one python block starting `# file: analyze.py`.
`hidden.spec` = `{mode: "script", fixtures: [{argv, files, expect}]}`; 5 to 7 hidden fixtures per task (small, empty, large with malformed lines and out-of-order timestamps,
boundary/edge, medium; burn also has a spike-only and a slow-burn fixture). `expect` is produced by running the reference script, so reference == ground truth.
Score = fraction of fixtures with matching stdout JSON (float tolerance 1e-6); pass = all.

### kind `slo` (c)
Eight subtypes: error budget, burn rate, two-window page decision, multi-window alert thresholds, composite availability, budget policy/freeze, capacity (N+1, growth, Little's law), histogram quantile/SLI.
Answer: one JSON object with the named keys. `hidden`: `expected`, `tol_rel` (0.005), `tol_abs`, `subtype`. Floats within tolerance, ints and booleans exact, strings rejected.

### kind `runbook` (d)
A runbook (6 topics: DB failover, bad deploy rollback, cert expiry, disk full, Kafka lag, DNS) with randomly relabeled step IDs, applicability conditions over incident facts and prerequisites.
Answer `{"steps": [ids]}`: applicable steps only; a step runs after its selected prerequisites; ties go to the smallest ID (the lexicographically smallest topological order is unique).
Medium adds 1 and hard 3 cross-cutting steps (page IC, call secondary, security notification, emergency change approval). Exact match required; score otherwise at most 0.5 (set F1).

### kind `fix` (e)
10 on-call helper templates (df alerts, duration parser, budget remaining, rotation, backoff, flap paging, cert status, percentile, alert dedupe, quorum), each with 3 to 4 injectable bugs.
Easy = 1 bug, medium = 2 to 3 bugs, hard = two functions with 2 bugs each. Answer: full file in a block starting `# file: oncall.py`.
`hidden.spec.cases` = JSON call/expect cases computed from the correct source (12 to 30 per task). Generation asserts that every injected bug is caught by the cases on its own.

## Grading sandbox
`graders.sandbox_run` runs `runner.py` in `python:3.12-slim` with `--network none --read-only --cap-drop ALL --user 65534:65534 --memory 256m --cpus 1 --pids-limit 64`
(+ `no-new-privileges`), the work dir mounted read-only at `/w` (fixtures pre-written by the host). Use `sandbox="docker"` (default) for anything a model wrote.
`sandbox="local"` runs the same runner on the host and is only for trusted code (references, validate negatives).

## What validate.py checks
Schema; unique ids; >=150 tasks; byte-identical regeneration; every reference passes with score 1.0; empty / prose / `{}` / `[]` answers fail;
triage: 20 random valid-format answers per task fail, each single-field mutation of the reference fails with score 0.8, decoy evidence, single evidence id and over-long evidence fail;
slo: 5% error in any field fails, 0.1% passes, zeros and strings fail; runbook: reversed, missing step, all steps, ID-sorted and shuffled orders fail;
script: print-`{}`, crash, and hard-coded sample output fail, and textual mutants of the reference (off-by-one windows, `<=` vs `<`, wrong rank, ...) are all rejected;
fix: the unmodified buggy file fails and so does every "fixed all bugs but one" candidate.

## Known limits
- Triage evidence ids are matched against planted lines only; a model citing a valid but unplanted line counts as a miss (cap of 5 ids, at least half must be planted).
- `cascading_failure` vs `dependency_timeout` and `noisy_neighbor` vs `resource_exhaustion(cpu)` depend on the definitions given in the prompt.
- Message templates are finite (about 8 per category); lexical variety comes from topology, noise and numbers, not from free text.
