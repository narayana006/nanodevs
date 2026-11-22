"""Builds tasks.jsonl (stdout). Run inside the sandbox container so expected outputs come from the same sqlite/python as grading:
   docker run --rm -i --network none --read-only --cap-drop ALL --user 65534:65534 -v $PWD:/b:ro python:3.12-slim python /b/build_tasks.py > tasks.jsonl
All data is deterministic (seeded from the task id)."""
import json
import random
import sys
import zlib

sys.dont_write_bytecode = True
sys.path.insert(0, "/b" if __import__("os").path.isdir("/b") else ".")
import grader as G
from domains import GENS, SCHEMAS
from defs_sql import W, F
from defs_ddl_opt import DDL, OPT
from defs_etl import ETL

SIZES = (6, 24, 60)
OPT_SIZES = (150, 400)
errors = []


def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return repr(v)


def sample_inserts(data, per=4):
    lines = []
    for t, rows in data.items():
        for r in rows[:per]:
            lines.append(f"INSERT INTO {t} VALUES ({', '.join(lit(v) for v in r)});")
    return "\n".join(lines)


def datasets(tid, domain, sizes):
    out = []
    for i, n in enumerate(sizes):
        rng = random.Random(zlib.crc32(f"{tid}/{i}".encode()))
        data = GENS[domain](rng, n)
        out.append({"name": f"d{i}_n{n}", "data": {t: [list(r) for r in rows] for t, rows in data.items()}})
    return out


def run_ref(task, sql, ds):
    conn = G.new_db(task, ds["data"])
    try:
        cols, rows = G.run_select(conn, sql)
        return {"columns": cols, "rows": [[G.norm_val(v) for v in r] for r in rows]}
    finally:
        conn.close()


def sql_task(kind, key, domain, diff, spec, ref, ordered, buggy=None, symptom=None):
    tid = f"data-{kind}-{key}"
    schema = SCHEMAS[domain]
    task = {"id": tid, "kind": kind, "difficulty": diff, "domain": domain, "schema_sql": schema}
    dss = datasets(tid, domain, SIZES)
    nonempty = 0
    for ds in dss:
        ds["expected"] = run_ref(task, ref, ds)
        nonempty += bool(ds["expected"]["rows"])
    if nonempty < 2:
        errors.append(f"{tid}: expected result non-empty on only {nonempty}/3 datasets")
    if kind == "sql_fix":
        differs = 0
        for ds in dss:
            try:
                r = run_ref(task, buggy, ds)
                if G.norm_rows(r["rows"], ordered) != G.norm_rows(ds["expected"]["rows"], ordered) or r["columns"] != ds["expected"]["columns"]:
                    differs += 1
            except G.Fail:
                differs += 1
        if differs == 0:
            errors.append(f"{tid}: buggy query indistinguishable from reference on all datasets")
    sample = GENS[domain](random.Random(zlib.crc32(tid.encode())), 5)
    note = "Rows must come back in exactly the order described." if ordered else "Row order does not matter."
    head = f"You are working with a SQLite database.\n\nSchema:\n```sql\n{schema}\n```\n\nSample rows (a few per table):\n```sql\n{sample_inserts(sample)}\n```\n\n"
    if kind == "sql_write":
        prompt = head + f"Task: {spec}\n\nWrite a single SQLite SELECT statement (CTEs and window functions are allowed; no other statements). Column names must match exactly. {note}\nAnswer with only the SQL in a ```sql block."
        start = "SELECT 1;"
    else:
        prompt = (head + f"Intended behaviour: {spec}\n\nThis query is supposed to do that but is wrong:\n```sql\n{buggy}\n```\nSymptom: {symptom}\n\n"
                  f"Return the corrected single SQLite SELECT statement with the same output column names. {note}\nAnswer with only the SQL in a ```sql block.")
        start = buggy
    task.update(
        files={},
        inputs={"spec": spec, "sample_sql": sample_inserts(sample), **({"buggy_query": buggy, "symptom": symptom} if kind == "sql_fix" else {})},
        hidden={"datasets": dss}, check={"type": "result_set", "ordered": ordered, "check_names": True},
        reference=ref, start_state=start, prompt=prompt, meta={"answer_format": "sql", "n_datasets": len(dss)})
    return task


