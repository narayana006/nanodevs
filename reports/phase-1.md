# nanodevs: fake-model Docker proof

This is a pipeline milestone, not a model capability benchmark. No model weights, benchmark source files, new images or dependencies were downloaded. All project files and the uv virtualenv are inside `the project directory`.

## Verified results

- 27 standard-library unit tests pass on host Python 3.14.2.
- 10 original scripted fault scenarios run independently in each Docker tier, 20 fresh containers total. Every scenario produced its expected outcome.
- Each tier includes deliberate coding failures (exhausted candidates and hidden-test overfitting). Treating those as failures is part of the successful pipeline proof.
- Swap is disabled; cgroup memory limits and a two-CPU quota are verified inside each task and against Docker HostConfig.
- A separate, unscored 64 MiB fault container was OOM-killed with exit 137. The runner recorded OOMKilled=true and cleaned up its owned containers.

| Tier | Verified cap | Fault contracts satisfied | Largest observed peak | Mean recipe time | Real-model pass rate |
| --- | --- | --- | --- | --- | --- |
| lite | 2 GiB / 2 CPUs | 10/10 | 25.29 MiB | 0.415 s | Not measured |
| standard | 4 GiB / 2 CPUs | 10/10 | 25.15 MiB | 0.409 s | Not measured |

Peak memory includes the harness, fake model and checker processes, but no LLM exists in these runs. Peaks are read from cgroup memory.peak after task/check completion, before final report serialization. Recipe time includes baseline checks, model calls and candidate checks; container startup/control time is recorded separately. These tiny fake timings and memory figures say nothing about real-model fit or speed.

## Runtime

- Container Python: 3.13.18 (main, Nov  5 2026, 08:08:09) [GCC 14.2.0]
- Native Linux ARM64, libc glibc 2.41.
- Immutable cached image: `sha256:a9973520a9ba3d6ed77937b32ab205b8acbbb7a80cc7ee9bc533ca1777d13145`.
- Cached personal-project image was used only as a Python interpreter donor; its application entrypoint was overridden. This temporary fake-test setup is not a clean real-model measurement image.

## Implemented safeguards

AST context is limited to 50 relevant source lines, including referenced helpers/constants/imports. Function-only edits preserve the input signature and return annotation. Unknown/duplicate JSON fields, truncation and invalid Python are rejected. Fresh candidates always start from original source. Hidden checks run once on the first development-accepted candidate and never select the next sample. Baseline-passing or oversized-context fixtures are explicitly invalid, never reported as solved.

## Remaining work and approval gate

- Real-model inference, llama.cpp grammar enforcement and memory-fit testing have not run. The macOS llama.cpp executable is not a Linux container runtime. A native Linux ARM64 runtime must be verified separately; the latest GitHub release metadata query did not offer a matching prebuilt Linux ARM64 asset.
- QuixBugs assets are absent, so ten actual benchmark task IDs and their checksums are not yet frozen. The selection rule and proposed budgets are in contracts/evaluation-plan.json. Asset import and independent hidden-test validation precede model scoring.
- The pinned QuixBugs download proposal contains 175 files totalling 145654 bytes, from revision `4257f44b0ff1181dedaedee6a447e133219fcebf`. Every filename, source URL and size is in reports/download-metadata.json. Reference solutions must remain outside the eventual model-accessible task package.
- For real memory measurements, use private weight allocation (for example llama.cpp --no-mmap) or prove equivalent accounting. Reused file-backed pages can otherwise remain charged outside a later container; ordinary Docker memory.stats alone is not sufficient proof that all model weights count against each task cap. Record the exact load mode and cold-start/load time.
- Skills 2–5, playbook cards and real card/no-card comparisons are intentionally not implemented yet.
- The 30% continuation gate is **not evaluated**. There are no model pass-rate numbers to interpret.

## Evidence

- reports/unit-tests.txt
- reports/fake-docker.json (all attempts and per-task cgroup evidence)
- reports/docker-run.txt
- reports/runtime-metadata.json
- reports/download-metadata.json (metadata only; assets not downloaded)
