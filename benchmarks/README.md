# Phase 0 benchmarks: choosing the base model

Two open models were compared on small, single-shot coding tasks that are graded by running real tests in a locked-down Docker sandbox (no network, read-only, all capabilities dropped, 256 MB, 1 CPU). All numbers below come from the raw files in `phase0/results/` and `phase0/results2/`.

Models (both Apache 2.0, both Q4_K_M GGUF, run with llama.cpp on an M1 Max):
- **Gemma 4 26B A4B** (Google, mixture of experts, about 4B active), thinking off.
- **Devstral Small 2 24B** (Mistral, dense).

## Round 1: 20 single-function bug fixes
| | Gemma 26B A4B | Devstral 24B |
|---|---|---|
| Passed on first try | 20/20 | 19/20 |
| Seconds per attempt | 2.5 | 11.5 |

Too easy to separate the models.

## Round 2: 30 harder multi-file tasks (fix, write, extend, write tests)
| First-try passes | Gemma 26B A4B | Devstral 24B |
|---|---|---|
| Bug fixing | 10/10 | 9/10 |
| Writing new code | 7/8 | 5/8 |
| Extending code | 6/6 | 5/6 |
| Writing tests (mutation-graded) | 4/6 | not recorded |
| Seconds per attempt | 12.8 | 141 |

Known limits, stated plainly:
- Devstral's results file holds 24 of the 30 tasks; the test-writing tasks were not recorded, so the totals are not comparable. On the 24 tasks both ran, Gemma passed 23 and Devstral 19.
- Devstral's answers were not saved (older harness version), so its misses cannot be inspected, and we did not tune its sampling settings.
- The per-attempt time gap may be inflated by memory pressure from running the models one after another.
- Retry counts (pass@k) in the early files used one fixed seed for every try and are not valid; only the first-try numbers above are used. The harness now uses a different seed per try and saves answers.
- These tasks are small and single-shot. They do not measure long agentic work, which Devstral is built for.

## Round 3: 132 python tasks (specialists/python), untrained base model
Gemma 4 26B A4B (Q4_K_M, no adapter), hidden tests run in the locked sandbox. Up to 4 attempts, first greedy, the rest sampled with fresh seeds.

| | First try | Pass within 4 |
|---|---|---|
| All 132 tasks | 116 (88%) | 120 (91%) |
| Bug fixing (38) | 36 | 36 |
| Writing new code (55) | 50 | 52 |
| Extending code (18) | 13 | 14 |
| Refactoring (21) | 17 | 18 |
| Easy (32) | 30 | 30 |
| Medium (73) | 66 | 67 |
| Hard (27) | 20 | 23 |

What this means: the base model is already strong on these tasks, so a trained python specialist has little room to show gains here. The 12 unsolved tasks and the hard tier are where a specialist can be measured. The 120 test-verified solutions are saved in `teacher/` as training data. Limits: single run, one model, tasks written by us (template-based in part), not an outside benchmark.

## Round 4: all ten specialist task sets, untrained base model
Same Gemma 4 26B A4B (Q4_K_M, no adapter), greedy, first try only, each task graded by that specialist's own grader. 60 tasks per set, sampled with a fixed seed across kinds and difficulties (python: all 132). Small samples: expect a few points of noise per cell. Per-task results and the passing answers are in `teacher/`.

| Specialist | First-try pass | Where it fails |
|---|---|---|
| java | 57/60 (95%) | 3 real misses |
| debugger | 55/60 (92%) | wrong root-cause label; the fix passed the hidden tests on 60/60 |
| python | 116/132 (88%) | hard tier 20/27 |
| data | 51/60 (85%) | etl 6/12; sql_write 21/24 |
| devops | 45/60 (75%) | write 11/18; 2 answers missing the code fence |
| ui | 42/60 (70%) | write 20/30; 2 answers missing the code fence |
| reviewer | 42/60 (70%) | finds only 16/30 planted bugs (right verdict, wrong line or category); 26/30 clean diffs approved |
| qa | 33/60 (55%) | regression 21/21, but improve 7/21 and tests 5/18 (mutation-graded) |
| ops | 31/60 (52%) | slo 0/12 (wrong arithmetic), runbook 3/12, script 8/12 |
| planner | 4/60 (7%) | 12 plans fail the format gate; the pass bar needs every component perfect (mean score 0.57) |

Limits: the qa sample over-represents the small kinds and its regression tasks are easy, so its headline number is inflated. Java prompts include the failing test output and exact signatures. Debugger tasks are templated, so the sample may include sibling tasks. Pass bars for debugger, reviewer and planner are stated in each runner. These are tasks we wrote, not an outside benchmark.

Reading: the base model is already strong on java, debugger, python and data. A trained specialist has the most room on planner, ops, qa, reviewer and ui.

## CPU-only speed (4 threads)
Gemma 26B A4B generates about 9.0 tokens/s and reads prompts at about 27 tokens/s. Devstral generates about 3.0 and reads at about 7.6. Memory use is about the same (14.2 to 14.3 GB).

## Reproduce
`phase0/validate2.py` checks that every task is sound (starting code fails, reference solution passes). `phase0/run_round2.sh` runs the models. See `phase0/harness2.py` for the sandbox and grading.

## Planner: first trained adapter vs base (held-out families)
Trained on 146 reference plans (rank 8, attention + dense MLP, 100 iterations), tested on 60 tasks from 7 families never seen in training. Same grader and prompts for both.

| | Base | Adapter |
|---|---|---|
| Strict pass (every component perfect) | 12/60 | 5/60 |
| Mean score | 0.665 | 0.793 |
| Plans failing the format gate | 7 | 4 |
| Acceptance criteria | 0.51 | 0.93 |
| Specialist choice | 0.87 | 0.95 |
| Step count | 0.73 | 0.58 |

Mixed result: plan quality and format improved, but the wrong number of steps cost strict passes. Not released. Reference plans are template-built, so part of the gain may be learning the template. Training stopped early (a GPU error at iteration 153; the iteration-100 checkpoint was used).

## In a CPU-only Docker container (Docker Desktop on an Apple M1 Max, linux/arm64)
Official llama.cpp server image, base model Gemma 4 26B A4B Q4_K_M (15.6 GB file), 4 CPUs, 22 GB memory limit, no GPU, no adapter.

| | Result |
|---|---|
| Fits and runs | yes; model loaded in 43 s from a local file |
| Memory used | 16.0 GiB |
| Generation | about 4.0 tokens/s (one cold 128-token request) |
| Prompt reading | about 5 tokens/s (one 29-token prompt; too short to be representative) |

Limits: one request, so treat the speeds as rough. This is slower than the 9 tokens/s measured directly on the host with 4 threads, probably because of the Docker Desktop virtual machine and a cold start. The 4, 8 and 16 GB tiers cannot hold this 15.6 GB model; small tiers need a smaller base model. Not yet tested: 8 to 16 CPUs, a warm run, long prompts, and adapters loaded.
