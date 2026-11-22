"""Easy families. Each family: files (templates with @tok@), fix/bad replacements, test, extra, gt, variants."""

FAMILIES = []


def fam(**kw):
    FAMILIES.append(kw)


# 1 ---------------------------------------------------------------- off-by-one: 1-based page
fam(key="page_bounds", cat="off-by-one", diff="easy", tags=["red_herring"],
    files={
        "paginate.py": r'''
def page_bounds(page, per_page):
    """Return (start, end) slice indexes for a 1-based page number."""
    start = page * per_page
    return start, start + per_page


def page_count(total, per_page):
    """Number of pages needed for `total` items."""
    return (total + per_page - 1) // per_page
''',
        "@mod@.py": r'''
from paginate import page_bounds, page_count


def @fn@(@things@, page, per_page=@pp@):
    start, end = page_bounds(page, per_page)
    return @things@[start:end]


def @fn@_summary(@things@, per_page=@pp@):
    return {"pages": page_count(len(@things@), per_page), "total": len(@things@)}
''',
    },
    fix=[("paginate.py", "start = page * per_page", "start = (page - 1) * per_page")],
    test=r'''
from @mod@ import @fn@, @fn@_summary

data = list(range(1, @n@ + 1))
assert @fn@(data, 1) == data[0:@pp@]
assert @fn@(data, 2) == data[@pp@:2 * @pp@]
last = @fn@_summary(data)["pages"]
assert @fn@(data, last) == data[(last - 1) * @pp@:]
''',
    extra=r'''
assert @fn@_summary(data) == {"pages": @pages@, "total": @n@}
assert @fn@(data, last + 1) == []
assert @fn@([], 1) == []
''',
    gt=dict(file="paginate.py", func="page_bounds", cause="page_bounds treats the 1-based page number as 0-based, so every page is shifted by one page"),
    variants=[
        dict(mod="inbox", fn="messages_page", things="messages", pp="10", n="25", pages="3"),
        dict(mod="catalog", fn="products_page", things="products", pp="5", n="12", pages="3"),
        dict(mod="audit", fn="entries_page", things="entries", pp="20", n="41", pages="3"),
        dict(mod="feed", fn="posts_page", things="posts", pp="8", n="64", pages="8"),
    ])

# 2 ---------------------------------------------------------------- wrong default (minimal diff)
fam(key="retry_default", cat="wrong default", diff="easy", tags=["red_herring", "minimal_diff"],
    files={
        "config.py": r'''
DEFAULTS = {"@key@": @r0@, "timeout": 5, "verbose": False}


def load(overrides=None):
    cfg = dict(DEFAULTS)
    cfg.update(overrides or {})
    return cfg
''',
        "client.py": r'''
from config import load


class Client:
    def __init__(self, **overrides):
        self.cfg = load(overrides)
        self.calls = 0

    def fetch(self, op):
        attempts = self.cfg["@key@"] + 1
        last = None
        for _ in range(attempts):
            self.calls += 1
            try:
                return op()
            except ConnectionError as exc:
                last = exc
        raise last
''',
    },
    fix=[("config.py", '"@key@": @r0@,', '"@key@": @r@,')],
    test=r'''
from client import Client


def make_flaky(n):
    state = {"left": n}

    def op():
        if state["left"] > 0:
            state["left"] -= 1
            raise ConnectionError("@msg@")
        return "ok"
    return op


c = Client()
assert c.fetch(make_flaky(@n@)) == "ok"
assert c.calls == @n@ + 1
''',
    extra=r'''
c2 = Client(@key@=0)
try:
    c2.fetch(make_flaky(1))
    raise SystemExit("override of 0 must still mean no retries")
except ConnectionError:
    pass
assert c2.calls == 1
assert Client().cfg["timeout"] == 5
''',
    gt=dict(file="config.py", func="DEFAULTS", cause="the default for @key@ is @r0@, so the client never retries a transient failure"),
    variants=[
        dict(key="retries", r0="0", r="3", n="2", msg="link down"),
        dict(key="max_retries", r0="0", r="4", n="3", msg="peer reset"),
        dict(key="retries", r0="1", r="2", n="2", msg="dns timeout"),
        dict(key="extra_attempts", r0="0", r="5", n="4", msg="socket closed"),
    ])

