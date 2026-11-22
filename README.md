# tinycoder

Open, private, test-verified coding models small enough to run in one CPU-only Docker container.

Instead of one giant model, tinycoder uses **ten small customized models**, one per task, all built on a single shared open base model (Gemma 4 26B A4B, Apache 2.0). A plain-code router picks the right specialist, and every answer is checked by running real tests in a locked-down sandbox before it is kept.

| Model | Task |
|---|---|
| planner | split a request into ordered, parallel steps |
| python, java, ui, data | write, fix and extend code |
| devops | Dockerfiles, CI, Kubernetes, shell |
| ops | incident triage, SLOs, runbooks (SRE) |
| qa | write tests that catch bugs |
| debugger | find the root cause of a failure |
| reviewer | find real bugs in a diff |

## Status: early. Read this first
- Done: architecture, a validated task factory for each specialist (tasks with hidden tests or graders), the Phase 0 base-model benchmark, and a working training pipeline (LoRA on Gemma under MLX, converted to GGUF, hot-swapped in llama.cpp).
- **Not done: no trained specialist has been released, and none has been shown to beat the untrained base.** The smoke training run proves the pipeline only.
- Nothing here is a claim of matching Devin or any commercial agent.

## Task sets (1,548 validated tasks)
Each specialist has a seeded task set with hidden tests or graders and reference solutions; every start state fails and every reference passes.

| Specialist | Tasks | Notes |
|---|---|---|
| planner | 206 | graded on JSON schema, DAG validity, file coverage, ordering, parallelism |
| ops | 174 | incident triage, scripts, SLO math, runbooks, on-call fixes |
| qa | 183 | graded by mutation: tests must pass the correct code and kill every planted bug |
| reviewer | 180 | half planted-defect diffs, half clean diffs (false-positive check) |
| ui | 156 | JavaScript runs on host Node with its permission model, not Docker (weaker sandbox) |
| devops | 135 | structural checks plus shellcheck; no real `docker build`, `kubectl` or `terraform` runs |
| data | 134 | SQL, DDL, ETL, query plans on SQLite |
| python | 132 | plus the 50 Phase 0 tasks |
| java | 124 | validated in a JDK container |
| debugger | 124 | root cause plus fix; 31 bug families x 4 variants |

Known limits: many tasks are template-instantiated (reviewer, debugger, ops), so variety is lower than the count suggests; split train and eval by template or module. Difficulty labels are heuristic. The qa set was validated by its builder (183/183); the other sets were re-checked independently.

## Where to look
- [specs/ARCHITECTURE.md](specs/ARCHITECTURE.md): design, training recipe, what is and is not verified.
- [benchmarks/README.md](benchmarks/README.md): the base-model comparison, with its limits stated.
- `specialists/<name>/`: task set, grader and validation for each model.
- `train/`: data preparation, MLX to PEFT to GGUF adapter conversion.
- `phase0/`: benchmark harness and raw results. `docs/phase1-fake-model-pipeline.md`: the earlier sandbox pipeline.

## Reproduce a check
```bash
python3 phase0/validate2.py           # tasks are sound: start fails, reference passes
python3 specialists/planner/validate.py
```
Needs Docker (python:3.12-slim) for the sandboxed graders.

## Contributing
Issues and results from other hardware are welcome, especially CPU-only VM measurements.

License: Apache 2.0.