def ddl_task(key, diff, spec, schema, seed, probes, ref):
    tid = f"data-ddl-{key}"
    seed_txt = f"\n\nCurrent data:\n```sql\n{seed}\n```" if seed.strip() else ""
    prompt = (f"You maintain a SQLite database. Current schema:\n```sql\n{schema}\n```{seed_txt}\n\nTask: {spec}\n\n"
              "Write a migration script (one or more SQLite statements, may include comments) that upgrades this database in place. "
              "Existing data must be preserved unless the task says otherwise. Foreign keys will be switched on (PRAGMA foreign_keys=ON) when the result is tested, "
              "and the migration runs with them off. Do not recreate the original tables from scratch unless a table rebuild is required.\n"
              "Answer with only the SQL in a ```sql block.")
    return {"id": tid, "kind": "ddl", "difficulty": diff, "domain": "migration", "schema_sql": schema, "files": {},
            "inputs": {"spec": spec, "seed_sql": seed}, "hidden": {"seed_sql": seed, "probes": probes},
            "check": {"type": "probes", "n_probes": len(probes)}, "reference": ref, "start_state": "-- no-op", "prompt": prompt,
            "meta": {"answer_format": "sql"}}


def etl_task(key, diff, spec, ref, cases_fn):
    tid = f"data-etl-{key}"
    rng = random.Random(zlib.crc32(tid.encode()))
    cases = cases_fn(rng)
    ns = {}
    exec(compile(ref, "ref.py", "exec"), ns)
    tests = []
    for args in cases:
        exp = json.loads(json.dumps(ns["solve"](*args)))
        tests.append({"args": args, "expected": exp})
    files = {f"example_arg{i}.txt": a for i, a in enumerate(cases[0])}
    ex = tests[0]
    argshow = "\n".join(f"argument {i}:\n```\n{a}\n```" for i, a in enumerate(cases[0]))
    prompt = (f"Write a Python 3 function for a data-cleaning step. Use only the standard library.\n\n{spec}\n\n"
              f"Worked example.\n{argshow}\nreturns:\n```json\n{json.dumps(ex['expected'], indent=1)[:1500]}\n```\n\n"
              "The function must be named `solve`, must not read files or the network, and must return JSON-serialisable values (dict, list, str, int, float, bool, None). "
              "Answer with only the code in a ```python block.")
    nparams = len(cases[0])
    stub = f"def solve({', '.join('arg%d' % i for i in range(nparams))}):\n    return None\n"
    return {"id": tid, "kind": "etl", "difficulty": diff, "domain": "etl", "schema_sql": "", "files": files,
            "inputs": {"spec": spec, "example": {"args": cases[0], "expected": ex["expected"]}},
            "hidden": {"tests": tests}, "check": {"type": "function_tests", "unordered": False}, "reference": ref, "start_state": stub,
            "prompt": prompt, "meta": {"answer_format": "python", "n_tests": len(tests)}}