# 3 ---------------------------------------------------------------- mutated shared state: mutable default
fam(key="tally_default", cat="mutated shared state", diff="easy", tags=["red_herring"],
    files={
        "report.py": r'''
def @fn@(words, counts={}):
    """Count word occurrences; pass `counts` to continue an earlier tally."""
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return counts


def top(counts, n=1):
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
''',
    },
    fix=[("report.py", "def @fn@(words, counts={}):", "def @fn@(words, counts=None):"),
         ("report.py", '    for w in words:', '    if counts is None:\n        counts = {}\n    for w in words:')],
    test=r'''
from report import @fn@, top

a = @fn@(@A@)
b = @fn@(@B@)
assert b == @EB@, b
assert a == @EA@, a
''',
    extra=r'''
c = @fn@(@B@, counts=dict(a))
assert c == @EC@
assert top(@fn@(@A@), 1) == [@TOP@]
''',
    gt=dict(file="report.py", func="@fn@", cause="mutable default argument `counts={}` is shared by every call, so tallies leak between calls"),
    variants=[
        dict(fn="tally", A='["x", "y", "x"]', B='["y"]', EA='{"x": 2, "y": 1}', EB='{"y": 1}', EC='{"x": 2, "y": 2}', TOP='("x", 2)'),
        dict(fn="count_tokens", A='["to", "be", "or", "to"]', B='["be"]', EA='{"to": 2, "be": 1, "or": 1}', EB='{"be": 1}', EC='{"to": 2, "be": 2, "or": 1}', TOP='("to", 2)'),
        dict(fn="histogram", A='["a", "b", "b", "b"]', B='["a", "a"]', EA='{"a": 1, "b": 3}', EB='{"a": 2}', EC='{"a": 3, "b": 3}', TOP='("b", 3)'),
        dict(fn="tally_votes", A='["red", "blue", "red"]', B='["blue", "blue"]', EA='{"red": 2, "blue": 1}', EB='{"blue": 2}', EC='{"red": 2, "blue": 3}', TOP='("blue", 3)'),
    ])
# variant 4: C has blue 1+2=3 and top of a is red 2 -> fix below in TOP semantic: top(fn(A)) uses fresh tally
FAMILIES[-1]["variants"][3]["TOP"] = '("red", 2)'

# 4 ---------------------------------------------------------------- aliasing: [[x]*c]*r
fam(key="grid_alias", cat="aliasing", diff="easy", tags=["red_herring"],
    files={
        "board.py": r'''
def new_board(rows, cols, fill="@fill@"):
    return [[fill] * cols] * rows


def place(board, r, c, mark):
    board[r][c] = mark


def render(board):
    return "\n".join("".join(row) for row in board)


def count(board, mark):
    return sum(row.count(mark) for row in board)
''',
    },
    fix=[("board.py", "return [[fill] * cols] * rows", "return [[fill] * cols for _ in range(rows)]")],
    test=r'''
from board import new_board, place, render, count

b = new_board(@R@, @C@)
place(b, 0, 0, "@m1@")
place(b, @R@ - 1, @C@ - 1, "@m2@")
exp = [["@fill@"] * @C@ for _ in range(@R@)]
exp[0][0] = "@m1@"
exp[@R@ - 1][@C@ - 1] = "@m2@"
assert b == exp, render(b)
''',
    extra=r'''
assert count(b, "@m1@") == 1 and count(b, "@m2@") == 1
assert render(new_board(2, 2)) == "@fill@@fill@\n@fill@@fill@"
''',
    gt=dict(file="board.py", func="new_board", cause="`[row] * rows` repeats one shared row list, so writing one cell writes the same column in every row"),
    variants=[
        dict(R="3", C="3", fill=".", m1="X", m2="O"),
        dict(R="2", C="4", fill="-", m1="#", m2="@"),
        dict(R="4", C="2", fill="_", m1="A", m2="B"),
        dict(R="5", C="5", fill="0", m1="1", m2="2"),
    ])

