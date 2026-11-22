"""ETL task definitions: plain-Python transforms. Each: (key, difficulty, spec, reference_code, cases(rng) -> list of arg lists).
The first case is shown to the model as the worked example; all cases are hidden tests."""
import json
import string


def words(rng, k):
    return " ".join("".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(2, 6))) for _ in range(k))


def rcsv(rng, header, n, gen):
    return "\n".join([header] + [gen(rng, i) for i in range(n)]) + "\n"


ETL = []


def add(key, diff, spec, ref, cases):
    ETL.append((key, diff, spec, ref, cases))


add("csv_total", "easy",
    "`solve(raw)` receives CSV text with header `name,qty,price`. Return the total value sum(qty * price) as a float rounded to 2 decimals. Skip any row where qty or price is blank (after stripping).",
    '''import csv, io
def solve(raw):
    total = 0.0
    for r in csv.DictReader(io.StringIO(raw)):
        q = (r.get("qty") or "").strip()
        p = (r.get("price") or "").strip()
        if not q or not p:
            continue
        total += int(q) * float(p)
    return round(total, 2)
''',
    lambda rng: [["name,qty,price\nbolt,3,1.50\nnut,,2\nscrew,10,0.25\n"], ["name,qty,price\n"], ["name,qty,price\na, 2 , 3.10 \nb,1,\n"],
                 [rcsv(rng, "name,qty,price", 12, lambda r, i: f"item{i},{r.choice(['', '1', '4', '7'])},{r.choice(['', '0.99', '12.5', '3'])}")],
                 [rcsv(rng, "name,qty,price", 30, lambda r, i: f"item{i},{r.randint(1, 9)},{r.randint(1, 5000) / 100:.2f}")]])

add("dedupe_emails", "easy",
    "`solve(text)` receives text with one email per line. Strip each line and lower-case it. Keep only valid addresses: exactly one '@', a non-empty local part and a domain that contains a '.' and has no empty label (no leading, trailing or double dots), and no whitespace inside. Return the list of unique valid addresses in order of first appearance.",
    '''def solve(text):
    out, seen = [], set()
    for line in text.splitlines():
        s = line.strip().lower()
        if s.count("@") != 1 or any(c.isspace() for c in s):
            continue
        local, domain = s.split("@")
        if not local or "." not in domain or any(not p for p in domain.split(".")):
            continue
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out
''',
    lambda rng: [["Ann@Example.com\n ann@example.com \nbob@@x.com\nbad@nodot\ncy@mail.org\n\n"], [""], ["a@b.c\nA@B.C\n@x.com\nx@.com\nx@y..com\nu v@x.com\n"],
                 ["\n".join(rng.choice(["a@x.com", "B@x.com", "b@X.com", " c@y.org ", "bad", "d@e.f"]) for _ in range(20))],
                 ["\n".join(f"{words(rng, 1)}@{rng.choice(['x', 'y', 'z'])}.com" for _ in range(25))]])

add("parse_kv", "easy",
    "`solve(text)` parses a config file. Each non-blank line not starting with '#' (after stripping) of the form `key = value` splits on the FIRST '='; strip key and value; if the value is wrapped in a matching pair of single or double quotes remove exactly that pair. Lines without '=' are ignored. Later duplicates override earlier ones. Return a dict of str to str.",
    '''def solve(text):
    out = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\\"'":
            v = v[1:-1]
        out[k] = v
    return out
''',
    lambda rng: [["# db\nhost = localhost\nport=5432\nname = \"my db\"\nbad line\n"], [""], ["a=1\na=2\n  # c=3\nb = 'x=y'\nc==d\nd = \"unclosed\n"],
                 ["\n".join("%s = %s" % (rng.choice(['k1', 'k2', 'k3', 'k4']), rng.choice(['v', '"q q"', "'s'", '1=2', ''])) for _ in range(12))],
                 ["key =  \" spaced \" \n=novalue\n  x  =  y  \n"]])

add("phones", "medium",
    "`solve(raw)` receives a JSON list of strings. For each string keep only its digits; if that leaves 11 digits starting with '1', drop the leading 1. If exactly 10 digits remain, output them as '(AAA) BBB-CCCC', otherwise None. Return the list of results (same length and order).",
    '''import json
def solve(raw):
    out = []
    for s in json.loads(raw):
        d = "".join(c for c in s if c.isdigit())
        if len(d) == 11 and d[0] == "1":
            d = d[1:]
        out.append(f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d) == 10 else None)
    return out
''',
    lambda rng: [['["415-555-0134", "1 (415) 555 0134", "555-0134", "+1.415.555.0134 ext 9", ""]'], ["[]"], ['["0123456789", "11234567890", "21234567890", "12345"]'],
                 [json.dumps([rng.choice(["212-555-0100", "(646) 555 0199", "1-800-555-0123", "999", "abc", "+44 20 7946 0958", "5551234567"]) for _ in range(15)])],
                 [json.dumps(["".join(rng.choice("0123456789 -().") for _ in range(rng.randint(5, 16))) for _ in range(20)])]])