def opt_task(key, domain, diff, spec, query, ordered, search, forbid):
    tid = f"data-optimize-{key}"
    schema = SCHEMAS[domain]
    task = {"id": tid, "kind": "optimize", "difficulty": diff, "domain": domain, "schema_sql": schema}
    dss = datasets(tid, domain, OPT_SIZES)
    for ds in dss:
        ds["expected"] = run_ref(task, query, ds)
        if not ds["expected"]["rows"]:
            errors.append(f"{tid}: empty expected on {ds['name']}")
    conn = G.new_db(task, dss[-1]["data"])
    plan = [r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + query).fetchall()]
    conn.close()
    prompt = (f"A SQLite query is too slow.\n\nSchema (no indexes besides primary keys):\n```sql\n{schema}\n```\n\nSlow query:\n```sql\n{query}\n```\n\n"
              f"Observation: {spec}\n\nCurrent EXPLAIN QUERY PLAN output:\n```\n" + "\n".join(plan) + "\n```\n\n"
              "First explain in 1-3 SQL comment lines (`-- ...`) why it is slow. Then give the fix as: CREATE INDEX statements, optionally followed by ONE rewritten SELECT "
              "that returns exactly the same rows and column names as the original (if you give no SELECT, the original query is used). No other statements are allowed. "
              "The fix is graded by running EXPLAIN QUERY PLAN on the final query after your indexes exist: it must use an index search as required and the results must not change.\n"
              "Answer with only the SQL in a ```sql block.")
    return dict(task, files={}, inputs={"spec": spec, "query": query, "start_plan": plan}, hidden={"datasets": dss},
                check={"type": "plan", "ordered": ordered, "search": search, "forbid": forbid}, query=query,
                reference=None, start_state=query, prompt=prompt, meta={"answer_format": "sql", "n_datasets": len(dss)})


OPT_REF = {  # reference fixes (indexes + optional rewritten query)
 "orders_by_customer": "CREATE INDEX i1 ON orders(customer_id);",
 "orders_in_month": "CREATE INDEX i1 ON orders(order_date);",
 "orders_substr_month": "CREATE INDEX i1 ON orders(order_date);\nSELECT id, customer_id FROM orders WHERE order_date >= '2024-06-01' AND order_date < '2024-07-01';",
 "orders_status_date_sort": "CREATE INDEX i1 ON orders(status, order_date);",
 "items_units_by_product": "CREATE INDEX i1 ON order_items(product_id, qty);",
 "events_latest": "CREATE INDEX i1 ON events(ts);",
 "events_lower_kind": "CREATE INDEX i1 ON events(kind);\nSELECT id, user_id FROM events WHERE kind = 'purchase';",
 "users_with_purchases": "CREATE INDEX i1 ON events(user_id, kind);",
 "customers_like_prefix": "CREATE INDEX i1 ON customers(name COLLATE NOCASE);",
 "orders_group_by_customer": "CREATE INDEX i1 ON orders(customer_id);",
 "readings_by_day": "CREATE INDEX i1 ON readings(ts, sensor_id);",
 "open_loans_member": "CREATE INDEX i1 ON loans(member_id, returned_on);",
 "books_of_country": "CREATE INDEX i1 ON books(author_id);\nCREATE INDEX i2 ON authors(country);",
 "customers_without_orders": "CREATE INDEX i1 ON orders(customer_id);",
 "high_earners_monthly": "CREATE INDEX i1 ON employees(salary);\nSELECT id, name, salary FROM employees WHERE salary >= 96012;",
}


def main():
    out = []
    for key, dom, diff, spec, ref, ordered in W:
        out.append(sql_task("sql_write", key, dom, diff, spec, ref, ordered))
    for key, dom, diff, spec, buggy, fixed, ordered, symptom in F:
        out.append(sql_task("sql_fix", key, dom, diff, spec, fixed, ordered, buggy, symptom))
    for d in DDL:
        out.append(ddl_task(*d))
    for e in ETL:
        out.append(etl_task(*e))
    for o in OPT:
        t = opt_task(*o)
        t["reference"] = OPT_REF[o[0]]
        out.append(t)
    ids = [t["id"] for t in out]
    assert len(ids) == len(set(ids)), "duplicate ids"
    for t in out:
        print(json.dumps(t, separators=(",", ":"), ensure_ascii=False))
    if errors:
        print("BUILD WARNINGS:\n" + "\n".join(errors), file=sys.stderr)
        sys.exit(1)
    print(f"built {len(out)} tasks", file=sys.stderr)


main()