# 5 ---------------------------------------------------------------- wrong unit (minimal diff)
fam(key="to_ms", cat="wrong unit", diff="easy", tags=["red_herring", "minimal_diff"],
    files={
        "units.py": r'''
FACTORS = {"ms": 1, "s": @fs@, "m": @fm@, "h": @fh@, "d": @fd@}


def to_ms(amount, unit):
    """Convert a duration to milliseconds."""
    return amount * FACTORS[unit]


def to_seconds(ms):
    return ms / 1000
''',
        "deadline.py": r'''
from units import to_ms


def deadline(start_ms, amount, unit):
    return start_ms + to_ms(amount, unit)


def expired(now_ms, start_ms, amount, unit):
    return now_ms >= deadline(start_ms, amount, unit)
''',
    },
    fix=[("units.py", '"@k@": @bad@', '"@k@": @good@')],
    test=r'''
from units import to_ms
from deadline import deadline, expired

assert to_ms(3, "@k@") == 3 * @good@
assert deadline(1000, 2, "@k@") == 1000 + 2 * @good@
assert not expired(1000 + 2 * @good@ - 1, 1000, 2, "@k@")
''',
    extra=r'''
assert to_ms(5, "ms") == 5
assert to_ms(1, "s") == 1000 and to_ms(1, "m") == 60000
assert to_ms(1, "h") == 3600000 and to_ms(1, "d") == 86400000
assert expired(1000 + 2 * @good@, 1000, 2, "@k@")
''',
    gt=dict(file="units.py", func="FACTORS", cause="the factor for '@k@' is expressed in a different unit (@bad@) than the milliseconds every other entry uses"),
    variants=[
        dict(k="m", bad="60", good="60000", fs="1000", fm="60", fh="3600000", fd="86400000"),
        dict(k="h", bad="3600", good="3600000", fs="1000", fm="60000", fh="3600", fd="86400000"),
        dict(k="d", bad="86400", good="86400000", fs="1000", fm="60000", fh="3600000", fd="86400"),
        dict(k="s", bad="1", good="1000", fs="1", fm="60000", fh="3600000", fd="86400000"),
    ])

# 6 ---------------------------------------------------------------- incorrect exception handling: blanket except
fam(key="reserve_swallow", cat="incorrect exception handling", diff="easy", tags=[],
    files={
        "inventory.py": r'''
class OutOfStock(Exception):
    pass


def reserve(stock, sku, qty):
    """Take qty units from stock. Raises OutOfStock if there are not enough."""
    try:
        if stock[sku] < qty:
            raise OutOfStock(sku)
        stock[sku] -= qty
    except Exception:
        return False
    return True
''',
        "orders.py": r'''
from inventory import reserve, OutOfStock


def fulfil(stock, lines):
    shipped, backordered = [], []
    for sku, qty in lines:
        try:
            reserve(stock, sku, qty)
            shipped.append(sku)
        except OutOfStock:
            backordered.append(sku)
    return shipped, backordered
''',
    },
    fix=[("inventory.py", """    try:
        if stock[sku] < qty:
            raise OutOfStock(sku)
        stock[sku] -= qty
    except Exception:
        return False
    return True""", """    if stock[sku] < qty:
        raise OutOfStock(sku)
    stock[sku] -= qty
    return True""")],
    test=r'''
from orders import fulfil

stock = {"@a@": @sa@, "@b@": @sb@}
shipped, back = fulfil(stock, [("@a@", @qa@), ("@b@", @qb@)])
assert shipped == ["@a@"], shipped
assert back == ["@b@"], back
''',
    extra=r'''
assert stock == {"@a@": @ra@, "@b@": @sb@}
try:
    fulfil(stock, [("nope", 1)])
    raise SystemExit("unknown sku must raise KeyError")
except KeyError:
    pass
''',
    gt=dict(file="inventory.py", func="reserve", cause="the blanket `except Exception` swallows OutOfStock and returns False, so the caller never sees the exception and ships anyway"),
    variants=[
        dict(a="bolt", b="nut", sa="10", sb="1", qa="4", qb="3", ra="6"),
        dict(a="pen", b="ink", sa="5", sb="0", qa="5", qb="1", ra="0"),
        dict(a="cable", b="plug", sa="9", sb="2", qa="1", qb="7", ra="8"),
        dict(a="tile", b="glue", sa="100", sb="3", qa="25", qb="4", ra="75"),
    ])