add("dept_avg", "medium",
    "`solve(raw)` receives CSV text with header `dept,salary`. Strip both fields. Ignore rows whose salary is blank or not a valid number. Return a dict mapping each department that has at least one valid row to the average salary rounded to 2 decimals (float).",
    '''import csv, io
def solve(raw):
    sums = {}
    for r in csv.DictReader(io.StringIO(raw)):
        d = (r.get("dept") or "").strip()
        try:
            s = float((r.get("salary") or "").strip())
        except ValueError:
            continue
        a = sums.setdefault(d, [0.0, 0])
        a[0] += s
        a[1] += 1
    return {d: round(t / n, 2) for d, (t, n) in sums.items()}
''',
    lambda rng: [["dept,salary\neng,100\neng,200\nops,50.5\nops,n/a\nhr,\n"], ["dept,salary\n"], ["dept,salary\n eng , 10 \nENG,20\n,5\n"],
                 [rcsv(rng, "dept,salary", 25, lambda r, i: f"{r.choice(['a', 'b', 'c'])},{r.choice(['', 'x', str(r.randint(30, 99) * 1000), '1e3'])}")],
                 [rcsv(rng, "dept,salary", 40, lambda r, i: f"d{r.randint(1, 6)},{r.randint(1000, 99999) / 10}")]])

add("mixed_dates", "medium",
    "`solve(raw)` receives a JSON list of date strings in any of these formats (after stripping): `YYYY-MM-DD`, `MM/DD/YYYY`, `D Mon YYYY` (e.g. `5 Mar 2024`), `Mon D, YYYY` (e.g. `Mar 5, 2024`; month names are 3-letter English abbreviations). Return a list of ISO `YYYY-MM-DD` strings; anything unparseable or an impossible calendar date (like 02/30/2024) becomes None.",
    '''import json
from datetime import datetime
FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d %b %Y", "%b %d, %Y"]
def solve(raw):
    out = []
    for s in json.loads(raw):
        res = None
        for f in FORMATS:
            try:
                res = datetime.strptime(s.strip(), f).strftime("%Y-%m-%d")
                break
            except ValueError:
                pass
        out.append(res)
    return out
''',
    lambda rng: [['["2024-03-05", "03/05/2024", "5 Mar 2024", "Mar 5, 2024", "  2024-12-31 ", "garbage", "02/30/2024"]'], ["[]"], ['["2023-02-29", "29 Feb 2024", "Feb 29, 2023", "13/01/2024", "2024/01/05"]'],
                 [json.dumps([rng.choice(["2024-%02d-%02d" % (rng.randint(1, 12), rng.randint(1, 31)), "%02d/%02d/2023" % (rng.randint(1, 12), rng.randint(1, 31)),
                                         "%d %s 2022" % (rng.randint(1, 31), rng.choice(["Jan", "Feb", "Apr", "Sep"])), "%s %d, 2021" % (rng.choice(["Mar", "Jun", "Dec"]), rng.randint(1, 31)), "n/a"]) for _ in range(25)])]])

add("flatten_json", "medium",
    "`solve(raw)` receives a JSON object (as text). Return a flat dict where nested object keys are joined with '.' and list items use their index as a key part (e.g. {'a': {'b': [10, {'c': 1}]}} -> {'a.b.0': 10, 'a.b.1.c': 1}). Empty dicts and empty lists are kept as leaf values ({} / []). null stays None.",
    '''import json
def solve(raw):
    out = {}
    def walk(v, path):
        if isinstance(v, dict) and v:
            for k, x in v.items():
                walk(x, f"{path}.{k}" if path else k)
        elif isinstance(v, list) and v:
            for i, x in enumerate(v):
                walk(x, f"{path}.{i}" if path else str(i))
        else:
            out[path] = v
    walk(json.loads(raw), "")
    return out
''',
    lambda rng: [['{"a": {"b": [10, {"c": 1}]}, "d": null, "e": {}}'], ['{"x": 1}'], ['{"x": [[1, 2], [3]], "y": {"z": {"w": []}}, "k.j": 1}'],
                 [json.dumps({"u%d" % i: rng.choice([1, "s", None, [1, {"q": 2}], {"r": {"s": [True, 2.5]}}, [], {}]) for i in range(8)})]])

