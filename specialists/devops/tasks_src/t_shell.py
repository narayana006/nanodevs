import hashlib

from _dsl import C, T, d

TASKS = []
add = TASKS.append


def SC(f, **kw):
    return C("shellcheck", "shellcheck reports no findings", file=f, **kw)


def B(script, cases, desc="behaviour tests pass in the sandbox", **kw):
    return C("sh_behavior", desc, script=script, cases=cases, **kw)


def K(desc, f, regex, **kw):
    return C("contains", desc, file=f, regex=regex, **kw)


SLEEP = {"sleep": ""}

# ---------------------------------------------------------------------------------------------- write
S = "summarize.sh"
LOG = ("2024-05-01T10:00:00Z INFO start\n2024-05-01T10:00:01Z ERROR db timeout\n2024-05-01T10:00:02Z WARN slow query\n"
       "2024-05-01T10:00:03Z INFO ok\n2024-05-01T10:00:04Z ERROR ERROR in message text\n2024-05-01T10:00:05Z DEBUG noise INFO WARN\n")
add(T("sh-log-summary", "write", "shell", "easy", """
Write `summarize.sh` (bash). Usage: `summarize.sh LOGFILE` or `summarize.sh -` (read stdin). Log lines look like `2024-05-01T10:00:00Z LEVEL free text...`: the LEVEL is the 2nd whitespace-separated field.
Print exactly one line `ERROR=<n> WARN=<n> INFO=<n>` counting lines by LEVEL (other levels, and level words that merely appear inside the message text, are ignored). Exit codes: 2 on wrong usage (no/too many args),
1 if the file is not readable (message on stderr), 0 otherwise. Must be shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 LOGFILE|-" >&2
  exit 2
}

[ $# -eq 1 ] || usage
src=$1
if [ "$src" = "-" ]; then
  input=/dev/stdin
else
  [ -r "$src" ] || { echo "cannot read $src" >&2; exit 1; }
  input=$src
fi

awk '
  $2 == "ERROR" { e++ }
  $2 == "WARN"  { w++ }
  $2 == "INFO"  { i++ }
  END { printf "ERROR=%d WARN=%d INFO=%d\n", e, w, i }
' "$input"
""")},
 [SC(S), K("bash shebang", S, r"\A#!.*bash"),
  B(S, [dict(name="file", args=["app.log"], files={"app.log": LOG}, stdout="ERROR=2 WARN=1 INFO=2"),
        dict(name="stdin", args=["-"], stdin=LOG, stdout="ERROR=2 WARN=1 INFO=2"),
        dict(name="empty", args=["e.log"], files={"e.log": ""}, stdout="ERROR=0 WARN=0 INFO=0"),
        dict(name="missing", args=["nope.log"], rc=1, stderr_re=[r"\S"]),
        dict(name="no args", args=[], rc=2), dict(name="two args", args=["a", "b"], files={"a": "", "b": ""}, rc=2)])]))

S = "check_env.sh"
add(T("sh-env-check", "write", "shell", "easy", """
Write `check_env.sh` (bash, `set -euo pipefail` style safe even when variables are unset). `check_env.sh VAR1 VAR2 ...` verifies that every named environment variable is set AND non-empty.
If all are fine print `all set` and exit 0. Otherwise print `missing: ` followed by the missing names (in argument order, space separated) to STDERR and exit 1. With no arguments it prints `all set`.
Never print the variable values. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

missing=()
for name in "$@"; do
  if [ -z "${!name:-}" ]; then
    missing+=("$name")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "missing: ${missing[*]}" >&2
  exit 1
fi
echo "all set"
""")},
 [SC(S), K("uses strict mode", S, r"set -[a-z]*e[a-z]*u|set -euo|set -eu"),
  B(S, [dict(name="ok", args=["A", "B"], env={"A": "1", "B": "x"}, stdout="all set"),
        dict(name="missing two", args=["A", "B", "C"], env={"A": "1"}, rc=1, stderr_re=[r"^missing: B C$"], stdout_not=["all set"]),
        dict(name="empty counts as missing", args=["A"], env={"A": ""}, rc=1, stderr_re=[r"^missing: A$"]),
        dict(name="no args", args=[], stdout="all set"),
        dict(name="secret not printed", args=["TOKEN", "NOPE"], env={"TOKEN": "supersecret99"}, rc=1, stdout_not=["supersecret99"], stderr_not=["supersecret99"])])]))

S = "retry.sh"
FLAKY = 'n=$(cat count 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > count; [ "$n" -ge 3 ]\n'
add(T("sh-retry", "write", "shell", "medium", """
Write `retry.sh` (bash): `retry.sh ATTEMPTS DELAY command [args...]` runs the command up to ATTEMPTS times (ATTEMPTS must be a positive integer). Stop at the first success and exit 0.
After each failed attempt print `attempt <i>/<ATTEMPTS> failed (rc=<code>)` to stderr and, if more attempts remain, `sleep DELAY` (use the `sleep` command so it can be stubbed; never sleep after the last attempt).
If all attempts fail, exit with the exit code of the last attempt. Wrong usage (fewer than 3 args or non-numeric ATTEMPTS): message to stderr, exit 2. The command's arguments must be passed through exactly (quoting preserved). Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -uo pipefail

if [ $# -lt 3 ]; then
  echo "usage: $0 ATTEMPTS DELAY command [args...]" >&2
  exit 2
fi
attempts=$1
delay=$2
shift 2
case $attempts in
  '' | *[!0-9]* | 0) echo "ATTEMPTS must be a positive integer" >&2; exit 2 ;;
esac

rc=0
for ((i = 1; i <= attempts; i++)); do
  if "$@"; then
    exit 0
  else
    rc=$?
  fi
  echo "attempt $i/$attempts failed (rc=$rc)" >&2
  if [ "$i" -lt "$attempts" ]; then
    sleep "$delay"
  fi
done
exit "$rc"
""")},
 [SC(S),
  B(S, [dict(name="succeeds on 3rd", args=["5", "1", "bash", "flaky.sh"], files={"flaky.sh": FLAKY}, stubs=SLEEP, out_files={"count": "3"}, calls_count=2, calls_re=["^sleep 1$"], stderr_re=[r"attempt 1/5 failed \(rc=1\)"]),
        dict(name="gives up", args=["2", "1", "bash", "flaky.sh"], files={"flaky.sh": FLAKY}, stubs=SLEEP, rc=1, out_files={"count": "2"}, calls_count=1, stderr_re=[r"attempt 2/2 failed"]),
        dict(name="propagates exit code", args=["3", "0", "bash", "-c", "exit 7"], stubs=SLEEP, rc=7),
        dict(name="args quoting preserved", args=["1", "0", "bash", "-c", 'printf "%s|" "$@" > got', "x", "a b", "c"], stubs=SLEEP, out_files={"got": "a b|c|"}),
        dict(name="no sleep on first success", args=["3", "5", "true"], stubs=SLEEP, calls_count=0),
        dict(name="usage", args=["3", "1"], rc=2), dict(name="non numeric", args=["x", "1", "true"], rc=2)])]))

