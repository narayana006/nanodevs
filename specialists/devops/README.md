# devops specialist - training-task factory

Machine-graded tasks for the `devops` LoRA specialist (Dockerfiles, docker-compose, Kubernetes manifests, CI pipelines,
shell scripts, Makefiles, Terraform-style config). Everything here is original, deterministic and offline: no model, no GPU,
no network, no downloads. Nothing is committed.

```
tasks.jsonl          the task set (generated from tasks_src/, one JSON object per line)
tasks_src/           task definitions, one module per domain (t_dockerfile, t_compose, t_k8s, t_ci, t_shell, t_makefile, t_terraform)
  _dsl.py            C()/Q()/T() helpers used to write tasks compactly
build_tasks.py       tasks_src/*.py -> tasks.jsonl
validate.py          start state must FAIL, reference must PASS (sandboxed); lints the schema
grade.py             grader API + CLI (make_prompt, extract_files, grade)
lib/yamlmini.py      safe YAML-subset parser (PyYAML is not in the image)
lib/hcl.py           small HCL2 parser for Terraform-style files
lib/rules.py         the rule library (Dockerfile / K8s / CI / Makefile / generic structured queries)
lib/grader_inner.py  runs INSIDE the sandbox container: evaluates rules and runs shell behaviour tests
```

## Task schema (`tasks.jsonl`)

| field | meaning |
|---|---|
| `id` | unique, `<domain-prefix>-<slug>` |
| `kind` | `write` (from spec), `fix` (broken/insecure -> correct), `harden` (apply security/reliability best practice), `convert` (shell -> Makefile, compose -> k8s, GH Actions -> GitLab, ...) |
| `domain` | `dockerfile`, `compose`, `k8s`, `ci`, `shell`, `makefile`, `terraform` |
| `difficulty` | `easy` / `medium` / `hard` |
| `instruction` | what the model is asked to do (never lists the hidden checks) |
| `files` | start state shown to the model: `{path: content}`; `{}` for pure write tasks |
| `outputs` | the file paths the model must return |
| `reference` | `{path: content}` reference solution (passes every check) |
| `checks` | hidden checks (below) |

Each check is `{"id", "type", "desc", "bug"?, "keep"?, ...type-specific args}`.
`bug: true` = this check fails on the start state (it is one of the injected violations; the check list *is* the violation list for fix/harden tasks).
`keep: true` = regression guard that must already pass on the start state (e.g. "the port mapping is still 8080").
A candidate passes a task only if ALL checks pass (there is no partial credit in `grade()["passed"]`; per-check results are returned for analysis/partial scoring).

### Check types (lib/rules.py)

* **Generic structured**: `q` queries a YAML/JSON/HCL file: `file`, `path` (dotted, `[*]`, `*`, quoted keys, ` | ` unions), `op`
  (`eq ne in not_in regex not_regex gte lte gt lt qty_lte qty_gte truthy falsy contains not_contains len_gte len_lte type exists missing`),
  `value`, `select` (pick documents of a multi-doc file, e.g. `{"kind": "Deployment"}`), `each` (apply to every element, e.g. every container), `mode` (`all`/`any`/`none`).
  Also `q_scan`, `docs`, `valid`, `contains`, `not_contains`, `lineset` (.dockerignore), `ordered`, `file_exists`.
* **Dockerfile** (`df_*`): pinned base (ARG-aware), non-root final `USER`, exec-form CMD/ENTRYPOINT, no `ADD` URL, HEALTHCHECK, multi-stage, apt hygiene,
  cache-friendly COPY/RUN order, secrets in ENV/ARG, `curl | sh`, generic `df_instr` / `df_instr_order`.
* **Kubernetes** (`k8s_*`): selector/template-label match, Service selector/targetPort resolution, probe ports, ConfigMap/PVC/volume reference resolution;
  everything else (resources, probes, securityContext, no `:latest`, RBAC wildcards, ...) through `q` with `each=spec.template.spec.containers[*]`.
* **CI** (`ci_*`): action pinning (SHA for third-party), untrusted `${{ }}` in `run:`, least-privilege `permissions`, `needs` graph validity; the rest through `q` (GitHub Actions and GitLab CI).
* **Compose**: `q` rules (healthchecks, `depends_on` conditions, privileged, loopback port binding, secrets, networks).
* **Makefile** (`mk_*`): parser + small planner that expands `make <target>` (prerequisites first, `$(VAR)`, `$@ $< $^`, `$$`, CLI overrides) so tests assert the command sequence.
* **Terraform**: HCL parsed to a dict, then `q` (resource attributes, nested blocks, variables, providers, policy documents); two JSON-answer reasoning tasks.
* **Shell**: `shellcheck` (real shellcheck 0.11 in `koalaman/shellcheck:stable`) AND `sh_behavior`: the script is executed in the sandbox against fixtures with stubbed
  commands (`kubectl`, `docker`, `curl`, `nc`, `sleep`, `df`, `mktemp`...; each stub logs its argv, so tests assert on calls, order and arguments). Case keys:
  `args env stdin files modes stubs rc stdout stdout_has stdout_not stdout_re stderr_re stderr_not out_files out_files_re no_files dirs_exist modes_after no_leftover_re calls_re calls_not calls_count`.

## Grading / sandbox

`grade.grade(task, candidate_files)` evaluates in ONE container at a time, both locked down like phase0/harness2.py:
`--network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 65534:65534 --memory 256m --cpus 1 --pids-limit 64`
(+ a 32 MB `/tmp` tmpfs mounted `exec` so stub commands can run). Images used (already local, nothing is pulled): `python:3.12-slim`
(stdlib only; the rule library parses YAML/HCL itself), `koalaman/shellcheck:stable`.

```python
from grade import load_tasks, make_prompt, extract_files, grade
t = load_tasks()[0]
prompt = make_prompt(t)                           # model input
res = grade(t, extract_files(model_answer_text))  # {"passed": bool, "checks": {id: [ok, msg]}}
```
Model answers are fenced code blocks whose first line is `# file: <path>` (one block per returned file).
CLI: `python grade.py TASK_ID answer.txt`.

## Validate

```
python validate.py            # rebuild tasks.jsonl, then for every task: start FAILS, reference PASSES (sandboxed, ~10 min)
python validate.py --fast     # host-only, no containers/shellcheck; static domains only make sense here (shell behaviour needs the sandbox)
python validate.py --domain shell --id sh-retry
```
For fix/harden tasks it also asserts every `bug` check fails on the start state and every `keep` check passes on it.

## Adding tasks
Add `T(...)` entries to `tasks_src/t_<domain>.py` (reference + checks), run `python validate.py --domain <d>`.
Keep checks about observable properties (behaviour, structure) rather than exact text, so any correct solution passes.

## Known limits
* The YAML/HCL parsers are subsets (no tags, complex keys, plain multi-line scalars). Candidates using unsupported YAML features fail the checks (`valid`).
* No real `docker build`, `kubectl apply --dry-run`, `terraform validate` or `make` run is possible (tools/binaries are not available offline); equivalents are structural rules and the Makefile planner.
* Shell behaviour tests run under the container's bash 5.2 / dash and GNU coreutils; scripts needing other tools (jq, curl, make) must be tested with stubs, as the tasks do.