add("latest_per_id", "medium",
    "`solve(raw)` receives CSV text with header `id,name,updated_at` (updated_at is ISO text, compare as strings). For each id keep the row with the greatest updated_at; if two rows tie, keep the one that appears later in the file. Return a list of dicts {'id': int, 'name': str, 'updated_at': str} sorted by id ascending.",
    '''import csv, io
def solve(raw):
    best = {}
    for r in csv.DictReader(io.StringIO(raw)):
        i = int(r["id"])
        if i not in best or r["updated_at"] >= best[i]["updated_at"]:
            best[i] = {"id": i, "name": r["name"], "updated_at": r["updated_at"]}
    return [best[i] for i in sorted(best)]
''',
    lambda rng: [["id,name,updated_at\n1,ann,2024-01-01\n2,bob,2024-02-01\n1,anna,2024-03-01\n2,bobby,2024-01-15\n"], ["id,name,updated_at\n"], ["id,name,updated_at\n5,a,2024-01-01\n5,b,2024-01-01\n10,c,2023-01-01\n"],
                 [rcsv(rng, "id,name,updated_at", 30, lambda r, i: f"{r.randint(1, 8)},n{i},2024-0{r.randint(1, 4)}-0{r.randint(1, 3)}")]])

add("money_cents", "medium",
    "`solve(raw)` receives a JSON list of strings. Parse each money string into an integer number of cents or None. After stripping: an optional leading '-' OR the whole value wrapped in parentheses means negative (not both); an optional '$' (after the '-' / inside the parentheses); the amount uses either plain digits or proper thousands grouping ('1,234' - groups of exactly 3 after the first group of 1-3 digits); at most 2 decimals (so '5.5' is 550 cents, '5.555' is invalid). Anything else, including the empty string, is None.",
    '''import json, re
RX = re.compile(r"^(?:(\\()|(-))?\\$?(\\d{1,3}(?:,\\d{3})+|\\d+)(?:\\.(\\d{1,2}))?(\\))?$")
def solve(raw):
    out = []
    for s in json.loads(raw):
        m = RX.match(s.strip())
        if not m or bool(m.group(1)) != bool(m.group(5)):
            out.append(None)
            continue
        cents = int(m.group(3).replace(",", "")) * 100 + int((m.group(4) or "0").ljust(2, "0"))
        out.append(-cents if (m.group(1) or m.group(2)) else cents)
    return out
''',
    lambda rng: [['["$1,234.50", "(12.5)", "-$3", "1234", "1,23.00", "abc", "", "$.50", "-(5)", "5.555"]'], ["[]"], ['["0", "$0.05", "  7.1 ", "(1,000)", "1,000,000.99", "12,34", "(5", "$-5"]'],
                 [json.dumps([rng.choice(["$%d.%02d" % (rng.randint(0, 999), rng.randint(0, 99)), "(%d)" % rng.randint(1, 50), "-%d.5" % rng.randint(1, 9), "%d,%03d" % (rng.randint(1, 99), rng.randint(0, 999)), "x%d" % rng.randint(1, 9)]) for _ in range(25)])]])

add("csv_records", "medium",
    "`solve(raw)` receives CSV text (fields may be quoted, quoted fields can contain commas, newlines and doubled quotes). Normalise header names: strip, lower-case, replace every run of non-alphanumeric characters with a single '_', strip leading/trailing '_'. Return a list of dicts keyed by those names, with values stripped; rows shorter than the header get '' for missing fields, extra fields beyond the header are dropped; rows where every value is empty are skipped.",
    '''import csv, io, re
def solve(raw):
    rows = list(csv.reader(io.StringIO(raw, newline="")))
    if not rows:
        return []
    keys = [re.sub(r"[^a-z0-9]+", "_", h.strip().lower()).strip("_") for h in rows[0]]
    out = []
    for r in rows[1:]:
        vals = [(r[i].strip() if i < len(r) else "") for i in range(len(keys))]
        if any(vals):
            out.append(dict(zip(keys, vals)))
    return out
''',
    lambda rng: [['First Name,Last-Name,Notes\nAda,Lovelace,"likes, commas"\n,,\nGrace,Hopper,"two\nlines"\n'], [""], ['ID , E-mail Address\n1\n2,"a ""q"" b",extra\n  ,  \n'],
                 [rcsv(rng, "Item #,Price ($),Tag", 10, lambda r, i: "%d,%s,%s" % (i, r.choice(['', '3.5']), r.choice(['"a,b"', 'x', ' y ', ''])))]])