S = "rotate.sh"
BK = {f"bk/backup-2024-01-0{i}.tar.gz": "x" for i in range(1, 6)}
BK.update({"bk/notes.txt": "n", "bk/backup-2024-01-01.tar.gz.sig": "s", "bk/backup-2023-12-31 b.tar.gz": "sp"})
add(T("sh-rotate-backups", "write", "shell", "medium", """
Write `rotate.sh` (bash): `rotate.sh DIR KEEP` keeps the KEEP newest files matching `backup-*.tar.gz` directly inside DIR (newest = greatest name in byte order, as the names embed ISO dates) and deletes the rest.
Print `deleted <basename>` for every removed file, oldest first. Other files (notes, `.sig` files, subdirectories) must never be touched; file names may contain spaces. KEEP=0 deletes all matching backups.
Exit codes: 2 for wrong usage or non-numeric KEEP, 1 if DIR is not a directory, 0 otherwise (also when nothing needs deleting). Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 2 ] || { echo "usage: $0 DIR KEEP" >&2; exit 2; }
dir=$1
keep=$2
case $keep in
  '' | *[!0-9]*) echo "KEEP must be a non-negative integer" >&2; exit 2 ;;
esac
[ -d "$dir" ] || { echo "not a directory: $dir" >&2; exit 1; }

mapfile -t files < <(find "$dir" -maxdepth 1 -type f -name 'backup-*.tar.gz' -print | LC_ALL=C sort)
n=${#files[@]}
[ "$n" -gt "$keep" ] || exit 0

for f in "${files[@]:0:n-keep}"; do
  rm -f -- "$f"
  echo "deleted $(basename "$f")"
done
""")},
 [SC(S),
  B(S, [dict(name="keep 2", args=["bk", "2"], files=BK, stdout="deleted backup-2023-12-31 b.tar.gz\ndeleted backup-2024-01-01.tar.gz\ndeleted backup-2024-01-02.tar.gz\ndeleted backup-2024-01-03.tar.gz",
             no_files=["bk/backup-2024-01-01.tar.gz", "bk/backup-2024-01-03.tar.gz", "bk/backup-2023-12-31 b.tar.gz"],
             out_files={"bk/backup-2024-01-04.tar.gz": "x", "bk/backup-2024-01-05.tar.gz": "x", "bk/notes.txt": "n", "bk/backup-2024-01-01.tar.gz.sig": "s"}),
        dict(name="nothing to delete", args=["bk", "10"], files=BK, stdout="", out_files={"bk/backup-2024-01-01.tar.gz": "x"}),
        dict(name="keep 0", args=["bk", "0"], files=BK, stdout_has=["deleted backup-2024-01-05.tar.gz"], no_files=["bk/backup-2024-01-05.tar.gz"], out_files={"bk/notes.txt": "n"}),
        dict(name="not a dir", args=["nodir", "1"], rc=1), dict(name="bad keep", args=["bk", "-1"], files=BK, rc=2, out_files={"bk/backup-2024-01-01.tar.gz": "x"}),
        dict(name="usage", args=["bk"], rc=2)])]))

S = "wait_for.sh"
NC = 'n=$(cat nc_count 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > nc_count; [ "$n" -ge "${NC_OK_AT:-3}" ]\n'
add(T("sh-wait-for-port", "write", "shell", "medium", """
Write `wait_for.sh` (bash): `wait_for.sh HOST PORT TIMEOUT` waits until `nc -z HOST PORT` succeeds. Poll once per second using `sleep 1`; give up after TIMEOUT seconds of waiting.
On success print `HOST:PORT is up` (stdout) and exit 0 without sleeping if the first probe already works. On timeout print `timeout waiting for HOST:PORT after TIMEOUTs` to stderr and exit 1.
Wrong usage: exit 2. Do not use `timeout`/background tricks, just a loop. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 3 ] || { echo "usage: $0 HOST PORT TIMEOUT" >&2; exit 2; }
host=$1
port=$2
timeout=$3

elapsed=0
while ! nc -z "$host" "$port"; do
  if [ "$elapsed" -ge "$timeout" ]; then
    echo "timeout waiting for $host:$port after ${timeout}s" >&2
    exit 1
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
echo "$host:$port is up"
""")},
 [SC(S),
  B(S, [dict(name="up on 3rd probe", args=["db", "5432", "10"], stubs={"nc": NC, "sleep": ""}, stdout="db:5432 is up", calls_re=["^nc -z db 5432$", "^sleep 1$"], out_files={"nc_count": "3"}),
        dict(name="immediately up", args=["db", "5432", "10"], env={"NC_OK_AT": "1"}, stubs={"nc": NC, "sleep": ""}, stdout="db:5432 is up", calls_not=["^sleep"]),
        dict(name="timeout", args=["db", "5432", "3"], env={"NC_OK_AT": "99"}, stubs={"nc": NC, "sleep": ""}, rc=1, stderr_re=[r"timeout waiting for db:5432 after 3s"], calls_re=["^sleep 1$"], stdout_not=["is up"]),
        dict(name="usage", args=["db", "5432"], rc=2)])]))

S = "cleanup.sh"
DOCKER = 'if [ "$1" = ps ]; then printf "a1\\nb2\\n"; fi\n'
add(T("sh-docker-cleanup", "write", "shell", "medium", """
Write `cleanup.sh` (bash) that removes exited Docker containers safely. It lists them with `docker ps -aq --filter status=exited`. Default is a DRY RUN: for each container id print `would remove <id>` and call nothing else.
With `--yes` it runs `docker rm <id>` for each id (one call per id, output of docker rm suppressed) and prints `removed <id>`. If there are no exited containers print `nothing to remove`.
Any other argument: usage message on stderr and exit 2. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

apply=0
case "${1:-}" in
  "") ;;
  --yes) apply=1 ;;
  *) echo "usage: $0 [--yes]" >&2; exit 2 ;;
esac

mapfile -t ids < <(docker ps -aq --filter status=exited)
if [ "${#ids[@]}" -eq 0 ]; then
  echo "nothing to remove"
  exit 0
fi

for id in "${ids[@]}"; do
  if [ "$apply" -eq 1 ]; then
    docker rm "$id" > /dev/null
    echo "removed $id"
  else
    echo "would remove $id"
  fi
done
""")},
 [SC(S),
  B(S, [dict(name="dry run", args=[], stubs={"docker": DOCKER}, stdout="would remove a1\nwould remove b2", calls_not=["^docker rm"], calls_re=[r"^docker ps .*exited"]),
        dict(name="apply", args=["--yes"], stubs={"docker": DOCKER}, stdout="removed a1\nremoved b2", calls_re=["^docker rm a1$", "^docker rm b2$"], calls_count=3),
        dict(name="none", args=["--yes"], stubs={"docker": "true"}, stdout="nothing to remove", calls_not=["^docker rm"]),
        dict(name="bad arg", args=["--force"], stubs={"docker": DOCKER}, rc=2, calls_count=0)])]))

