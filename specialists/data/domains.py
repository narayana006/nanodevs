"""Schemas + deterministic data generators for the six shared domains."""
import datetime as dt
import random

D = dt.date
TD = dt.timedelta

SCHEMAS = {
"shop": """CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT NOT NULL,
  signup_date TEXT NOT NULL,          -- YYYY-MM-DD
  referred_by INTEGER REFERENCES customers(id)   -- NULL when not referred
);
CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  price REAL NOT NULL
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  order_date TEXT NOT NULL,           -- YYYY-MM-DD
  status TEXT NOT NULL,               -- 'paid', 'refunded', 'pending', 'cancelled'
  ship_date TEXT                      -- YYYY-MM-DD, NULL if not shipped
);
CREATE TABLE order_items (
  order_id INTEGER NOT NULL REFERENCES orders(id),
  product_id INTEGER NOT NULL REFERENCES products(id),
  qty INTEGER NOT NULL,
  discount REAL,                      -- fraction 0..1, NULL means no discount
  PRIMARY KEY (order_id, product_id)
);""",
"hr": """CREATE TABLE departments (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  budget INTEGER NOT NULL
);
CREATE TABLE employees (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  dept_id INTEGER NOT NULL REFERENCES departments(id),
  manager_id INTEGER REFERENCES employees(id),   -- NULL for top-level
  salary INTEGER NOT NULL,
  hire_date TEXT NOT NULL,                       -- YYYY-MM-DD
  term_date TEXT                                 -- NULL while employed
);
CREATE TABLE bonuses (
  emp_id INTEGER NOT NULL REFERENCES employees(id),
  year INTEGER NOT NULL,
  amount INTEGER,                                -- may be NULL (not yet decided)
  PRIMARY KEY (emp_id, year)
);""",
"events": """CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  plan TEXT NOT NULL,                 -- 'free', 'pro', 'team'
  country TEXT NOT NULL,
  created_at TEXT NOT NULL            -- YYYY-MM-DD HH:MM:SS
);
CREATE TABLE events (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  ts TEXT NOT NULL,                   -- YYYY-MM-DD HH:MM:SS (UTC)
  kind TEXT NOT NULL,                 -- 'signup', 'view', 'click', 'purchase'
  page TEXT,
  amount REAL                         -- only for purchases, may be NULL
);""",
"library": """CREATE TABLE authors (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT NOT NULL
);
CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author_id INTEGER NOT NULL REFERENCES authors(id),
  genre TEXT NOT NULL,
  year INTEGER NOT NULL,
  pages INTEGER NOT NULL
);
CREATE TABLE members (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  joined TEXT NOT NULL                -- YYYY-MM-DD
);
CREATE TABLE loans (
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL REFERENCES books(id),
  member_id INTEGER NOT NULL REFERENCES members(id),
  loaned_on TEXT NOT NULL,            -- YYYY-MM-DD
  due_on TEXT NOT NULL,               -- YYYY-MM-DD
  returned_on TEXT                    -- NULL while still out
);""",
"sensors": """CREATE TABLE sensors (
  id INTEGER PRIMARY KEY,
  site TEXT NOT NULL,
  kind TEXT NOT NULL                  -- 'temp' or 'humidity'
);
CREATE TABLE readings (
  sensor_id INTEGER NOT NULL REFERENCES sensors(id),
  ts TEXT NOT NULL,                   -- YYYY-MM-DD HH:MM:SS
  value REAL,                         -- NULL when the sensor reported nothing
  PRIMARY KEY (sensor_id, ts)
);""",
"school": """CREATE TABLE students (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  year INTEGER NOT NULL               -- 1..4
);
CREATE TABLE courses (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  dept TEXT NOT NULL,                 -- 'MATH', 'CS', 'BIO'
  credits INTEGER NOT NULL
);
CREATE TABLE enrollments (
  student_id INTEGER NOT NULL REFERENCES students(id),
  course_id INTEGER NOT NULL REFERENCES courses(id),
  term TEXT NOT NULL,                 -- 'F23', 'S24', 'F24'
  grade REAL,                         -- 0.0-4.0, NULL if not graded yet
  PRIMARY KEY (student_id, course_id, term)
);""",
}