add("customer_totals", "hard",
    "`solve(customers_csv, orders_csv)` receives two CSV texts: customers with header `id,name`, orders with header `order_id,customer_id,amount`. Ignore order rows whose amount is blank or not a number, and rows whose customer_id is not a known customer. Return a list of dicts {'id': int, 'name': str, 'orders': int, 'total': float (rounded to 2 decimals)} for EVERY customer (zeros if none), sorted by id.",
    '''import csv, io
def solve(customers_csv, orders_csv):
    cust = {}
    for r in csv.DictReader(io.StringIO(customers_csv)):
        cust[int(r["id"])] = {"id": int(r["id"]), "name": r["name"].strip(), "orders": 0, "total": 0.0}
    for r in csv.DictReader(io.StringIO(orders_csv)):
        try:
            amt = float(r["amount"].strip())
            cid = int(r["customer_id"])
        except ValueError:
            continue
        if cid in cust:
            cust[cid]["orders"] += 1
            cust[cid]["total"] += amt
    return [dict(c, total=round(c["total"], 2)) for _, c in sorted(cust.items())]
''',
    lambda rng: [["id,name\n1,Ann\n2,Bob\n3,Cy\n", "order_id,customer_id,amount\n1,1,10.5\n2,1,4.5\n3,2,7\n4,9,100\n5,2,\n"], ["id,name\n", "order_id,customer_id,amount\n"],
                 ["id,name\n2,Bo\n1,Al\n", "order_id,customer_id,amount\n1,2,x\n2,2,1.005\n3,1,2\n"],
                 ["id,name\n" + "\n".join(f"{i},c{i}" for i in range(1, 8)) + "\n", rcsv(rng, "order_id,customer_id,amount", 25, lambda r, i: f"{i},{r.randint(1, 9)},{r.choice(['', 'n', str(r.randint(1, 900) / 10)])}")]])

add("ndjson", "medium",
    "`solve(text)` receives newline-delimited JSON. Skip blank lines. A line is VALID if it parses as a JSON object that has an 'id' key; every other non-blank line (bad JSON, non-object, missing id) counts as an error. Return {'records': [valid objects in order], 'errors': error_count}.",
    '''import json
def solve(text):
    recs, errs = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            o = json.loads(line)
        except ValueError:
            errs += 1
            continue
        if isinstance(o, dict) and "id" in o:
            recs.append(o)
        else:
            errs += 1
    return {"records": recs, "errors": errs}
''',
    lambda rng: [['{"id": 1, "v": "a"}\n\n{"id": 2}\nnot json\n[1,2]\n{"v": 3}\n'], [""], ['{"id": null}\n{"id": 1,}\n  {"id": 2, "n": {"x": [1]}}  \n"str"\n'],
                 ["\n".join(rng.choice(['{"id": %d}' % rng.randint(1, 99), '{"x": 1}', "oops", "", "[]", '{"id": 5, "t": "é"}']) for _ in range(20))]])

add("top_words", "medium",
    "`solve(text)` returns the 3 most frequent words as a list of [word, count] pairs. Words are matched with the pattern `[a-z]+(?:'[a-z]+)*` on the lower-cased text. Sort by count descending then word ascending. Fewer than 3 distinct words -> return them all.",
    '''import re
from collections import Counter
def solve(text):
    c = Counter(re.findall(r"[a-z]+(?:'[a-z]+)*", text.lower()))
    return [[w, n] for w, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:3]]
''',
    lambda rng: [["The cat and the hat. The CAT's hat, and... the end!"], [""], ["b a B A c"], ["don't Don't stop--stop 'quoted' 'quoted' x1y"],
                 [" ".join(rng.choice(["alpha", "Beta", "gamma", "delta", "it's", "eps"]) for _ in range(60))]])

add("sessions", "hard",
    "`solve(text)` receives log lines `ISO_TIMESTAMP user action` separated by single spaces (timestamps like 2024-03-05T10:00:00, no timezone), in arbitrary order. Ignore lines that do not have exactly 3 whitespace-separated fields or whose timestamp is invalid. For each user, sort their events by timestamp; a new session starts at the first event and whenever the gap to the previous event is strictly more than 30 minutes. Return a dict user -> number of sessions.",
    '''from datetime import datetime
def solve(text):
    ev = {}
    for line in text.splitlines():
        p = line.split()
        if len(p) != 3:
            continue
        try:
            t = datetime.fromisoformat(p[0])
        except ValueError:
            continue
        ev.setdefault(p[1], []).append(t)
    out = {}
    for u, ts in ev.items():
        ts.sort()
        n = 1
        for a, b in zip(ts, ts[1:]):
            if (b - a).total_seconds() > 1800:
                n += 1
        out[u] = n
    return out
''',
    lambda rng: [["2024-03-05T10:00:00 ann click\n2024-03-05T10:20:00 ann view\n2024-03-05T11:00:01 ann view\n2024-03-05T09:00:00 bob login\n"], [""],
                 ["2024-03-05T10:30:00 a x\n2024-03-05T10:00:00 a x\nbad line\n2024-13-05T10:00:00 a x\n2024-03-05T10:00:00 b y z\n2024-03-05T11:00:00 a x\n"],
                 ["\n".join("2024-03-0%dT%02d:%02d:00 %s a" % (rng.randint(1, 2), rng.randint(0, 23), rng.choice([0, 15, 45]), rng.choice(["u1", "u2", "u3"])) for _ in range(30))]])