S = "deploy.sh"
KUBECTL = 'case "$*" in *"rollout status"*) [ "${STUB_FAIL:-}" = 1 ] && exit 1;; esac\nexit 0\n'


def line(*parts):
    return "^kubectl " + "".join(f"(?=.*{p})" for p in parts) + ".*$"


add(T("sh-deploy-guarded", "write", "shell", "hard", """
Write `deploy.sh` (bash): `deploy.sh ENV VERSION`. ENV must be `staging` or `prod`; VERSION must look like `v1.2.3` (v + three dot-separated numbers). Anything else: usage on stderr, exit 2, no kubectl calls.
Deploying to `prod` additionally requires the environment variable `CONFIRM=yes`, otherwise print `refusing to deploy to prod without CONFIRM=yes` to stderr and exit 3 (no kubectl calls).
Deploy: `kubectl -n ENV set image deployment/app app=registry.example.com/app:VERSION`, then `kubectl -n ENV rollout status deployment/app --timeout=120s`.
If the rollout status command fails: print `rollout failed, rolling back` to stderr, run `kubectl -n ENV rollout undo deployment/app` and exit 1. On success print `deployed VERSION to ENV`. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 staging|prod vMAJOR.MINOR.PATCH" >&2
  exit 2
}

[ $# -eq 2 ] || usage
env=$1
version=$2
case $env in
  staging | prod) ;;
  *) usage ;;
esac
[[ $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || usage

if [ "$env" = prod ] && [ "${CONFIRM:-}" != yes ]; then
  echo "refusing to deploy to prod without CONFIRM=yes" >&2
  exit 3
fi

image="registry.example.com/app:$version"
kubectl -n "$env" set image deployment/app app="$image"
if ! kubectl -n "$env" rollout status deployment/app --timeout=120s; then
  echo "rollout failed, rolling back" >&2
  kubectl -n "$env" rollout undo deployment/app
  exit 1
fi
echo "deployed $version to $env"
""")},
 [SC(S),
  B(S, [dict(name="staging ok", args=["staging", "v1.2.3"], stubs={"kubectl": KUBECTL}, stdout="deployed v1.2.3 to staging",
             calls_re=[line("staging", "set image", r"deployment/app", r"app=registry\.example\.com/app:v1\.2\.3"), line("staging", "rollout status", r"deployment/app", r"--timeout=120s")], calls_not=["rollout undo"]),
        dict(name="prod needs confirm", args=["prod", "v1.2.3"], stubs={"kubectl": KUBECTL}, rc=3, stderr_re=[r"refusing to deploy to prod without CONFIRM=yes"], calls_count=0),
        dict(name="prod confirmed", args=["prod", "v2.0.10"], env={"CONFIRM": "yes"}, stubs={"kubectl": KUBECTL}, stdout="deployed v2.0.10 to prod", calls_re=[line(r"\bprod\b", "set image", r"app:v2\.0\.10")]),
        dict(name="confirm must be exactly yes", args=["prod", "v1.0.0"], env={"CONFIRM": "true"}, stubs={"kubectl": KUBECTL}, rc=3, calls_count=0),
        dict(name="bad version", args=["staging", "1.2.3"], stubs={"kubectl": KUBECTL}, rc=2, calls_count=0),
        dict(name="bad version 2", args=["staging", "v1.2"], stubs={"kubectl": KUBECTL}, rc=2, calls_count=0),
        dict(name="bad env", args=["dev", "v1.2.3"], stubs={"kubectl": KUBECTL}, rc=2, calls_count=0),
        dict(name="rollback", args=["staging", "v1.2.3"], env={"STUB_FAIL": "1"}, stubs={"kubectl": KUBECTL}, rc=1, stderr_re=[r"rollout failed, rolling back"], stdout_not=["deployed"],
             calls_re=[line("set image"), line("rollout status"), line("staging", "rollout undo", "deployment/app")])])]))

S = "tool.sh"
add(T("sh-getopts-cli", "write", "shell", "medium", """
Write `tool.sh` (bash) with a proper option parser built on `getopts`: options `-e ENV` (default `dev`), `-n COUNT` (default `1`, must be digits only), `-v` (verbose flag), `-h` (help), plus an optional positional FILE (may contain spaces).
Print exactly one line: `env=<env> count=<count> verbose=<0|1> file=<file or none>`. Invalid usage (unknown option, missing option argument, non-numeric count, `-h`) prints a usage line starting with `usage:` to stderr and exits 2. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 [-e ENV] [-n COUNT] [-v] [FILE]" >&2
  exit 2
}

env=dev
count=1
verbose=0
while getopts ":e:n:vh" opt; do
  case $opt in
    e) env=$OPTARG ;;
    n) count=$OPTARG ;;
    v) verbose=1 ;;
    h) usage ;;
    :) echo "option -$OPTARG requires an argument" >&2; usage ;;
    *) echo "unknown option -$OPTARG" >&2; usage ;;
  esac
done
shift $((OPTIND - 1))

case $count in
  '' | *[!0-9]*) echo "count must be numeric" >&2; usage ;;
esac

file=${1:-none}
echo "env=$env count=$count verbose=$verbose file=$file"
""")},
 [SC(S), K("uses getopts", S, r"\bgetopts\b"),
  B(S, [dict(name="all options", args=["-e", "prod", "-n", "3", "-v", "data.csv"], stdout="env=prod count=3 verbose=1 file=data.csv"),
        dict(name="defaults", args=[], stdout="env=dev count=1 verbose=0 file=none"),
        dict(name="file with space", args=["my file.csv"], stdout="env=dev count=1 verbose=0 file=my file.csv"),
        dict(name="options after nothing", args=["-v", "-n", "10"], stdout="env=dev count=10 verbose=1 file=none"),
        dict(name="unknown option", args=["-x"], rc=2, stderr_re=[r"usage:"]), dict(name="non numeric", args=["-n", "abc"], rc=2, stderr_re=[r"usage:"]),
        dict(name="missing arg", args=["-e"], rc=2, stderr_re=[r"usage:"]), dict(name="help", args=["-h"], rc=2, stderr_re=[r"usage:"])])]))