# 7 ---------------------------------------------------------------- None handling
fam(key="nickname_none", cat="wrong type/None handling", diff="easy", tags=["red_herring"],
    files={
        "people.py": r'''
def display_name(user):
    """Nickname if the user set a non-blank one, otherwise the full name."""
    nick = user.get("@nick@")
    return nick.strip() or user["name"]


def initials(user):
    return "".join(part[0].upper() for part in user["name"].split())
''',
        "directory.py": r'''
from people import display_name


def labels(users):
    return [display_name(u) for u in users]
''',
    },
    fix=[("people.py", """    nick = user.get("@nick@")
    return nick.strip() or user["name"]""", """    nick = (user.get("@nick@") or "").strip()
    return nick or user["name"]""")],
    test=r'''
from directory import labels

users = [
    {"name": "@n1@", "@nick@": "@k1@"},
    {"name": "@n2@"},
    {"name": "@n3@", "@nick@": "   "},
    {"name": "@n4@", "@nick@": None},
]
assert labels(users) == ["@k1@", "@n2@", "@n3@", "@n4@"], labels(users)
''',
    extra=r'''
from people import initials
assert initials({"name": "@n1@"}) == "@ini@"
assert labels([{"name": "Z", "@nick@": "  pad  "}]) == ["pad"]
''',
    gt=dict(file="people.py", func="display_name", cause="user.get('@nick@') can be None (missing key or null value) and .strip() is called on it unguarded"),
    variants=[
        dict(nick="nickname", n1="Ada Lovelace", k1="countess", n2="Alan Turing", n3="Grace Hopper", n4="Linus T", ini="AL"),
        dict(nick="alias", n1="Maya Angelou", k1="maya", n2="Toni Morrison", n3="Octavia Butler", n4="Ursula Le Guin", ini="MA"),
        dict(nick="handle", n1="Ravi Shankar", k1="rs", n2="Zakir Hussain", n3="Anoushka S", n4="Ali Akbar", ini="RS"),
        dict(nick="short_name", n1="Katherine Johnson", k1="kj", n2="Mary Jackson", n3="Dorothy Vaughan", n4="Margot Shetterly", ini="KJ"),
    ])

# 8 ---------------------------------------------------------------- ordering
fam(key="leaderboard_order", cat="incorrect ordering", diff="easy", tags=["red_herring"],
    files={
        "leaderboard.py": r'''
def rank(scores):
    """(name, score) pairs, highest score first; ties are broken by name A-Z."""
    return sorted(scores.items(), key=lambda kv: (kv[1], kv[0]))


def position(scores, name):
    names = [n for n, _ in rank(scores)]
    return names.index(name) + 1
''',
        "top.py": r'''
from leaderboard import rank


def top_names(scores, n):
    return [name for name, _ in rank(scores)[:n]]
''',
    },
    fix=[("leaderboard.py", "key=lambda kv: (kv[1], kv[0])", "key=lambda kv: (-kv[1], kv[0])")],
    test=r'''
from top import top_names

scores = @S@
assert top_names(scores, @N@) == @E@, top_names(scores, @N@)
''',
    extra=r'''
from leaderboard import position, rank
assert position(scores, "@first@") == 1
assert [s for _, s in rank(scores)] == sorted(scores.values(), reverse=True)
''',
    gt=dict(file="leaderboard.py", func="rank", cause="sort key orders scores ascending; it needs descending score with name as ascending tie-break"),
    variants=[
        dict(S='{"ann": 7, "bob": 9, "cy": 9, "dee": 3}', N="3", E='["bob", "cy", "ann"]', first="bob"),
        dict(S='{"zed": 1, "amy": 5, "kim": 5, "lou": 8, "ned": 2}', N="2", E='["lou", "amy"]', first="lou"),
        dict(S='{"p1": 40, "p2": 40, "p3": 50}', N="2", E='["p3", "p1"]', first="p3"),
        dict(S='{"x": 0, "y": 10, "z": 5}', N="3", E='["y", "z", "x"]', first="y"),
    ])