add("pivot_wide", "medium",
    "`solve(raw)` receives CSV text with header `id,key,value` (long format). Return a list of dicts, one per distinct id (ids are strings, sorted ascending as strings), each with 'id' plus every key that appears anywhere in the file (value None if that id lacks it). If an (id, key) pair repeats, the last value wins.",
    '''import csv, io
def solve(raw):
    data, keys = {}, []
    for r in csv.DictReader(io.StringIO(raw)):
        if r["key"] not in keys:
            keys.append(r["key"])
        data.setdefault(r["id"], {})[r["key"]] = r["value"]
    return [dict({"id": i}, **{k: data[i].get(k) for k in keys}) for i in sorted(data)]
''',
    lambda rng: [["id,key,value\n1,color,red\n1,size,L\n2,color,blue\n2,color,green\n3,weight,5\n"], ["id,key,value\n"], ["id,key,value\nb,x,1\na,y,2\nb,y,3\n"],
                 [rcsv(rng, "id,key,value", 25, lambda r, i: f"{r.randint(1, 6)},{r.choice(['a', 'b', 'c', 'd'])},{r.randint(0, 99)}")]])

add("validate_records", "hard",
    "`solve(raw)` receives a JSON list of record objects. Validate each record IN THIS ORDER and report the first failing rule: (1) 'id' must be an int >= 1 (not a bool) or a string of digits that converts to an int >= 1 -> else 'bad_id'; (2) 'name' must be a string that is non-empty after stripping -> else 'bad_name'; (3) 'age' is optional (missing or null -> None); otherwise an int (not bool) or digit string, 0..120 -> else 'bad_age'; (4) 'email' must be a string that, lower-cased and stripped, has exactly one '@' with a non-empty local part and a domain containing '.' -> else 'bad_email'. Return {'valid': [{'id': int, 'name': stripped str, 'age': int or None, 'email': normalised str}], 'invalid': [[index, reason], ...]} preserving input order.",
    '''import json
def _int(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None
def solve(raw):
    valid, invalid = [], []
    for i, r in enumerate(json.loads(raw)):
        rid = _int(r.get("id"))
        if rid is None or rid < 1:
            invalid.append([i, "bad_id"]); continue
        name = r.get("name")
        if not isinstance(name, str) or not name.strip():
            invalid.append([i, "bad_name"]); continue
        age = None
        if r.get("age") is not None:
            age = _int(r["age"])
            if age is None or not 0 <= age <= 120:
                invalid.append([i, "bad_age"]); continue
        em = r.get("email")
        if not isinstance(em, str):
            invalid.append([i, "bad_email"]); continue
        em = em.strip().lower()
        if em.count("@") != 1 or not em.split("@")[0] or "." not in em.split("@")[1]:
            invalid.append([i, "bad_email"]); continue
        valid.append({"id": rid, "name": name.strip(), "age": age, "email": em})
    return {"valid": valid, "invalid": invalid}
''',
    lambda rng: [['[{"id": 1, "name": " Ann ", "age": "30", "email": " ANN@x.com"}, {"id": 0, "name": "z", "email": "z@z.z"}, {"id": 2, "name": "  ", "email": "a@b.c"}, {"id": "3", "name": "Cy", "age": 130, "email": "c@d.e"}, {"id": 4, "name": "Di", "email": "nope"}]'], ["[]"],
                 ['[{"id": true, "name": "a", "email": "a@b.c"}, {"id": "07", "name": "b", "age": null, "email": "b@c.d"}, {"id": 5, "name": 7, "email": "a@b.c"}, {"id": 6, "name": "c", "age": true, "email": "a@b.c"}, {"id": 7, "name": "d"}]'],
                 [json.dumps([{"id": rng.choice([1, 2, "3", 0, -1, "x", None]), "name": rng.choice(["a", " ", "bob", None]), "age": rng.choice([None, 5, "12", 121, -3, "x"]), "email": rng.choice(["a@b.co", "A@B.CO ", "bad", "a@b", "@x.y", "a@@b.c"])} for _ in range(20)])]])