S = "scan.sh"
add(T("sh-secret-scan", "write", "shell", "medium", """
Write `scan.sh` (bash): `scan.sh DIR` scans all files under DIR recursively (skip binary files and any `.git` directory) for likely secrets: AWS access key ids (`AKIA` + 16 uppercase letters/digits),
PEM private key headers (`BEGIN PRIVATE KEY`, `BEGIN RSA PRIVATE KEY`, `BEGIN EC PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY`), and assignments like `password = x`, `passwd=x`, `secret: ` is NOT required - only `=` assignments of password/passwd/secret with a non-empty value
(case-insensitive, optional spaces around `=`). Output one `path:line` per finding (sorted, NEVER the matching content), exit 1 if anything was found. Otherwise print `clean` and exit 0. Usage error (not exactly one existing directory): exit 2. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 1 ] && [ -d "$1" ] || { echo "usage: $0 DIR" >&2; exit 2; }

hits=$(grep -rnIiE \
  --exclude-dir=.git \
  -e 'AKIA[0-9A-Z]{16}' \
  -e 'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY' \
  -e '(password|passwd|secret)[[:space:]]*=[[:space:]]*[^[:space:]]+' \
  "$1" | cut -d: -f1,2 | sort || true)

if [ -n "$hits" ]; then
  echo "$hits"
  exit 1
fi
echo "clean"
""")},
 [SC(S),
  B(S, [dict(name="findings", args=["src"], files={"src/app.env": "HOST=x\nPASSWORD = hunter2\n", "src/k.txt": "a\nb\nkey AKIAABCDEFGHIJKLMNOP end\n", "src/ok.txt": "nothing here\n",
                                                  "src/.git/config": "password = gitsecret\n", "src/deep/pem.key": "-----BEGIN RSA PRIVATE KEY-----\nabc\n", "src/empty.cfg": "password =\n"},
             rc=1, stdout="src/app.env:2\nsrc/deep/pem.key:1\nsrc/k.txt:3", stdout_not=["hunter2", "AKIA", "gitsecret"]),
        dict(name="clean", args=["src"], files={"src/a.txt": "hello\n", "src/b/c.txt": "passwords are great\n"}, stdout="clean"),
        dict(name="not a dir", args=["nope"], rc=2), dict(name="usage", args=[], rc=2)])]))

S = "poll.sh"
CURL = 'code=$(head -n1 codes 2>/dev/null || true)\nsed -i 1d codes 2>/dev/null || true\necho "${code:-000}"\n'
add(T("sh-health-poll", "write", "shell", "medium", """
Write `poll.sh` (bash): `poll.sh URL ATTEMPTS` polls a health endpoint with `curl -s -o /dev/null -w '%{http_code}' --max-time 5 URL` (the status code is read from curl's stdout; a failing curl counts as code 000).
HTTP 200 means healthy: print `healthy after <i> attempt(s)` and exit 0. Otherwise print `attempt <i>: HTTP <code>` to stderr and, if attempts remain, run `sleep 2`. After the last failed attempt print `unhealthy: URL` to stderr and exit 1.
Wrong usage: exit 2. `set -e` must not abort the script when curl fails. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 2 ] || { echo "usage: $0 URL ATTEMPTS" >&2; exit 2; }
url=$1
attempts=$2

for ((i = 1; i <= attempts; i++)); do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" || true)
  if [ "$code" = 200 ]; then
    echo "healthy after $i attempt(s)"
    exit 0
  fi
  echo "attempt $i: HTTP ${code:-000}" >&2
  if [ "$i" -lt "$attempts" ]; then
    sleep 2
  fi
done
echo "unhealthy: $url" >&2
exit 1
""")},
 [SC(S),
  B(S, [dict(name="recovers", args=["http://svc/health", "5"], files={"codes": "503\n503\n200\n"}, stubs={"curl": CURL, "sleep": ""}, stdout="healthy after 3 attempt(s)", stderr_re=[r"attempt 1: HTTP 503"], calls_re=["^curl .*http://svc/health$", "^sleep 2$", "^sleep 2$", "^curl"]),
        dict(name="gives up", args=["http://svc/health", "2"], files={"codes": "500\n502\n"}, stubs={"curl": CURL, "sleep": ""}, rc=1, stderr_re=[r"unhealthy: http://svc/health"], stdout_not=["healthy after"]),
        dict(name="curl failure is code 000", args=["http://svc/health", "1"], files={"codes": ""}, stubs={"curl": CURL + "exit 7\n", "sleep": ""}, rc=1, stderr_re=[r"attempt 1: HTTP 000|attempt 1: HTTP"]),
        dict(name="first try", args=["http://svc/health", "3"], files={"codes": "200\n"}, stubs={"curl": CURL, "sleep": ""}, stdout="healthy after 1 attempt(s)", calls_not=["^sleep"]),
        dict(name="usage", args=["http://svc/health"], rc=2)])]))

S = "locked.sh"
add(T("sh-cron-lock", "write", "shell", "hard", """
Write `locked.sh` (bash): `locked.sh command [args...]` runs the command while holding a lock directory (create it atomically with `mkdir`) at `$LOCK_DIR` (default `/tmp/locked.lock`) so cron jobs never overlap.
If the lock is already held: print `already running (lock <path>)` to stderr, exit 75, and do NOT run the command and do NOT remove the other process's lock. Otherwise run the command and exit with ITS exit code.
The lock must be released (directory removed) in every case where we acquired it: success, command failure, and when the script is interrupted by SIGTERM/SIGINT (use `trap`). No arguments: usage, exit 2. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -uo pipefail

[ $# -ge 1 ] || { echo "usage: $0 command [args...]" >&2; exit 2; }
lock=${LOCK_DIR:-/tmp/locked.lock}

if ! mkdir "$lock" 2> /dev/null; then
  echo "already running (lock $lock)" >&2
  exit 75
fi
trap 'rmdir "$lock"' EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

"$@"
""")},
 [SC(S), K("uses trap", S, r"\btrap\b"),
  B(S, [dict(name="runs and releases", args=["bash", "-c", "echo ran >> out.txt"], env={"LOCK_DIR": "lk"}, out_files={"out.txt": "ran"}, no_files=["lk"]),
        dict(name="propagates failure and releases", args=["bash", "-c", "echo ran >> out.txt; exit 3"], env={"LOCK_DIR": "lk"}, rc=3, out_files={"out.txt": "ran"}, no_files=["lk"]),
        dict(name="lock held", args=["bash", "-c", "echo ran >> out.txt"], env={"LOCK_DIR": "lk"}, files={"lk/owner": "pid 1"}, rc=75, stderr_re=[r"already running \(lock lk\)"], no_files=["out.txt"], out_files={"lk/owner": "pid 1"}),
        dict(name="holds the lock while running", args=["bash", "-c", "test -d lk && echo held >> out.txt"], env={"LOCK_DIR": "lk"}, out_files={"out.txt": "held"}),
        dict(name="released on SIGTERM", args=["bash", "-c", "kill -TERM $PPID; sleep 1"], env={"LOCK_DIR": "lk"}, rc=143, no_files=["lk"]),
        dict(name="usage", args=[], rc=2)])]))

