"""Grader for the `data` specialist. Runs INSIDE the locked-down container (stdlib only).

Protocol: reads JSONL jobs on stdin: {"job_id", "task": <task record>, "answer": <model answer text>}
          writes JSONL results on stdout: {"job_id", "pass": bool, "detail": str}
Task data arrives via stdin (not a mounted file) so candidate code cannot read hidden tests from disk.
"""
import json
import math
import re
import signal
import sqlite3
import subprocess
import sys
import time

JOB_TIMEOUT = 25
QUERY_TIMEOUT = 6.0


class Fail(Exception):
    pass


# ---------------------------------------------------------------- answer extraction
def extract(answer, kind):
    """Return the code from the first fenced block if present, else the raw text."""
    m = re.search(r"```[A-Za-z0-9_+-]*[ \t]*\n(.*?)```", answer, re.S)
    return (m.group(1) if m else answer).strip()


def strip_comments(sql):
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


# ---------------------------------------------------------------- normalisation
def norm_val(v):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, float):
        if math.isnan(v):
            return "nan"
        r = round(v, 6)
        return int(r) if r == int(r) else r
    if isinstance(v, bytes):
        return v.hex()
    return v


def sort_key(row):
    return tuple((0, 0, "") if v is None else (1, 0, v) if isinstance(v, (int, float)) else (2, 0, str(v)) for v in row)


def norm_rows(rows, ordered):
    out = [[norm_val(v) for v in r] for r in rows]
    return out if ordered else sorted(out, key=sort_key)


def new_db(task, data):
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(task["schema_sql"])
    for table, rows in data.items():
        if rows:
            conn.executemany(f"INSERT INTO {table} VALUES ({','.join('?' * len(rows[0]))})", rows)
    return conn


def arm_timeout(conn):
    t0 = time.time()

    def handler():
        return 1 if time.time() - t0 > QUERY_TIMEOUT else 0
    conn.set_progress_handler(handler, 10000)


def readonly_authorizer(conn):
    ok = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}

    def auth(action, a, b, c, d):
        return sqlite3.SQLITE_OK if action in ok else sqlite3.SQLITE_DENY
    conn.set_authorizer(auth)


def run_select(conn, sql):
    body = strip_comments(sql).strip().rstrip(";").strip()
    if not re.match(r"(?is)^(select|with)\b", body):
        raise Fail("answer must be a single SELECT/WITH statement")
    readonly_authorizer(conn)
    arm_timeout(conn)
    try:
        cur = conn.execute(body)
        cols = [c[0].lower() for c in cur.description]
        return cols, cur.fetchall()
    except sqlite3.Error as e:
        raise Fail(f"SQL error: {e}")
    finally:
        conn.set_authorizer(None)


def compare_result(cols, rows, exp, ordered, check_names=True):
    if len(cols) != len(exp["columns"]):
        raise Fail(f"expected {len(exp['columns'])} columns {exp['columns']}, got {len(cols)} {cols}")
    if check_names and cols != [c.lower() for c in exp["columns"]]:
        raise Fail(f"column names {cols} != {exp['columns']}")
    got = norm_rows(rows, ordered)
    want = norm_rows(exp["rows"], ordered)
    if got != want:
        raise Fail(f"result mismatch: got {len(got)} rows, want {len(want)}; first got={got[:3]} want={want[:3]}")


# ---------------------------------------------------------------- kinds
def grade_sql(task, answer):
    sql = extract(answer, task["kind"])
    for ds in task["hidden"]["datasets"]:
        conn = new_db(task, ds["data"])
        try:
            cols, rows = run_select(conn, sql)
            compare_result(cols, rows, ds["expected"], task["check"]["ordered"], task["check"].get("check_names", True))
        except Fail as e:
            raise Fail(f"[dataset {ds['name']}] {e}")
        finally:
            conn.close()


def split_statements(script):
    out, cur = [], ""
    for line in script.splitlines(keepends=True):
        cur += line
        if sqlite3.complete_statement(cur):
            out.append(cur.strip())
            cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out


def norm_probe_rows(rows, ordered=False):
    return norm_rows(rows, ordered)


def grade_ddl(task, answer):
    script = extract(answer, "ddl")
    conn = sqlite3.connect(":memory:", isolation_level=None)
    try:
        conn.executescript(task["schema_sql"])
        conn.executescript(task["hidden"]["seed_sql"])
        arm_timeout(conn)
        try:
            conn.executescript(script)
        except sqlite3.Error as e:
            raise Fail(f"migration failed: {e}")
        if conn.in_transaction:
            conn.execute("COMMIT")
        conn.execute("PRAGMA foreign_keys=ON")
        bad = conn.execute("PRAGMA foreign_key_check").fetchall()
        if bad:
            raise Fail(f"foreign_key_check violations after migration: {bad[:3]}")
        for i, p in enumerate(task["hidden"]["probes"]):
            conn.execute("BEGIN")
            try:
                label = p.get("label", f"probe {i}")
                try:
                    for s in p.get("setup", []):
                        conn.execute(s)
                except sqlite3.Error as e:
                    raise Fail(f"{label}: setup failed: {e}")
                exp = p["expect"]
                if exp == "error":
                    want = {"integrity": sqlite3.IntegrityError, "operational": sqlite3.OperationalError}[p.get("err", "integrity")]
                    try:
                        conn.execute(p["sql"]).fetchall()
                    except want:
                        continue
                    except sqlite3.Error as e:
                        raise Fail(f"{label}: wrong error type {type(e).__name__}: {e}")
                    raise Fail(f"{label}: expected {p.get('err', 'integrity')} error but statement succeeded")
                try:
                    cur = conn.execute(p["sql"])
                    rows = cur.fetchall()
                except sqlite3.Error as e:
                    raise Fail(f"{label}: unexpected error {e}")
                if exp == "rows":
                    if norm_probe_rows(rows, p.get("ordered", False)) != norm_probe_rows(p["rows"], p.get("ordered", False)):
                        raise Fail(f"{label}: rows {norm_probe_rows(rows)[:4]} != {norm_probe_rows(p['rows'])[:4]}")
            finally:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
    finally:
        conn.close()