add("durations", "medium",
    "`solve(raw)` receives a JSON list of duration strings built from the parts `<n>d`, `<n>h`, `<n>m`, `<n>s` which must appear in that order, each at most once, at least one part present, no spaces inside, case-insensitive; surrounding whitespace is ignored. Return the total seconds as ints (86400 per day, 3600 per hour, 60 per minute), or None for invalid strings.",
    '''import json, re
RX = re.compile(r"^(?:(\\d+)d)?(?:(\\d+)h)?(?:(\\d+)m)?(?:(\\d+)s)?$")
def solve(raw):
    out = []
    for s in json.loads(raw):
        s = s.strip().lower()
        m = RX.match(s)
        if not s or not m:
            out.append(None)
            continue
        d, h, mi, sec = (int(x or 0) for x in m.groups())
        out.append(d * 86400 + h * 3600 + mi * 60 + sec)
    return out
''',
    lambda rng: [['["1h30m", "45s", "2d4h", "", "1m1h", "5", "10M", " 3h "]'], ["[]"], ['["0s", "1d1d", "1h 30m", "99999s", "1.5h", "d", "2h5s"]'],
                 [json.dumps([rng.choice(["%dh" % rng.randint(0, 30), "%dm%ds" % (rng.randint(0, 99), rng.randint(0, 99)), "%dd%dh%dm%ds" % tuple(rng.randint(0, 9) for _ in range(4)), "1s2m", "x", ""]) for _ in range(25)])]])

add("normalize_names", "medium",
    "`solve(raw)` receives a JSON list of person names, each either 'First Last...' or 'Last, First...'. Collapse runs of whitespace to one space and strip. If the name contains a comma, split at the FIRST comma and reorder as '<after> <before>' (stripping each side again). Then capitalise every space-separated word as `w[:1].upper() + w[1:].lower()`. Return the list of normalised names.",
    '''import json
def solve(raw):
    out = []
    for n in json.loads(raw):
        n = " ".join(n.split())
        if "," in n:
            a, b = n.split(",", 1)
            n = " ".join((b.strip() + " " + a.strip()).split())
        out.append(" ".join(w[:1].upper() + w[1:].lower() for w in n.split(" ")))
    return out
''',
    lambda rng: [['["  mcDONALD,  john ", "ada   LOVELACE", "hopper, grace brewster", "o\'neil, pat"]'], ["[]"], ['["", ",", "x,", ",y", "a,b,c", "JEAN-LUC picard"]'],
                 [json.dumps([rng.choice(["smith, JOHN", "  mary   JANE watson", "doe,j", "bob   ROSS", "li,  wei  ming"]) for _ in range(15)])]])

add("near_dupes", "medium",
    "`solve(raw)` receives CSV text with header `id,name,zip`. Two rows are duplicates if their key is equal, where key = (name lower-cased with every non-alphanumeric character removed, first 5 digits of zip after removing every non-digit character). Keep the first row of each key. Return {'kept': [ids (as strings) of kept rows in file order], 'dropped': number of dropped rows}.",
    '''import csv, io, re
def solve(raw):
    seen, kept, dropped = set(), [], 0
    for r in csv.DictReader(io.StringIO(raw)):
        key = (re.sub(r"[^a-z0-9]", "", r["name"].lower()), re.sub(r"\\D", "", r["zip"])[:5])
        if key in seen:
            dropped += 1
        else:
            seen.add(key)
            kept.append(r["id"])
    return {"kept": kept, "dropped": dropped}
''',
    lambda rng: [['id,name,zip\n1,Acme Inc.,94105-1234\n2,ACME INC,94105\n3,Acme Inc,10001\n4,"Bob\'s Shop",  9 4 1 0 5\n'], ["id,name,zip\n"], ["id,name,zip\n1,a,12\n2,A.,1-2\n3,a,123456\n4,a,12345\n"],
                 [rcsv(rng, "id,name,zip", 25, lambda r, i: f"{i},{r.choice(['Foo Bar', 'foo-bar', 'Baz', 'BAZ!', 'Qux'])},{r.choice(['11111', '11111-2222', '22222', '1 1 1 1 1'])}")]])