S = "csv_to_env.sh"
CSV = "key,value\nDB_HOST,db.internal\nGREETING,hello world\nQUOTE,it's fine\nCSV,a,b,c\n\n# comment\nEMPTY,\n1BAD,x\nNOCOMMA\n"
add(T("sh-csv-to-env", "write", "shell", "hard", """
Write `csv_to_env.sh` (bash): `csv_to_env.sh FILE.csv` converts a two-column CSV (`key,value`, first line is a header) into shell-safe export lines `export KEY='value'` on stdout.
Rules: skip the header, blank lines and lines starting with `#`; the key is everything before the FIRST comma and must match `[A-Za-z_][A-Za-z0-9_]*`; the value is everything after it (it may contain commas, spaces, `=`) and is single-quoted
with embedded single quotes escaped as `'\\''`; tolerate CRLF line endings; a last line without trailing newline still counts. Invalid lines (bad key or no comma) are reported as `invalid line: <line>` on stderr, skipped, and make the final exit code 1.
Unreadable/missing file or no argument: exit 2. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 1 ] && [ -r "$1" ] || { echo "usage: $0 FILE.csv" >&2; exit 2; }

first=1
rc=0
while IFS= read -r line || [ -n "$line" ]; do
  line=${line%$'\r'}
  if [ "$first" -eq 1 ]; then
    first=0
    continue
  fi
  case $line in
    '' | '#'*) continue ;;
  esac
  key=${line%%,*}
  value=${line#*,}
  if [ "$key" = "$line" ] || [[ ! $key =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "invalid line: $line" >&2
    rc=1
    continue
  fi
  value=${value//\'/\'\\\'\'}
  printf "export %s='%s'\n" "$key" "$value"
done < "$1"
exit "$rc"
""")},
 [SC(S),
  B(S, [dict(name="mixed", args=["in.csv"], files={"in.csv": CSV}, rc=1,
             stdout="export DB_HOST='db.internal'\nexport GREETING='hello world'\nexport QUOTE='it'\\''s fine'\nexport CSV='a,b,c'\nexport EMPTY=''", stderr_re=[r"invalid line: 1BAD,x", r"invalid line: NOCOMMA"]),
        dict(name="crlf and no trailing newline", args=["w.csv"], files={"w.csv": "key,value\r\nA,b c\r\nZ,last"}, stdout="export A='b c'\nexport Z='last'"),
        dict(name="value with equals and dollar", args=["x.csv"], files={"x.csv": "k,v\nURL,http://h/?a=1&b=$HOME\n"}, stdout="export URL='http://h/?a=1&b=$HOME'"),
        dict(name="missing file", args=["nope.csv"], rc=2), dict(name="no args", args=[], rc=2)])]))

S = "bump.sh"
add(T("sh-version-bump", "write", "shell", "medium", """
Write `bump.sh` (bash): `bump.sh major|minor|patch FILE` reads a semantic version `X.Y.Z` (surrounding whitespace/newline allowed) from FILE, increments the requested part (resetting lower parts to 0), writes the new version plus newline back to FILE and prints it.
Strict semver: no leading zeros in any part (`1.09.0` is invalid) and exactly three parts. Invalid version content or missing file: message on stderr, exit 1 and the file is left unchanged. Unknown level or wrong argument count: exit 2.
Beware of octal interpretation in shell arithmetic. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 2 ] || { echo "usage: $0 major|minor|patch FILE" >&2; exit 2; }
level=$1
file=$2
case $level in
  major | minor | patch) ;;
  *) echo "unknown level: $level" >&2; exit 2 ;;
esac
[ -f "$file" ] || { echo "no such file: $file" >&2; exit 1; }

current=$(tr -d '[:space:]' < "$file")
re='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
if [[ ! $current =~ $re ]]; then
  echo "invalid version: $current" >&2
  exit 1
fi
major=${BASH_REMATCH[1]}
minor=${BASH_REMATCH[2]}
patch=${BASH_REMATCH[3]}

case $level in
  major) major=$((major + 1)); minor=0; patch=0 ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  patch) patch=$((patch + 1)) ;;
esac
new="$major.$minor.$patch"
echo "$new" > "$file"
echo "$new"
""")},
 [SC(S),
  B(S, [dict(name="patch", args=["patch", "VERSION"], files={"VERSION": "1.4.9\n"}, stdout="1.4.10", out_files={"VERSION": "1.4.10"}),
        dict(name="minor", args=["minor", "VERSION"], files={"VERSION": "1.4.9\n"}, stdout="1.5.0", out_files={"VERSION": "1.5.0"}),
        dict(name="major", args=["major", "VERSION"], files={"VERSION": "  1.4.9  \n"}, stdout="2.0.0", out_files={"VERSION": "2.0.0"}),
        dict(name="leading zero rejected", args=["patch", "VERSION"], files={"VERSION": "1.09.0\n"}, rc=1, out_files={"VERSION": "1.09.0"}),
        dict(name="two parts rejected", args=["patch", "VERSION"], files={"VERSION": "1.4\n"}, rc=1, out_files={"VERSION": "1.4"}),
        dict(name="zero ok", args=["patch", "VERSION"], files={"VERSION": "0.0.0\n"}, stdout="0.0.1"),
        dict(name="missing file", args=["patch", "NOPE"], rc=1), dict(name="bad level", args=["huge", "VERSION"], files={"VERSION": "1.0.0\n"}, rc=2)])]))

S = "disk_alert.sh"
DF = r"""cat <<'EOF'
Filesystem     1024-blocks      Used Available Capacity Mounted on
/dev/sda1           100000     91000      9000      91% /
tmpfs                 5000         0      5000       0% /dev/shm
/dev/sdb1           200000    170000     30000      85% /data
/dev/sdc1           200000     50000    150000      25% /mnt/my disk
EOF
"""
add(T("sh-disk-alert", "write", "shell", "easy", """
Write `disk_alert.sh` (bash): `disk_alert.sh THRESHOLD` (integer percent) parses `df -P` output and prints `ALERT <mountpoint> <use%>` (e.g. `ALERT /data 85%`) for every filesystem whose use is STRICTLY greater than THRESHOLD, in df order.
Mount points may contain spaces. If any alert was printed exit 1; otherwise print `ok` and exit 0. Non-integer or missing THRESHOLD: exit 2. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $0 THRESHOLD" >&2; exit 2; }
case $1 in
  '' | *[!0-9]*) echo "THRESHOLD must be an integer" >&2; exit 2 ;;
esac

alerts=$(df -P | awk -v t="$1" '
  NR > 1 {
    pct = $5
    sub(/%/, "", pct)
    if (pct + 0 > t) {
      mount = $6
      for (i = 7; i <= NF; i++) mount = mount " " $i
      print "ALERT " mount " " $5
    }
  }')

if [ -n "$alerts" ]; then
  echo "$alerts"
  exit 1
fi
echo "ok"
""")},
 [SC(S),
  B(S, [dict(name="threshold 80", args=["80"], stubs={"df": DF}, rc=1, stdout="ALERT / 91%\nALERT /data 85%"),
        dict(name="strictly greater", args=["85"], stubs={"df": DF}, rc=1, stdout="ALERT / 91%"),
        dict(name="space in mountpoint", args=["20"], stubs={"df": DF}, rc=1, stdout="ALERT / 91%\nALERT /data 85%\nALERT /mnt/my disk 25%"),
        dict(name="all ok", args=["95"], stubs={"df": DF}, stdout="ok"),
        dict(name="bad threshold", args=["abc"], stubs={"df": DF}, rc=2), dict(name="usage", args=[], stubs={"df": DF}, rc=2)])]))