def grade_optimize(task, answer):
    script = extract(answer, "optimize")
    query = None
    idx = []
    for st in split_statements(script):
        body = strip_comments(st).strip().rstrip(";").strip()
        if not body:
            continue
        if re.match(r"(?is)^create\s+(unique\s+)?index\b", body):
            idx.append(body)
        elif re.match(r"(?is)^(select|with)\b", body):
            query = body
        else:
            raise Fail("only CREATE INDEX statements and one SELECT/WITH query are allowed")
    if query is None:
        query = task["query"]
    chk = task["check"]
    for ds in task["hidden"]["datasets"]:
        conn = new_db(task, ds["data"])
        try:
            for s in idx:
                try:
                    conn.execute(s)
                except sqlite3.Error as e:
                    raise Fail(f"[{ds['name']}] index failed: {e}")
            arm_timeout(conn)
            readonly_authorizer(conn)
            try:
                cur = conn.execute(query)
                cols = [c[0].lower() for c in cur.description]
                rows = cur.fetchall()
                plan = [r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + query).fetchall()]
            except sqlite3.Error as e:
                raise Fail(f"[{ds['name']}] SQL error: {e}")
            conn.set_authorizer(None)
            compare_result(cols, rows, ds["expected"], chk["ordered"])
            for pat in chk.get("search", []):
                if not any(re.search(pat, line) for line in plan):
                    raise Fail(f"plan lacks /{pat}/; plan={plan}")
            for pat in chk.get("forbid", []):
                if any(re.search(pat, line) for line in plan):
                    raise Fail(f"plan matches forbidden /{pat}/; plan={plan}")
        finally:
            conn.close()


RUNNER = r"""
import sys, json, os
p = json.load(sys.stdin)
real = sys.stdout
sys.stdout = open(os.devnull, 'w')
ns = {'__name__': 'candidate'}
try:
    exec(compile(p['code'], 'candidate.py', 'exec'), ns)
    f = ns['solve']
except BaseException as e:
    real.write(json.dumps({'fatal': repr(e)[:300]})); sys.exit(0)
res = []
for args in p['tests']:
    try:
        v = f(*args)
        res.append({'ok': json.loads(json.dumps(v))})
    except BaseException as e:
        res.append({'err': repr(e)[:200]})
real.write(json.dumps({'results': res}))
"""


def deep_eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or (type(a) == type(b) and a == b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)
    if type(a) != type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(deep_eq(a[k], b[k]) for k in a)
    return a == b


def grade_etl(task, answer):
    code = extract(answer, "etl")
    tests = task["hidden"]["tests"]
    try:
        p = subprocess.run([sys.executable, "-I", "-c", RUNNER], input=json.dumps({"code": code, "tests": [t["args"] for t in tests]}),
                           capture_output=True, text=True, timeout=12)
    except subprocess.TimeoutExpired:
        raise Fail("timeout running solve()")
    try:
        out = json.loads(p.stdout)
    except Exception:
        raise Fail(f"candidate crashed: {p.stderr[-200:]}")
    if "fatal" in out:
        raise Fail("could not load solve(): " + out["fatal"])
    for i, (t, r) in enumerate(zip(tests, out["results"])):
        if "err" in r:
            raise Fail(f"test {i}: raised {r['err']}")
        got, want = r["ok"], t["expected"]
        if task["check"].get("unordered") and isinstance(got, list):
            key = lambda x: json.dumps(x, sort_keys=True)
            got, want = sorted(got, key=key), sorted(want, key=key)
        if not deep_eq(got, want):
            raise Fail(f"test {i}: got {json.dumps(got)[:200]} want {json.dumps(want)[:200]}")


GRADERS = {"sql_write": grade_sql, "sql_fix": grade_sql, "ddl": grade_ddl, "etl": grade_etl, "optimize": grade_optimize}


def on_alarm(signum, frame):
    raise Fail("job timeout")


def main():
    signal.signal(signal.SIGALRM, on_alarm)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        job = json.loads(line)
        signal.alarm(JOB_TIMEOUT)
        try:
            GRADERS[job["task"]["kind"]](job["task"], job["answer"])
            res = {"job_id": job["job_id"], "pass": True, "detail": ""}
        except Fail as e:
            res = {"job_id": job["job_id"], "pass": False, "detail": str(e)[:600]}
        except Exception as e:  # grader bug or hostile input; never pass
            res = {"job_id": job["job_id"], "pass": False, "detail": f"internal {type(e).__name__}: {str(e)[:300]}"}
        finally:
            signal.alarm(0)
        print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