def gen_shop(rng, n):
    countries = ["US", "DE", "IN", "BR", "JP", "FR"]
    cats = ["Books", "Toys", "Garden", "Kitchen", "Sports"]
    customers = []
    for i in range(1, n + 1):
        ref = rng.randint(1, i - 1) if i > 1 and rng.random() < 0.3 else None
        customers.append((i, f"cust{i:03d}", rng.choice(countries), (D(2023, 1, 1) + TD(days=rng.randint(0, 700))).isoformat(), ref))
    prices = [4.5, 9.99, 12.0, 19.5, 25.0, 49.0]
    npd = max(5, n // 2)
    products = [(i, f"prod{i:03d}", cats[(i - 1) % 5] if i <= 5 else rng.choice(cats), rng.choice(prices)) for i in range(1, npd + 1)]
    orders, items = [], []
    active = max(1, int(n * 0.8))
    active_p = max(3, int(npd * 0.8))   # the last ~20% of products are never ordered
    for oid in range(1, 2 * n + 1):
        cid = rng.randint(1, active)
        od = D(2024, 1, 1) + TD(days=rng.randint(0, 365))
        st = rng.choices(["paid", "refunded", "pending", "cancelled"], [6, 1, 2, 1])[0]
        ship = None
        if st in ("paid", "refunded") and rng.random() < 0.85:
            ship = (od + TD(days=rng.randint(0, 9))).isoformat()
        orders.append((oid, cid, od.isoformat(), st, ship))
        for pid in rng.sample(range(1, active_p + 1), min(active_p, rng.randint(1, 4))):
            items.append((oid, pid, rng.randint(1, 5), rng.choice([None, None, 0.1, 0.2, 0.0])))
    return {"customers": customers, "products": products, "orders": orders, "order_items": items}


def gen_hr(rng, n):
    names = ["Ana", "Bo", "Cy", "Di", "Ed", "Flo", "Gus", "Hal", "Ivy", "Jo"]
    k = max(3, n // 6)
    dn = ["Eng", "Ops", "Sales", "HR", "Legal", "Data"]
    depts = [(i, dn[(i - 1) % 6] + ("" if i <= 6 else str(i)), rng.choice([200000, 300000, 450000, 600000])) for i in range(1, k + 1)]
    sal = [48000, 52000, 60000, 60000, 72000, 85000, 85000, 99000, 120000]
    emps = []
    for i in range(1, n + 1):
        mgr = rng.randint(1, i - 1) if i > 1 and rng.random() < 0.9 else None
        hire = D(2015, 1, 1) + TD(days=rng.randint(0, 3600))
        term = (hire + TD(days=rng.randint(200, 1500))).isoformat() if rng.random() < 0.2 else None
        emps.append((i, f"{rng.choice(names)}{i}", rng.randint(1, k - 1), mgr, rng.choice(sal), hire.isoformat(), term))
    bon = []
    for e in emps:
        for y in (2023, 2024):
            if rng.random() < 0.5:
                bon.append((e[0], y, rng.choice([None, 1000, 2000, 5000])))
    return {"departments": depts, "employees": emps, "bonuses": bon}


def gen_events(rng, n):
    pages = ["/home", "/pricing", "/docs", "/blog", "/cart"]
    base = dt.datetime(2024, 3, 18)
    users, events = [], []
    eid = 1
    for u in range(1, n + 1):
        start = base + TD(days=rng.randint(0, 13), minutes=rng.randint(0, 1439), seconds=rng.randint(0, 59))
        users.append((u, rng.choice(["free", "free", "pro", "team"]), rng.choice(["US", "DE", "IN", "BR"]), start.strftime("%Y-%m-%d %H:%M:%S")))
        t = start
        if rng.random() < 0.9:
            events.append((eid, u, t.strftime("%Y-%m-%d %H:%M:%S"), "signup", None, None))
            eid += 1
        for _ in range(rng.choice([0, 0, 1, 3, 6, 10, 14])):
            t = t + TD(minutes=rng.choice([3, 10, 25, 45, 120, 600, 1500]), seconds=rng.randint(0, 59))
            k = rng.choices(["view", "click", "purchase"], [6, 3, 1])[0]
            amt = rng.choice([None, 9.0, 19.0, 49.0]) if k == "purchase" else None
            events.append((eid, u, t.strftime("%Y-%m-%d %H:%M:%S"), k, rng.choice(pages), amt))
            eid += 1
    events.sort(key=lambda e: (e[2], e[1]))
    events = [(i + 1,) + e[1:] for i, e in enumerate(events)]
    return {"users": users, "events": events}


def gen_library(rng, n):
    countries = ["Norway", "Chile", "Japan", "UK", "Kenya"]
    nouns = ["River", "Garden", "Engine", "Stone", "Letters", "Harbor", "Winter"]
    na = n // 3 + 2
    authors = [(i, f"author{i}", rng.choice(countries)) for i in range(1, na + 1)]
    books = []
    for i in range(1, n + 1):
        books.append((i, f"{rng.choice(['The', 'the', 'A', 'An', 'Of'])} {rng.choice(nouns)} {i}", rng.randint(1, na),
                      rng.choice(["fiction", "history", "science", "poetry", "travel"]), rng.randint(1950, 2023), rng.randint(80, 700)))
    nm = n // 2 + 2
    members = [(i, f"member{i}", (D(2022, 1, 1) + TD(days=rng.randint(0, 500))).isoformat()) for i in range(1, nm + 1)]
    loans = []
    for i in range(1, 3 * n + 1):
        lo = D(2024, 1, 1) + TD(days=rng.randint(0, 180))
        ret = (lo + TD(days=rng.randint(5, 40))).isoformat() if rng.random() < 0.75 else None
        loans.append((i, rng.randint(1, n), rng.randint(1, nm), lo.isoformat(), (lo + TD(days=14)).isoformat(), ret))
    return {"authors": authors, "books": books, "members": members, "loans": loans}


def gen_sensors(rng, n):
    ns = n // 4 + 2
    sensors = [(i, rng.choice(["north", "south", "dock"]), rng.choice(["temp", "humidity"])) for i in range(1, ns + 1)]
    rd = []
    for s in sensors:
        t = dt.datetime(2024, 5, 1) + TD(minutes=rng.randint(0, 59))
        for _ in range(rng.randint(8, 24)):
            v = None if rng.random() < 0.15 else float(round(rng.gauss(25, 6)))
            rd.append((s[0], t.strftime("%Y-%m-%d %H:%M:%S"), v))
            t += TD(minutes=rng.choice([60, 60, 60, 60, 120, 180]))
    return {"sensors": sensors, "readings": rd}


def gen_school(rng, n):
    ns = n
    students = [(i, f"stu{i:03d}", rng.randint(1, 4)) for i in range(1, ns + 1)]
    nc = max(4, n // 4)
    courses = [(i, f"course{i}", ["MATH", "CS", "BIO"][(i - 1) % 3], rng.choice([2, 3, 4, 5])) for i in range(1, nc + 1)]
    enr = []
    for s in students:
        pairs = set()
        for _ in range(rng.randint(2, 5)):
            pairs.add((rng.randint(1, nc), rng.choice(["F23", "S24", "F24"])))
        for c, t in sorted(pairs):
            g = None if rng.random() < 0.15 else rng.choice([2.0, 2.5, 3.0, 3.5, 4.0])
            enr.append((s[0], c, t, g))
    return {"students": students, "courses": courses, "enrollments": enr}


GENS = {"shop": gen_shop, "hr": gen_hr, "events": gen_events, "library": gen_library, "sensors": gen_sensors, "school": gen_school}