add("ledger", "hard",
    "`solve(raw)` receives CSV text with header `date,account,amount,type` where type is 'credit' (adds) or 'debit' (subtracts); amount is a non-negative decimal with at most 2 decimals. Rows are in arbitrary order: process them sorted by date ascending (ISO strings), keeping file order among equal dates. For each account return {'balance': final balance as a float rounded to 2 decimals, 'overdrawn_on': the date of the first processed row after which the running balance was below zero, or None}. Return a dict keyed by account.",
    '''import csv, io
from decimal import Decimal
def solve(raw):
    rows = list(csv.DictReader(io.StringIO(raw)))
    rows.sort(key=lambda r: r["date"])
    bal, over = {}, {}
    for r in rows:
        a = r["account"]
        amt = Decimal(r["amount"])
        bal[a] = bal.get(a, Decimal(0)) + (amt if r["type"] == "credit" else -amt)
        over.setdefault(a, None)
        if bal[a] < 0 and over[a] is None:
            over[a] = r["date"]
    return {a: {"balance": float(round(b, 2)), "overdrawn_on": over[a]} for a, b in bal.items()}
''',
    lambda rng: [["date,account,amount,type\n2024-01-03,A,50.00,debit\n2024-01-01,A,30.25,credit\n2024-01-02,B,10,credit\n2024-01-05,A,100,credit\n"], ["date,account,amount,type\n"],
                 ["date,account,amount,type\n2024-02-01,X,5,debit\n2024-02-01,X,5,credit\n2024-02-02,X,0.10,debit\n2024-02-03,X,1,credit\n"],
                 [rcsv(rng, "date,account,amount,type", 30, lambda r, i: f"2024-01-{r.randint(1, 9):02d},{r.choice(['A', 'B', 'C'])},{r.randint(0, 9999) / 100:.2f},{r.choice(['credit', 'debit'])}")]])

add("units_grams", "medium",
    "`solve(raw)` receives a JSON list of strings like '5 kg', '200g', '1.5 lb', '3 OZ'. Pattern: optional whitespace, a non-negative decimal number, optional whitespace, a unit (case-insensitive: kg=1000 g, g=1, lb=453.592 g, oz=28.3495 g), optional whitespace. Return the amount in grams as a float rounded to 1 decimal, or None for any string that does not fit (unknown unit, missing number, negative number).",
    '''import json, re
RX = re.compile(r"^\\s*(\\d+(?:\\.\\d+)?)\\s*([a-zA-Z]+)\\s*$")
F = {"kg": 1000.0, "g": 1.0, "lb": 453.592, "oz": 28.3495}
def solve(raw):
    out = []
    for s in json.loads(raw):
        m = RX.match(s)
        u = m.group(2).lower() if m else None
        out.append(round(float(m.group(1)) * F[u], 1) if m and u in F else None)
    return out
''',
    lambda rng: [['["5 kg", "200g", "1.5 lb", "3 OZ", "7 stone", "-2 kg", "kg", "12"]'], ["[]"], ['[" 0 g ", "0.5kg", "1 lbs", "2..5 kg", "10 Kg"]'],
                 [json.dumps(["%s %s" % (rng.choice(["1", "2.5", "10", "0.25", "100"]), rng.choice(["kg", "g", "lb", "OZ", "mg", "Oz"])) for _ in range(25)])]])

add("transpose", "easy",
    "`solve(raw)` receives CSV text with no header. Parse it with the csv module (quoted fields allowed), skip completely blank lines, and return the transposed table as a list of columns, each column a list of strings. Rows shorter than the longest row are padded with '' at the end. Empty input -> [].",
    '''import csv, io
def solve(raw):
    rows = [r for r in csv.reader(io.StringIO(raw)) if r]
    if not rows:
        return []
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    return [[r[i] for r in rows] for i in range(w)]
''',
    lambda rng: [["a,b,c\n1,2\n\nx,y,z\n"], [""], ['"q,1",2\n3\n'],
                 [rcsv(rng, "h1,h2,h3", 6, lambda r, i: ",".join(str(r.randint(0, 9)) for _ in range(r.randint(1, 4))))]])

add("hourly_buckets", "hard",
    "`solve(raw)` receives a JSON list of ISO-8601 timestamp strings. Each timestamp either ends in 'Z', carries an offset with a colon such as '+05:30' or '-08:00', or is naive (no offset), in which case it is already UTC. Convert every timestamp to UTC and count events per UTC hour. Return a dict mapping 'YYYY-MM-DDTHH' to the count.",
    '''import json
from datetime import datetime, timezone
def solve(raw):
    out = {}
    for s in json.loads(raw):
        t = datetime.fromisoformat(s)
        t = t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc)
        k = t.strftime("%Y-%m-%dT%H")
        out[k] = out.get(k, 0) + 1
    return out
''',
    lambda rng: [['["2024-03-05T10:15:00Z", "2024-03-05T15:45:00+05:30", "2024-03-05T10:59:59", "2024-03-05T02:00:00-08:00"]'], ["[]"], ['["2024-12-31T23:30:00-01:00", "2025-01-01T00:10:00+00:00", "2024-03-10T00:00:00+14:00"]'],
                 [json.dumps(["2024-03-%02dT%02d:%02d:00%s" % (rng.randint(1, 3), rng.randint(0, 23), rng.randint(0, 59), rng.choice(["Z", "", "+05:30", "-08:00", "+00:00"])) for _ in range(30)])]])