# ---------------------------------------------------------------------------------------------- fix
S = "copy_logs.sh"
add(T("sh-fix-unquoted-copy", "fix", "shell", "easy", """
`copy_logs.sh SRC DEST` copies `*.log` files from SRC to DEST (creating DEST), but it breaks on paths containing spaces, and when SRC has no logs it errors out. Fix it (quote correctly, handle the no-match case) and make it print
`copied <N> file(s) to <DEST>` where N is the number of files copied. Other files in SRC are not copied. Usage error (not exactly 2 args): exit 2. The script must be shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 2 ] || { echo "usage: $0 SRC DEST" >&2; exit 2; }
src=$1
dest=$2

mkdir -p -- "$dest"
shopt -s nullglob
count=0
for f in "$src"/*.log; do
  cp -- "$f" "$dest"/
  count=$((count + 1))
done
echo "copied $count file(s) to $dest"
""")},
 [SC(S, bug=True), B(S, [dict(name="spaces", args=["my logs", "out dir"], files={"my logs/a b.log": "A", "my logs/c.log": "C", "my logs/x.txt": "X"}, stdout="copied 2 file(s) to out dir",
                              out_files={"out dir/a b.log": "A", "out dir/c.log": "C"}, no_files=["out dir/x.txt"]),
                         dict(name="no logs", args=["empty", "dst"], files={"empty/x.txt": "X"}, stdout="copied 0 file(s) to dst", dirs_exist=["dst"]),
                         dict(name="usage", args=["only-one"], rc=2)], bug=True)],
 start={S: d(r"""
#!/bin/bash
src=$1
dest=$2
mkdir -p $dest
for f in $src/*.log; do
  cp $f $dest/
done
echo copied to $dest
""")}))

S = "cleanup_build.sh"
add(T("sh-fix-dangerous-rm", "fix", "shell", "medium", """
`cleanup_build.sh DIR` empties a build directory. Today, running it without an argument wipes the caller's HOME, and an unset/odd argument can delete the wrong things (`cd` failures are ignored, dotfiles survive).
Make it safe: strict mode, exactly one argument (else exit 2 without deleting anything), the argument must be an existing directory (else exit 1), refuse `/` and empty strings (exit 2), never continue after a failed `cd`,
remove ALL contents including hidden files but keep the directory itself, work with names containing spaces. Print `cleaned <DIR>` on success. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $0 DIR" >&2; exit 2; }
dir=$1
if [ -z "$dir" ] || [ "$dir" = "/" ]; then
  echo "refusing to clean '$dir'" >&2
  exit 2
fi
[ -d "$dir" ] || { echo "not a directory: $dir" >&2; exit 1; }

find "$dir" -mindepth 1 -delete
echo "cleaned $dir"
""")},
 [SC(S, bug=True),
  B(S, [dict(name="no argument must not touch cwd/HOME", args=[], files={"precious.txt": "keep"}, rc=2, out_files={"precious.txt": "keep"}),
        dict(name="empty string argument", args=[""], files={"precious.txt": "keep"}, rc=2, out_files={"precious.txt": "keep"}),
        dict(name="missing dir", args=["nope"], files={"precious.txt": "keep"}, rc=1, out_files={"precious.txt": "keep"}),
        dict(name="cleans everything incl. hidden", args=["my build"], files={"my build/a.o": "1", "my build/.cache": "2", "my build/sub/b.o": "3", "precious.txt": "keep"}, stdout="cleaned my build",
             no_files=["my build/a.o", "my build/.cache", "my build/sub/b.o"], dirs_exist=["my build"], out_files={"precious.txt": "keep"})], bug=True)],
 start={S: d(r"""
#!/bin/bash
BUILD_DIR=$1
cd $BUILD_DIR
rm -rf *
echo cleaned $BUILD_DIR
""")}))

S = "report.sh"
DATA = "fig\napple\nfig\npear\nfig\napple\nkiwi\nfig\npear\napple\n"
MKTEMP = 'if [ "${1:-}" = "-d" ]; then d="$TMPDIR/stubdir.$$"; mkdir -p "$d"; echo "$d"; else f="$TMPDIR/stubtmp.$$"; : > "$f"; echo "$f"; fi\n'
add(T("sh-fix-tempfile", "fix", "shell", "medium", """
`report.sh FILE` prints the 3 most frequent lines of FILE as `<count> <line>` (most frequent first, e.g. via `sort | uniq -c | sort -rn | head -3`). It stages the result in a predictable world-writable path (`/tmp/report.txt`) and never cleans up,
so two runs collide and leave junk behind (also a symlink-attack vector). Fix it: create the temp file with `mktemp` (honouring TMPDIR), remove it on EVERY exit path (normal exit, error, signals) using `trap ... EXIT`, use strict mode,
and exit 2 when not exactly one argument is given. A missing input file must produce a non-zero exit (and leave no temp file). Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $0 FILE" >&2; exit 2; }

tmp=$(mktemp)
trap 'rm -rf "$tmp"' EXIT

sort -- "$1" | uniq -c | sort -rn > "$tmp"
head -n 3 "$tmp"
""")},
 [SC(S, bug=True), K("uses mktemp", S, r"\bmktemp\b", bug=True), K("cleans up via trap", S, r"\btrap\b.*\bEXIT\b", bug=True), C("not_contains", "no hardcoded /tmp/report path", file=S, regex=r"/tmp/report", bug=True),
  B(S, [dict(name="top3", args=["data.txt"], files={"data.txt": DATA}, stubs={"mktemp": MKTEMP}, stdout_re=[r"^\s*4 fig$", r"^\s*3 apple$", r"^\s*2 pear$"], stdout_not=["kiwi"], no_leftover_re=r"stub", calls_re=["^mktemp"]),
        dict(name="missing input leaves no temp", args=["missing.txt"], stubs={"mktemp": MKTEMP}, rc="nonzero", no_leftover_re=r"stub"),
        dict(name="usage", args=[], stubs={"mktemp": MKTEMP}, rc=2)])],
 start={S: d(r"""
#!/bin/bash
sort $1 | uniq -c | sort -rn > /tmp/report.txt
head -3 /tmp/report.txt
""")}))

