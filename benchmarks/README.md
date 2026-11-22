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

## CPU-only speed (4 threads)
Gemma 26B A4B generates about 9.0 tokens/s and reads prompts at about 27 tokens/s. Devstral generates about 3.0 and reads at about 7.6. Memory use is about the same (14.2 to 14.3 GB).

## Reproduce
`phase0/validate2.py` checks that every task is sound (starting code fails, reference solution passes). `phase0/run_round2.sh` runs the models. See `phase0/harness2.py` for the sandbox and grading.
