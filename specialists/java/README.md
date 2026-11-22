# specialists/java: training-task factory

124 original Java tasks (plain JDK, no Maven/Gradle), each with starting files, hidden tests and a reference solution.
Mirrors `phase0/harness2.py`: tasks with reference solutions + hidden tests, run in a locked-down container.

| kind | count | what the model gets |
|---|---|---|
| `fix` | 47 | buggy files + symptom; must make hidden tests pass |
| `implement` | 46 | stub files (compile, throw `UnsupportedOperationException`) + spec |
| `extend` | 31 | working files + instruction for new behaviour (often a new class) |

Difficulty: 33 easy, 62 medium, 29 hard. Topics: collections, streams, records, sealed types, generics, interfaces, enums,
exceptions, string processing, parsing, algorithms (DP, graphs, heaps, tries), concurrency, state machines.

## Files
- `tasks.jsonl` : the deliverable (generated, one JSON object per line).
- `tasks_fix.py`, `tasks_impl.py`, `tasks_ext.py`, `lib.py`, `build.py` : source of the tasks. `python3 build.py` regenerates `tasks.jsonl`.
- `runner.py` : compile+run backend (`host` or locked-down `docker`) and a reference `make_prompt`.
- `validate.py` : checks every task (reference passes, starting files fail).

## Schema (tasks.jsonl)
| field | type | meaning |
|---|---|---|
| `id` | str | unique, prefixed `fix-`/`impl-`/`ext-` |
| `kind` | `fix`\|`implement`\|`extend` | |
| `difficulty` | `easy`\|`medium`\|`hard` | |
| `files` | {name: source} | starting project shown to the model (all `.java`, default package) |
| `instruction` | str | symptom (fix) or spec/feature request (implement, extend) |
| `visible` | str | optional example snippet shown in the prompt (`implement`/`extend`) |
| `hidden_tests` | {name: source} | `HiddenTest.java`: a `main()` using a tiny hand-rolled harness (`ok`, `eq`, `thrown`, `fail`); prints `PASS` and exits 0, else prints `FAIL: ...` lines and exits 1 |
| `reference` | {name: source} | files to overlay on `files` (changed and new files only, full contents) to make the tests pass |
| `entry` | str | main class to run (`HiddenTest`) |
| `tags` | [str] | reserved, currently empty |

Grading a candidate: overlay the candidate's returned files on `files`, add `hidden_tests`, compile everything with
`javac --release 17`, run `java HiddenTest`; pass = exit code 0. `runner.task_files(task, candidate)` does the overlay and
`runner.run_task(files, entry, backend, image)` runs it. Candidates must not rename the tested classes/signatures;
the tests only use the public API stated in the instruction. Java 17 language level (records, sealed, switch expressions,
pattern `instanceof`); no preview features.

## Validate
```
python3 validate.py                                   # host javac, 4 jobs, no sandbox (reference code is ours)
python3 validate.py --backend docker --image eclipse-temurin:21-jdk   # sandboxed, one container at a time
```
Docker flags: `--network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 65534:65534 --memory 512m
--cpus 1 --pids-limit 128`, sources mounted read-only at `/w`, compile output in a `--tmpfs /out:exec`.
Use the docker backend for any model-generated code. A task is valid iff the reference passes AND the unmodified starting
files fail the hidden tests.