S = "check_build.sh"
MAKE = 'echo compiling\nexit "${MAKE_RC:-0}"\n'
add(T("sh-fix-pipeline-status", "fix", "shell", "hard", """
`check_build.sh` runs `make all`, logging to `build/build.log` via `tee`, then prints `build finished`. CI keeps going green when the build is broken: the pipeline hides make's failure behind tee, and a missing `build` directory is ignored.
Fix it: if `make all` fails the script must exit non-zero (with make's failure code) and NOT print `build finished`, the log must still be written, and a missing `build` directory must be an error (exit 1, make not called).
Keep the behaviour otherwise (make runs inside `build/`, output is shown AND logged). Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

cd build || { echo "no build directory" >&2; exit 1; }
make all 2>&1 | tee build.log
echo "build finished"
""")},
 [SC(S, bug=True), C("contains", "pipefail enabled (or PIPESTATUS checked)", file=S, regex=r"pipefail|PIPESTATUS", bug=True),
  B(S, [dict(name="success", args=[], files={"build/keep": ""}, stubs={"make": MAKE}, stdout_re=[r"^compiling$", r"^build finished$"], out_files_re={"build/build.log": r"compiling"}, calls_re=["^make all$"]),
        dict(name="make fails", args=[], files={"build/keep": ""}, env={"MAKE_RC": "2"}, stubs={"make": MAKE}, rc="nonzero", stdout_not=["build finished"], out_files_re={"build/build.log": r"compiling"}),
        dict(name="no build dir", args=[], stubs={"make": MAKE}, rc="nonzero", stdout_not=["build finished"], calls_not=["^make"])], bug=True)],
 start={S: d(r"""
#!/bin/bash
cd build
make all 2>&1 | tee build.log
echo "build finished"
""")}))

S = "portable.sh"
add(T("sh-fix-bashisms", "fix", "shell", "hard", """
This script uses `#!/bin/sh` but is full of bashisms (arrays, `[[ ]]`, `==`, the `function` keyword). On Debian/Alpine `/bin/sh` is dash/busybox and it crashes. Make it POSIX sh clean (do NOT switch the shebang to bash).
Behaviour: with one argument `all` print `process a`, `process b`, `process c` (one per line) then `done`; with any other single argument X print `process X` then `done`; with no argument print a usage line to stderr and exit 2. Must pass `shellcheck -s sh`.""",
 {S: d(r"""
#!/bin/sh
set -eu

if [ $# -ne 1 ]; then
  echo "usage: $0 all|NAME" >&2
  exit 2
fi

done_msg() {
  echo "done"
}

if [ "$1" = "all" ]; then
  for f in a b c; do
    echo "process $f"
  done
else
  echo "process $1"
fi
done_msg
""")},
 [SC(S, bug=True, shell="sh"), K("shebang stays /bin/sh", S, r"\A#!\s*/(usr/)?bin/(env )?sh\b"), C("not_contains", "no bash-only syntax", file=S, regex=r"\[\[|\]\]|^\s*function\s|=\(|\$\{[A-Za-z_]+\[@\]\}", bug=True),
  B(S, [dict(name="all", args=["all"], stdout="process a\nprocess b\nprocess c\ndone"), dict(name="one", args=["web"], stdout="process web\ndone"),
        dict(name="no arg", args=[], rc=2, stderr_re=[r"usage"]), dict(name="spaces", args=["a b"], stdout="process a b\ndone")], bug=True)],
 start={S: d(r"""
#!/bin/sh
files=(a b c)
if [[ "$1" == "all" ]]; then
  for f in "${files[@]}"; do
    echo "process $f"
  done
else
  echo "process $1"
fi
function done_msg { echo "done"; }
done_msg
""")}))

S = "count_lines.sh"
add(T("sh-fix-word-splitting", "fix", "shell", "medium", """
`count_lines.sh DIR` prints, for every `*.txt` file directly in DIR (in glob/alphabetical order), `<basename>: <number of lines>`. The current implementation parses `ls`, breaks on names with spaces, prints full paths and misbehaves when there are no matching files
(it should print nothing and exit 0). Fix it properly (no `ls` parsing, quote everything, use `wc -l <` so the output has no padding). Exit 2 if DIR is missing/not a directory. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 1 ] && [ -d "$1" ] || { echo "usage: $0 DIR" >&2; exit 2; }

shopt -s nullglob
for f in "$1"/*.txt; do
  n=$(wc -l < "$f")
  echo "$(basename "$f"): $n"
done
""")},
 [SC(S, bug=True), C("not_contains", "parses ls output", file=S, regex=r"\$\(\s*ls\b|`ls\b", bug=True),
  B(S, [dict(name="spaces", args=["d"], files={"d/a b.txt": "1\n2\n", "d/c.txt": "1\n2\n3\n", "d/ignore.log": "x\n"}, stdout="a b.txt: 2\nc.txt: 3"),
        dict(name="empty dir", args=["e"], files={"e/x.log": "x\n"}, stdout=""), dict(name="not a dir", args=["nope"], rc=2), dict(name="usage", args=[], rc=2)], bug=True)],
 start={S: d(r"""
#!/bin/bash
DIR=$1
for f in $(ls $DIR/*.txt); do
  n=$(cat $f | wc -l)
  echo "$f: $n"
done
""")}))

S = "fetch_token.sh"
CURL2 = 'cat > .curl_stdin\nexit 0\n'
add(T("sh-fix-secret-leak", "fix", "shell", "hard", """
`fetch_token.sh` logs in to an API with HTTP basic auth but leaks the password everywhere: it takes it as a command-line argument (visible in `ps` and shell history), echoes it, and runs with `set -x` (traces credentials), and passes it in curl's argv.
Fix it: the password comes ONLY from the environment variable `API_PASS` (exit 2 with a message that does not contain the value if it is unset/empty); the user is `deploy`; no `set -x`, no echoing the secret; curl must receive the credentials via a config on stdin
(`curl -K -` / `--config -`, e.g. `printf 'user = "%s:%s"\\n' ... | curl -K - ...`), never in its argument list. Keep requesting `https://api.example.com/v1/token` and saving to `token.json`. Neither stdout, stderr nor curl's argv may contain the secret. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

if [ -z "${API_PASS:-}" ]; then
  echo "API_PASS is not set" >&2
  exit 2
fi
api_user=deploy

printf 'user = "%s:%s"\n' "$api_user" "$API_PASS" |
  curl --silent --show-error --fail -K - -o token.json https://api.example.com/v1/token
echo "token saved"
""")},
 [SC(S), C("not_contains", "set -x traces the secret", file=S, regex=r"set\s+-[a-z]*x|set\s+-o\s+xtrace", bug=True),
  B(S, [dict(name="ok", args=[], env={"API_PASS": "s3cr3t-Pa55"}, stubs={"curl": CURL2}, stdout_not=["s3cr3t-Pa55"], stderr_not=["s3cr3t-Pa55"], calls_not=["s3cr3t-Pa55"], out_files_re={".curl_stdin": r"user\s*=.*deploy:s3cr3t-Pa55"},
             calls_re=[r"^curl .*(-K|--config)[ =]-.*https://api\.example\.com/v1/token|^curl .*https://api\.example\.com/v1/token.*(-K|--config)[ =]-"], bug=True),
        dict(name="unset", args=[], stubs={"curl": CURL2}, rc=2, calls_count=0),
        dict(name="password as arg is not accepted nor leaked", args=["s3cr3t-Pa55"], stubs={"curl": CURL2}, rc=2, stdout_not=["s3cr3t-Pa55"], stderr_not=["s3cr3t-Pa55"], calls_count=0)], bug=True)],
 start={S: d(r"""
#!/bin/bash
set -x
API_USER=deploy
API_PASS=$1
echo "Logging in with password $API_PASS"
curl -u "$API_USER:$API_PASS" https://api.example.com/v1/token -o token.json
echo "token saved"
""")}))