add("access_log", "medium",
    "`solve(text)` receives Apache-style access log lines: `IP - - [date] \"METHOD /path?query HTTP/1.1\" STATUS BYTES`. Lines that do not match this shape (quoted request with 3 parts, then a 3-digit status, then bytes or '-') are ignored. Return {'by_status': {class: count} using classes '2xx','3xx','4xx','5xx' (only classes present), 'top_path': the most requested path with the query string removed (ties: alphabetically first), or None if there are no valid lines}.",
    '''import re
from collections import Counter
RX = re.compile(r'^\\S+ \\S+ \\S+ \\[[^\\]]+\\] "(\\S+) (\\S+) (\\S+)" (\\d{3}) (\\d+|-)$')
def solve(text):
    cls, paths = Counter(), Counter()
    for line in text.splitlines():
        m = RX.match(line.strip())
        if not m:
            continue
        cls[m.group(4)[0] + "xx"] += 1
        paths[m.group(2).split("?")[0]] += 1
    top = sorted(paths.items(), key=lambda kv: (-kv[1], kv[0]))
    return {"by_status": dict(cls), "top_path": top[0][0] if top else None}
''',
    lambda rng: [['1.2.3.4 - - [10/Oct/2023:13:55:36 +0000] "GET /a?x=1 HTTP/1.1" 200 2326\n1.2.3.4 - - [10/Oct/2023:13:55:37 +0000] "GET /a HTTP/1.1" 404 -\ngarbage\n5.6.7.8 - - [10/Oct/2023:13:55:38 +0000] "POST /b HTTP/1.1" 500 12\n'], [""],
                 ['h - - [d] "GET /z HTTP/1.1" 301 5\nh - - [d] "GET /y HTTP/1.1" 301 5\nh - - [d] "GET /y" 200 5\nh - - [d] "GET /y HTTP/1.1" 20 5\n'],
                 ["\n".join('9.9.9.%d - - [10/Oct/2023:13:55:36 +0000] "%s %s HTTP/1.1" %d %d' % (rng.randint(1, 5), rng.choice(["GET", "POST"]), rng.choice(["/a", "/b?q=1", "/c", "/a?z=2"]), rng.choice([200, 200, 301, 404, 503]), rng.randint(0, 999)) for _ in range(30))]])

add("build_tree", "hard",
    "`solve(raw)` receives CSV text with header `id,parent_id,name`. Build the forest: a row is a root if parent_id is blank OR refers to an id that does not exist. Return a list of root nodes sorted by id ascending (as ints), where each node is {'id': int, 'name': str, 'children': [child nodes sorted by id ascending]}. No cycles in the input.",
    '''import csv, io
def solve(raw):
    rows = {int(r["id"]): r for r in csv.DictReader(io.StringIO(raw))}
    kids = {}
    roots = []
    for i, r in rows.items():
        p = r["parent_id"].strip()
        if p and int(p) in rows:
            kids.setdefault(int(p), []).append(i)
        else:
            roots.append(i)
    def node(i):
        return {"id": i, "name": rows[i]["name"], "children": [node(c) for c in sorted(kids.get(i, []))]}
    return [node(i) for i in sorted(roots)]
''',
    lambda rng: [["id,parent_id,name\n1,,root\n2,1,a\n3,1,b\n4,2,c\n9,77,orphan\n"], ["id,parent_id,name\n"], ["id,parent_id,name\n5,3,x\n3,,y\n4,5,z\n"],
                 [rcsv(rng, "id,parent_id,name", 15, lambda r, i: "%d,%s,n%d" % (i + 1, (str(r.randint(1, i)) if i and r.random() < 0.8 else ''), i + 1))]])

add("tag_set", "easy",
    "`solve(raw)` receives a JSON list of strings, each a comma-separated list of tags (e.g. 'Python, SQL ,  data'). Strip and lower-case every tag, drop empty tags, and return the sorted list of unique tags.",
    '''import json
def solve(raw):
    tags = set()
    for s in json.loads(raw):
        for t in s.split(","):
            t = t.strip().lower()
            if t:
                tags.add(t)
    return sorted(tags)
''',
    lambda rng: [['["Python, SQL ,  data", "sql,,Spark", ""]'], ["[]"], ['[" , ", "A,a,A", "b c, B C"]'],
                 [json.dumps([", ".join(rng.choice(["x", "Y", "z", "  w ", "", "Q"]) for _ in range(4)) for _ in range(8)])]])
