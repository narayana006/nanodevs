# tinycoder — step 1

A local experiment in verified Python coding with tiny existing models and a fixed Python recipe. No training, external model APIs or publishing.

**Status: fake-model pipeline only. No real model or QuixBugs accuracy results exist yet.**

The Docker proof is complete: 27 unit tests pass, and all 10 scripted fault scenarios behave as expected in each memory tier. See [the phase-1 report](reports/phase-1.md). These are not model accuracy results.

## What is implemented

- Skill 1's fixed loop: locate a named function with AST, collect its dependency context, request one exact JSON object, replace only that function, run development checks, and evaluate the first accepted candidate once on hidden checks.
- At most 50 source lines; the target name is given by the task manifest. This is function-local repair, not autonomous repository localization. Oversized contexts are rejected rather than silently truncated.
- Fresh candidates always start from unchanged source. Default maximum is 10 generations, with zero self-repair rounds in this first baseline. Every rejected output and transport failure consumes an attempt.
- One function-only edit; no file path is accepted from the model, signatures are preserved, Python is parsed before execution, and test data is never part of the proposed edit.
- Candidate subprocess isolation and deadlines, discarded stdout, fresh imports and cleanup of process groups.
- Per-task Docker cgroup limits: lite 2 GiB / 2-CPU quota, standard 4 GiB / 2-CPU quota; swap disabled. Harness, fake model and checker share the same cap. Containers have no network, read-only roots, a read-only project mount, no extra capabilities, and a disposable tmpfs workspace.
- Container cgroup `memory.peak`, CPU accounting, memory-event counters, per-task and per-container time, image identity, candidate logs, error reasons and Docker OOM state. Peaks are observed after task/check completion, before final JSON output. CPU quota is not a claim of matching the performance of an arbitrary x86 VPS.
- Ten original scripted fault fixtures: successful edit, failed test then fresh success, malformed JSON, truncated output, invalid Python, rejected boundary edit, checker timeout, exhausted candidates, hidden-test overfitting, and model transport error.

JSON Schema is the real-model transport contract; no llama.cpp decoding guarantee has been tested without an actual model. A future adapter must supply it to llama.cpp and enforce request deadlines. Grammar constraints do not prove code correctness or prevent truncation.

## No downloads so far

The virtualenv uses installed Python and the harness has no third-party dependencies. Fake Docker validation uses an existing cached ARM64 Python image as an interpreter donor with its application entrypoint overridden. No application code is invoked. It is a temporary pipeline-test environment, not the clean image for real model measurements. Image pulls are disabled and the exact local image ID is recorded.

Model weights, llama.cpp Linux binaries/build dependencies, a clean measurement image, and QuixBugs assets are **not downloaded**. Each needs explicit approval before acquisition. The host macOS llama.cpp binary cannot be used as the Linux container inference process. Real inference must run inside the same capped container, CPU-only for this experiment. Use private weight allocation (`--no-mmap`) or independently verify file-backed page accounting so shared warm model pages cannot escape the task cap; a host-side Metal or Ollama server does not qualify.

## Run the unit checks

A uv virtualenv already exists at `.venv`, with caches confined to `.uv-cache`.

```sh
mkdir -p .tmp
TMPDIR="$PWD/.tmp" .venv/bin/python -B -m unittest discover -s tests -v
```

## Run the Docker proof

Only use an already-cached Linux ARM64 image containing Python 3.11 or later. This command never pulls an image. Each scenario gets a fresh container and cgroup, so peaks do not carry across tasks. The optional 64 MiB OOM probe is a deliberate infrastructure fault test and is excluded from either tier's task results.

```sh
.venv/bin/python -B scripts/run_docker.py \
  --image ghcr.io/narayana006/incident-rehearsal-lab:0.1.0 \
  --probe-oom \
  --output reports/fake-docker.json
```

## Interpretation

`contracts_satisfied=10/10` means the harness correctly handled ten scripted scenarios, including intentional failures. **It does not mean a model solved ten tasks.** No 30% go/no-go decision can be made from fake runs. `model_pass_rate` remains null, and no benchmark tasks are silently substituted or skipped.

## Next gate, after this proof

1. Approve named QuixBugs assets and pin their upstream revision, licence and checksums. Freeze ten eligible task IDs, development/hidden checks and budgets before any model evaluation. The selection rule and limits are recorded in `contracts/evaluation-plan.json`; actual IDs are not yet frozen because assets are absent. Keep supplied reference programs out of the measured/model-accessible workspace. Independently review hidden tests and disclose benchmark contamination risk.
2. Approve specific GGUF files and the Linux inference runtime/image. Initial candidates: Qwen2.5-Coder-1.5B-Instruct Q4_K_M (official GGUF, about 1.12 GB; Apache-2.0) and Qwen3.5-4B Q4_K_M (ggml-org GGUF, about 3.03 GB; upstream Apache-2.0). Download sizes are not RAM requirements; confirm fit with short context before scoring. Do not quietly swap models or change tasks after seeing failures.
3. Add and verify the actual constrained-decoding transport, then run skill 1 on both tiers. Report raw counts, first-attempt success, bounded-search success, time, peak container memory, OOMs, timeouts and failure categories.
4. Only after reporting that pilot: skills 2–4, original playbook cards with their own tests, paired card/no-card runs, and five stretch tasks. Stretch decomposition is authored in task manifests, never planned by the model.

Generated code should be treated as untrusted. The container profile limits host access, but this prototype is not a formal adversarial anti-cheating sandbox. The full project is available to fake fixtures; real task packaging must withhold references and hidden expected outputs before real-model scoring.