# ---------------------------------------------------------------------------------------------- harden
S = "install.sh"
PAYLOAD = "#!/bin/sh\necho tool v1.0\n"
SHA = hashlib.sha256(PAYLOAD.encode()).hexdigest()
CURLDL = 'out=""\nwhile [ $# -gt 0 ]; do case "$1" in -o|--output) out=$2; shift;; esac; shift; done\n[ -n "$out" ] && cp payload.src "$out"\nexit 0\n'
add(T("sh-harden-installer", "harden", "shell", "hard", """
`install.sh URL SHA256 PREFIX` installs a CLI binary, but today it pipes a remote script into bash with root rights and trusts whatever it gets. Harden it: download the file with `curl --fail ... -o <temp file>` (temp file via `mktemp`, always removed),
verify the SHA-256 against the argument using `sha256sum -c` BEFORE installing (mismatch: print `checksum mismatch` to stderr, exit 1, install nothing), then install it as `PREFIX/bin/tool` with mode 0755 (create dirs as needed; use `install -D -m 0755`).
Wrong usage: exit 2. Strict mode on. The expected hash is a 64-hex string; reject anything else with exit 2. Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 3 ] || { echo "usage: $0 URL SHA256 PREFIX" >&2; exit 2; }
url=$1
sha=$2
prefix=$3
[[ $sha =~ ^[0-9a-fA-F]{64}$ ]] || { echo "SHA256 must be 64 hex characters" >&2; exit 2; }

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

curl --fail --silent --show-error --location -o "$tmp" "$url"
if ! echo "$sha  $tmp" | sha256sum -c --status -; then
  echo "checksum mismatch" >&2
  exit 1
fi
install -D -m 0755 "$tmp" "$prefix/bin/tool"
echo "installed $prefix/bin/tool"
""")},
 [SC(S, bug=True), C("not_contains", "curl | bash", file=S, regex=r"\|\s*(sudo\s+)?(ba)?sh\b", bug=True), K("verifies with sha256sum", S, r"sha256sum\s+-c", bug=True), K("uses mktemp", S, r"\bmktemp\b", bug=True),
  B(S, [dict(name="good download", args=["https://dl.example.com/tool", SHA, "pfx"], files={"payload.src": PAYLOAD}, stubs={"curl": CURLDL}, out_files={"pfx/bin/tool": PAYLOAD}, modes_after={"pfx/bin/tool": "755"}, calls_re=[r"^curl .*https://dl\.example\.com/tool"], no_leftover_re=r"^tmp\."),
        dict(name="tampered download", args=["https://dl.example.com/tool", "0" * 64, "pfx"], files={"payload.src": PAYLOAD}, stubs={"curl": CURLDL}, rc=1, stderr_re=[r"checksum mismatch"], no_files=["pfx/bin/tool"]),
        dict(name="bad hash format", args=["https://dl.example.com/tool", "abc", "pfx"], files={"payload.src": PAYLOAD}, stubs={"curl": CURLDL}, rc=2, calls_count=0, no_files=["pfx/bin/tool"]),
        dict(name="usage", args=["https://dl.example.com/tool"], stubs={"curl": CURLDL}, rc=2)], bug=True)],
 start={S: d(r"""
#!/bin/bash
URL=$1
curl -sL $URL | sudo bash
cp /tmp/tool $3/bin/tool
chmod 777 $3/bin/tool
""")}))

S = "run_job.sh"
add(T("sh-harden-injection", "harden", "shell", "hard", """
`run_job.sh NAME` runs `jobs/NAME.sh` for an operator-facing web hook, but NAME flows into `eval`, so `backup; touch pwned` executes arbitrary commands. Harden it: validate NAME against `^[a-z0-9_-]+$` (else print `invalid job name` to stderr and exit 2 WITHOUT running anything),
no `eval`/`bash -c` with interpolated input, run the job with `bash "jobs/$name.sh"` (no exec bit needed), and exit 1 with `unknown job: NAME` when `jobs/NAME.sh` does not exist. Exactly one argument required (else exit 2). Shellcheck-clean.""",
 {S: d(r"""
#!/usr/bin/env bash
set -euo pipefail

[ $# -eq 1 ] || { echo "usage: $0 NAME" >&2; exit 2; }
name=$1
if [[ ! $name =~ ^[a-z0-9_-]+$ ]]; then
  echo "invalid job name" >&2
  exit 2
fi
if [ ! -f "jobs/$name.sh" ]; then
  echo "unknown job: $name" >&2
  exit 1
fi
bash "jobs/$name.sh"
""")},
 [SC(S), C("not_contains", "eval / bash -c on user input", file=S, regex=r"\beval\b|bash\s+-c|sh\s+-c", bug=True),
  B(S, [dict(name="valid job", args=["backup"], files={"jobs/backup.sh": "echo backup ran\n"}, stdout="backup ran"),
        dict(name="injection attempt", args=["backup; touch pwned"], files={"jobs/backup.sh": "echo backup ran\n"}, rc=2, no_files=["pwned"], stderr_re=[r"invalid job name"], stdout_not=["backup ran"], bug=True),
        dict(name="command substitution", args=["$(touch pwned)"], files={"jobs/backup.sh": "echo x\n"}, rc=2, no_files=["pwned"]),
        dict(name="path traversal", args=["../evil"], files={"evil.sh": "touch pwned\n", "jobs/backup.sh": "echo x\n"}, rc=2, no_files=["pwned"]),
        dict(name="uppercase rejected", args=["Backup"], files={"jobs/backup.sh": "echo x\n"}, rc=2),
        dict(name="unknown job", args=["missing"], files={"jobs/backup.sh": "echo x\n"}, rc=1, stderr_re=[r"unknown job: missing"]),
        dict(name="usage", args=[], rc=2)], bug=True)],
 start={S: d(r"""
#!/bin/bash
eval "bash jobs/$1.sh"
""")}))
