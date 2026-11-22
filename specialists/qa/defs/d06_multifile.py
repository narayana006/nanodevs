TASKS = []

TASKS.append(dict(
    id="qa_mf_inventory", diff="hard", main="stock.py",
    spec="Write tests for the two-module inventory package (`items.py` and `stock.py`). Test the public behaviour of `Inventory`.",
    files={"items.py": r'''
class Item:
    """A product: sku (str, non-empty), price in integer cents (>= 0), reorder_level (int >= 0, default 5).
    Invalid values -> ValueError."""

    def __init__(self, sku, price, reorder_level=5):
        if not sku:
            raise ValueError("sku required")
        if price < 0 or reorder_level < 0:
            raise ValueError("negative value")
        self.sku = sku
        self.price = price
        self.reorder_level = reorder_level
''', "stock.py": r'''
from items import Item


class OutOfStock(Exception):
    pass


class Inventory:
    """Tracks quantities per sku. add_item(item, qty=0) registers an item (duplicate sku -> ValueError).
    receive(sku, n) adds n > 0 units; remove(sku, n) takes n > 0 units, raising OutOfStock if fewer are on hand
    (nothing is removed then). Unknown sku -> KeyError, n < 1 -> ValueError. quantity(sku), value() = total of
    price * quantity in cents, low_stock() = sorted skus whose quantity is <= reorder_level."""

    def __init__(self):
        self._items = {}
        self._qty = {}

    def add_item(self, item, qty=0):
        if item.sku in self._items:
            raise ValueError("duplicate sku")
        if qty < 0:
            raise ValueError("negative qty")
        self._items[item.sku] = item
        self._qty[item.sku] = qty

    def receive(self, sku, n):
        if n < 1:
            raise ValueError("n must be >= 1")
        self._qty[sku] += n

    def remove(self, sku, n):
        if n < 1:
            raise ValueError("n must be >= 1")
        if self._qty[sku] < n:
            raise OutOfStock(sku)
        self._qty[sku] -= n

    def quantity(self, sku):
        return self._qty[sku]

    def value(self):
        return sum(self._items[s].price * q for s, q in self._qty.items())

    def low_stock(self):
        return sorted(s for s, q in self._qty.items() if q <= self._items[s].reorder_level)
'''},
    tests=r'''
from items import Item
from stock import Inventory, OutOfStock

for args in (("", 100), ("a", -1), ("a", 1, -1)):
    try:
        Item(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % (args,))
assert Item("a", 0).price == 0 and Item("a", 5).reorder_level == 5 and Item("a", 5, 0).reorder_level == 0

inv = Inventory()
inv.add_item(Item("apple", 50), 10)
inv.add_item(Item("pear", 75, reorder_level=2), 3)
inv.add_item(Item("fig", 200, reorder_level=0))
assert inv.quantity("apple") == 10 and inv.quantity("fig") == 0
try:
    inv.add_item(Item("apple", 1))
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert inv.quantity("apple") == 10
try:
    inv.add_item(Item("neg", 1), -1)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert inv.value() == 50 * 10 + 75 * 3
inv.receive("fig", 2)
assert inv.quantity("fig") == 2 and inv.value() == 500 + 225 + 400
inv.remove("apple", 4)
assert inv.quantity("apple") == 6
inv.remove("apple", 6)
assert inv.quantity("apple") == 0
try:
    inv.remove("pear", 4)
except OutOfStock:
    pass
else:
    raise AssertionError("expected OutOfStock")
assert inv.quantity("pear") == 3
inv.remove("pear", 3)
assert inv.quantity("pear") == 0
for fn in (inv.receive, inv.remove):
    for n in (0, -1):
        try:
            fn("fig", n)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")
    try:
        fn("ghost", 1)
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
assert inv.quantity("fig") == 2
assert inv.low_stock() == ["apple", "pear"]
inv.receive("pear", 2)
assert inv.low_stock() == ["apple", "pear"]
inv.receive("pear", 1)
assert inv.low_stock() == ["apple"]
inv.receive("fig", 1)
assert inv.low_stock() == ["apple"]
inv2 = Inventory()
inv2.add_item(Item("zed", 1))
inv2.add_item(Item("bee", 1))
assert inv2.low_stock() == ["bee", "zed"]
''',
    muts=[
        ("boundary: low stock at exactly reorder level", "if q <= self._items[s].reorder_level", "if q < self._items[s].reorder_level"),
        ("boundary: remove exact stock", "if self._qty[sku] < n:", "if self._qty[sku] <= n:"),
        ("missing-edge-case: remove partially before raising", "            raise OutOfStock(sku)\n        self._qty[sku] -= n", "            self._qty[sku] = 0\n            raise OutOfStock(sku)\n        self._qty[sku] -= n"),
        ("missing-edge-case: duplicate sku", 'if item.sku in self._items:\n            raise ValueError("duplicate sku")', "if False:\n            pass"),
        ("logic: value ignores price", "self._items[s].price * q", "q"),
        ("ordering: low_stock unsorted", "return sorted(s for s, q in", "return list(s for s, q in"),
        ("boundary: free items rejected", "stock_placeholder", "stock_placeholder") if False else ("boundary: zero price rejected", "items.py", "if price < 0 or reorder_level < 0:", "if price <= 0 or reorder_level < 0:"),
        ("boundary: receive 0 accepted", "        if n < 1:\n            raise ValueError(\"n must be >= 1\")\n        self._qty[sku] += n", "        if n < 0:\n            raise ValueError(\"n must be >= 1\")\n        self._qty[sku] += n"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_mf_cart", diff="hard", main="pricing.py",
    spec="Write tests for the shopping-cart package (`catalog.py`, `pricing.py`, `cart.py`). Test `Cart` behaviour end to end.",
    files={"catalog.py": r'''
PRICES = {"apple": 100, "bread": 250, "milk": 199, "cheese": 800}


def price_of(name):
    """Unit price in cents. Unknown product -> KeyError."""
    return PRICES[name]
''', "pricing.py": r'''
def bulk_discount(qty, unit_price):
    """Line discount in cents: 10% off the line when qty >= 10, 5% off when qty >= 5 (integer division)."""
    line = qty * unit_price
    if qty >= 10:
        return line * 10 // 100
    if qty >= 5:
        return line * 5 // 100
    return 0


def coupon_discount(subtotal, code):
    """'SAVE5' -> 500 cents off (never more than the subtotal); 'HALF' -> half the subtotal (integer division);
    unknown code -> ValueError."""
    if code == "SAVE5":
        return min(500, subtotal)
    if code == "HALF":
        return subtotal // 2
    raise ValueError("unknown coupon")
''', "cart.py": r'''
from catalog import price_of
from pricing import bulk_discount, coupon_discount


class Cart:
    """add(name, qty=1) (qty >= 1 else ValueError; unknown product -> KeyError; adding again increases qty),
    remove(name) drops the line (KeyError if absent), apply_coupon(code) sets one coupon (the latest replaces the
    previous one; unknown -> ValueError), subtotal() = sum of line totals after bulk discounts,
    total() = subtotal minus coupon, shipping added: 0 if the discounted total >= 2000 cents or the cart is empty,
    otherwise 499. total() = discounted subtotal + shipping."""

    def __init__(self):
        self._lines = {}
        self._coupon = None

    def add(self, name, qty=1):
        if qty < 1:
            raise ValueError("qty must be >= 1")
        price_of(name)
        self._lines[name] = self._lines.get(name, 0) + qty

    def remove(self, name):
        del self._lines[name]

    def apply_coupon(self, code):
        coupon_discount(0, code)
        self._coupon = code

    def subtotal(self):
        total = 0
        for name, qty in self._lines.items():
            p = price_of(name)
            total += qty * p - bulk_discount(qty, p)
        return total

    def total(self):
        sub = self.subtotal()
        if self._coupon:
            sub -= coupon_discount(sub, self._coupon)
        if not self._lines or sub >= 2000:
            return sub
        return sub + 499
'''},
    tests=r'''
from cart import Cart
from pricing import bulk_discount, coupon_discount
from catalog import price_of

assert price_of("apple") == 100
try:
    price_of("unicorn")
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
assert bulk_discount(1, 100) == 0
assert bulk_discount(4, 100) == 0
assert bulk_discount(5, 100) == 25
assert bulk_discount(9, 100) == 45
assert bulk_discount(10, 100) == 100
assert bulk_discount(20, 199) == 398
assert bulk_discount(5, 199) == 49
assert coupon_discount(1000, "SAVE5") == 500
assert coupon_discount(300, "SAVE5") == 300
assert coupon_discount(1001, "HALF") == 500
assert coupon_discount(0, "HALF") == 0
try:
    coupon_discount(100, "BOGUS")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")

c = Cart()
assert c.subtotal() == 0 and c.total() == 0
c.add("apple")
assert c.subtotal() == 100 and c.total() == 599
c.add("apple", 3)
assert c.subtotal() == 400
c.add("apple")
assert c.subtotal() == 475
c.add("bread", 4)
assert c.subtotal() == 475 + 1000
assert c.total() == 1475 + 499
c.add("cheese", 1)
assert c.subtotal() == 2275 and c.total() == 2275
c.remove("cheese")
assert c.subtotal() == 1475
c.apply_coupon("SAVE5")
assert c.total() == 1475 - 500 + 499
c.apply_coupon("HALF")
assert c.total() == 1475 - 737 + 499
c.add("cheese", 3)
assert c.subtotal() == 475 + 1000 + 2400
assert c.total() == 3875 - 1937 + 499
try:
    c.apply_coupon("NOPE")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert c.total() == 3875 - 1937 + 499
for args in (("apple", 0), ("apple", -2)):
    try:
        c.add(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
try:
    c.add("ghost")
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
try:
    c.remove("ghost")
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
d = Cart()
d.add("cheese", 2)
d.add("bread", 1)
assert d.subtotal() == 1850 and d.total() == 2349
d.add("bread", 1)
assert d.total() == 2100
f = Cart()
f.add("cheese")
f.add("bread", 4)
f.add("apple", 2)
assert f.subtotal() == 2000 and f.total() == 2000
e = Cart()
e.add("milk", 10)
assert e.subtotal() == 1791 and e.total() == 2290
''',
    muts=[
        ("boundary: bulk 5", "if qty >= 5:", "if qty > 5:"),
        ("boundary: bulk 10", "if qty >= 10:", "if qty > 10:"),
        ("logic: wrong bulk percent", "return line * 5 // 100", "return line * 10 // 100"),
        ("rounding: bulk discount rounds up", "return line * 5 // 100", "return -(-line * 5 // 100)"),
        ("logic: coupon can exceed subtotal", "return min(500, subtotal)", "return 500"),
        ("boundary: free shipping threshold", "sub >= 2000", "sub > 2000", ) if False else ("boundary: free shipping threshold", "cart.py", "sub >= 2000", "sub > 2000"),
        ("logic: shipping charged on empty cart", "cart.py", "if not self._lines or sub >= 2000:", "if sub >= 2000:"),
        ("logic: bulk discount ignored in subtotal", "cart.py", "qty * p - bulk_discount(qty, p)", "qty * p"),
        ("logic: add replaces quantity", "cart.py", "self._lines.get(name, 0) + qty", "qty"),
    ][:8],
    weak=12,
))

TASKS.append(dict(
    id="qa_mf_calculator", diff="hard",
    spec="Write tests for the expression calculator package (`lexer.py`, `evaluator.py`). Test `evaluate(text)` and `tokenize(text)`.",
    files={"lexer.py": r'''
def tokenize(text):
    """Tokens for arithmetic: numbers (ints or decimals like 3.14, as float or int), the operators + - * / ^ and
    parentheses. Whitespace is skipped. Any other character -> ValueError. A number like '1.2.3' -> ValueError."""
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
        elif c.isdigit() or c == ".":
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == "."):
                j += 1
            raw = text[i:j]
            if raw.count(".") > 1 or raw == ".":
                raise ValueError("bad number")
            tokens.append(float(raw) if "." in raw else int(raw))
            i = j
        elif c in "+-*/^()":
            tokens.append(c)
            i += 1
        else:
            raise ValueError("unexpected %r" % c)
    return tokens
''', "evaluator.py": r'''
from lexer import tokenize


def evaluate(text):
    """Evaluate an arithmetic expression. Precedence: ^ (right-associative) > unary minus > * / > + -; the rest is
    left-associative. Division by zero -> ZeroDivisionError. Syntax errors -> ValueError. '/' always gives a float
    result only when needed: 6/3 == 2.0 (float). Note: unary minus binds looser than ^, so -2^2 == -4."""
    toks = tokenize(text)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        t = peek()
        pos[0] += 1
        return t

    def expr():
        v = term()
        while peek() in ("+", "-"):
            op = take()
            r = term()
            v = v + r if op == "+" else v - r
        return v

    def term():
        v = unary()
        while peek() in ("*", "/"):
            op = take()
            r = unary()
            v = v * r if op == "*" else v / r
        return v

    def unary():
        if peek() == "-":
            take()
            return -unary()
        return power()

    def power():
        base = atom()
        if peek() == "^":
            take()
            return base ** unary()
        return base

    def atom():
        t = take()
        if t == "(":
            v = expr()
            if take() != ")":
                raise ValueError("missing )")
            return v
        if isinstance(t, (int, float)):
            return t
        raise ValueError("unexpected token")

    v = expr()
    if peek() is not None:
        raise ValueError("trailing tokens")
    return v
'''},
    tests=r'''
from lexer import tokenize
from evaluator import evaluate

assert tokenize("") == []
assert tokenize("1\t+\n2") == [1, "+", 2]
assert tokenize("1+2") == [1, "+", 2]
assert tokenize(" 12 * (3.5-1) ") == [12, "*", "(", 3.5, "-", 1, ")"]
assert tokenize("2^3") == [2, "^", 3]
assert tokenize(".5") == [0.5]
assert isinstance(tokenize("7")[0], int) and isinstance(tokenize("7.0")[0], float)
for bad in ("1.2.3", "2 $ 3", "a", "."):
    try:
        tokenize(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)

assert evaluate("1+2") == 3
assert evaluate("2+3*4") == 14
assert evaluate("(2+3)*4") == 20
assert evaluate("10-3-2") == 5
assert evaluate("2*3/4") == 1.5
assert evaluate("8/4/2") == 1.0
assert evaluate("6/3") == 2.0
assert evaluate("2^3^2") == 512
assert evaluate("2^3*2") == 16
assert evaluate("-3") == -3
assert evaluate("-2^2") == -4
assert evaluate("2*-3") == -6
assert evaluate("--3") == 3
assert evaluate("3-(-2)") == 5
assert evaluate("((1))") == 1
assert evaluate("1.5+1.5") == 3.0
assert evaluate("2^-1") == 0.5
assert evaluate("100/10-5*2+1") == 1.0
assert evaluate(" 4 ") == 4
for expr in ("1/0", "5/(2-2)"):
    try:
        evaluate(expr)
    except ZeroDivisionError:
        pass
    else:
        raise AssertionError("expected ZeroDivisionError")
for expr in ("", "1+", "(1", "1)", "1 2", "*3", "()", "2^", "1+*2"):
    try:
        evaluate(expr)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % expr)
''',
    muts=[
        ("logic: subtraction right-associative", "evaluator.py", "v = v + r if op == \"+\" else v - r", "v = v + r if op == \"+\" else r - v"),
        ("logic: division swapped", "evaluator.py", 'v = v * r if op == "*" else v / r', 'v = v * r if op == "*" else r / v'),
        ("logic: power left-associative", "evaluator.py", "return base ** unary()", "return base ** atom()"),
        ("logic: unary binds tighter than power", "evaluator.py", "        return power()\n\n    def power", "        return atom() ** unary() if False else power()\n\n    def power") if False else ("logic: unary minus dropped", "evaluator.py", "            return -unary()", "            return unary()"),
        ("missing-edge-case: trailing tokens", "evaluator.py", '    if peek() is not None:\n        raise ValueError("trailing tokens")\n', ""),
        ("missing-edge-case: missing close paren", "evaluator.py", 'if take() != ")":\n                raise ValueError("missing )")', "take()"),
        ("missing-edge-case: caret operator", "lexer.py", 'c in "+-*/^()"', 'c in "+-*/()"'),
        ("logic: whitespace not skipped", "lexer.py", "        if c.isspace():\n            i += 1\n        elif c.isdigit()", "        if c == ' ':\n            i += 1\n        elif c.isdigit()"),
        ("logic: decimal parsed as int", "lexer.py", 'float(raw) if "." in raw else int(raw)', "float(raw)"),
    ][:8],
    weak=10,
))

TASKS.append(dict(
    id="qa_mf_rbac", diff="medium",
    spec="Write tests for the access-control package (`roles.py`, `policy.py`). Test `Policy.can(user, action, resource)`.",
    files={"roles.py": r'''
HIERARCHY = {"viewer": [], "editor": ["viewer"], "admin": ["editor"]}
PERMISSIONS = {"viewer": {"read"}, "editor": {"write"}, "admin": {"delete", "grant"}}


def effective_permissions(role):
    """Permissions of a role including everything inherited from the roles below it. Unknown role -> KeyError."""
    perms = set(PERMISSIONS[role])
    for parent in HIERARCHY[role]:
        perms |= effective_permissions(parent)
    return perms
''', "policy.py": r'''
from roles import effective_permissions


class Policy:
    """Users have one role. A user may act on a resource when their role's effective permissions include the action
    AND the resource is not in the user's denied set. Owners of a resource may always 'read' and 'write' it
    (but not delete/grant) regardless of role, unless it is denied. Unknown users -> False for everything.
    assign(user, role) sets the role (unknown role -> KeyError). deny(user, resource) blocks a resource.
    owns(user, resource) registers ownership. Denials win over everything."""

    def __init__(self):
        self._roles = {}
        self._denied = {}
        self._owners = {}

    def assign(self, user, role):
        effective_permissions(role)
        self._roles[user] = role

    def deny(self, user, resource):
        self._denied.setdefault(user, set()).add(resource)

    def owns(self, user, resource):
        self._owners.setdefault(resource, set()).add(user)

    def can(self, user, action, resource):
        if resource in self._denied.get(user, ()):
            return False
        if user in self._owners.get(resource, ()) and action in ("read", "write"):
            return True
        role = self._roles.get(user)
        if role is None:
            return False
        return action in effective_permissions(role)
'''},
    tests=r'''
from roles import effective_permissions
from policy import Policy

assert effective_permissions("viewer") == {"read"}
assert effective_permissions("editor") == {"read", "write"}
assert effective_permissions("admin") == {"read", "write", "delete", "grant"}
try:
    effective_permissions("root")
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")

p = Policy()
p.assign("v", "viewer")
p.assign("e", "editor")
p.assign("a", "admin")
assert p.can("v", "read", "doc") and not p.can("v", "write", "doc") and not p.can("v", "delete", "doc")
assert p.can("e", "read", "doc") and p.can("e", "write", "doc") and not p.can("e", "delete", "doc")
assert not p.can("e", "grant", "doc")
assert all(p.can("a", act, "doc") for act in ("read", "write", "delete", "grant"))
assert not p.can("a", "fly", "doc")
assert not p.can("nobody", "read", "doc")
p.deny("a", "secret")
assert not p.can("a", "read", "secret") and p.can("a", "read", "doc")
assert p.can("e", "read", "secret")
p.owns("v", "mine")
assert p.can("v", "read", "mine") and p.can("v", "write", "mine")
assert not p.can("v", "delete", "mine") and not p.can("v", "grant", "mine")
assert not p.can("v", "write", "other")
assert not p.can("e", "delete", "mine")
p.owns("nobody", "thing")
assert p.can("nobody", "write", "thing")
assert not p.can("nobody", "write", "other")
p.deny("v", "mine")
assert not p.can("v", "read", "mine")
p.assign("v", "editor")
assert p.can("v", "write", "doc")
try:
    p.assign("x", "root")
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
assert not p.can("x", "read", "doc")
''',
    muts=[
        ("logic: no inheritance", "roles.py", "        perms |= effective_permissions(parent)\n", "        pass\n"),
        ("logic: editor missing write", "roles.py", '"editor": {"write"}', '"editor": set()'),
        ("logic: denial ignored", "policy.py", "        if resource in self._denied.get(user, ()):\n            return False\n", ""),
        ("logic: owner can delete", "policy.py", 'action in ("read", "write"):\n            return True', 'True:\n            return True'),
        ("logic: owner cannot write", "policy.py", 'action in ("read", "write")', 'action == "read"'),
        ("ordering: ownership checked before denial", "policy.py", "        if resource in self._denied.get(user, ()):\n            return False\n        if user in self._owners.get(resource, ()) and action in (\"read\", \"write\"):\n            return True\n", "        if user in self._owners.get(resource, ()) and action in (\"read\", \"write\"):\n            return True\n        if resource in self._denied.get(user, ()):\n            return False\n"),
        ("missing-edge-case: unknown role assignable", "policy.py", "        effective_permissions(role)\n", ""),
        ("logic: denial is global", "policy.py", "self._denied.get(user, ())", "[r for d in self._denied.values() for r in d]"),
    ],
    weak=14,
))

TASKS.append(dict(
    id="qa_mf_deps", diff="hard",
    spec="Write tests for the dependency-ordering package (`graph.py`, `planner.py`). Test `build_order(deps)` and `Graph`.",
    files={"graph.py": r'''
class Graph:
    """Directed graph on hashable nodes. add_edge(a, b) means 'a depends on b'. nodes() is sorted. deps(a) returns
    the sorted direct dependencies of a (empty for a node without any). Self-dependency -> ValueError."""

    def __init__(self):
        self._edges = {}

    def add_node(self, a):
        self._edges.setdefault(a, set())

    def add_edge(self, a, b):
        if a == b:
            raise ValueError("self dependency")
        self._edges.setdefault(a, set()).add(b)
        self._edges.setdefault(b, set())

    def nodes(self):
        return sorted(self._edges)

    def deps(self, a):
        return sorted(self._edges.get(a, ()))
''', "planner.py": r'''
from graph import Graph


class CycleError(Exception):
    pass


def build_order(deps):
    """deps: dict node -> list of nodes it depends on. Returns a list where every node comes after all its
    dependencies; among independent nodes the alphabetically smallest is emitted first (deterministic).
    Nodes only mentioned as dependencies are included. A cycle -> CycleError."""
    g = Graph()
    for node, ds in deps.items():
        g.add_node(node)
        for d in ds:
            g.add_edge(node, d)
    remaining = {n: set(g.deps(n)) for n in g.nodes()}
    order = []
    while remaining:
        ready = sorted(n for n, ds in remaining.items() if not ds)
        if not ready:
            raise CycleError("cycle among %s" % sorted(remaining))
        n = ready[0]
        order.append(n)
        del remaining[n]
        for ds in remaining.values():
            ds.discard(n)
    return order
'''},
    tests=r'''
from graph import Graph
from planner import build_order, CycleError

g = Graph()
assert g.nodes() == []
g.add_edge("b", "a")
g.add_edge("b", "c")
g.add_edge("b", "a")
g.add_node("z")
assert g.nodes() == ["a", "b", "c", "z"]
assert g.deps("b") == ["a", "c"]
assert g.deps("a") == [] and g.deps("unknown") == []
try:
    g.add_edge("x", "x")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")

assert build_order({}) == []
assert build_order({"a": []}) == ["a"]
assert build_order({"b": ["a"]}) == ["a", "b"]
assert build_order({"c": ["b"], "b": ["a"], "a": []}) == ["a", "b", "c"]
assert build_order({"app": ["lib", "util"], "lib": ["core"], "util": ["core"]}) == ["core", "lib", "util", "app"]
assert build_order({"z": [], "y": [], "x": []}) == ["x", "y", "z"]
assert build_order({"d": ["b", "c"], "b": ["a"], "c": ["a"]}) == ["a", "b", "c", "d"]
assert build_order({"b": ["a"], "c": []}) == ["a", "b", "c"]
assert build_order({"m": ["a", "a"]}) == ["a", "m"]
order = build_order({"x": ["y", "z"], "y": ["z"], "w": ["x"]})
assert order == ["z", "y", "x", "w"]
for bad in ({"a": ["b"], "b": ["a"]}, {"a": ["b"], "b": ["c"], "c": ["a"]}, {"ok": [], "a": ["b"], "b": ["a"]}):
    try:
        build_order(bad)
    except CycleError:
        pass
    else:
        raise AssertionError("expected CycleError for %r" % bad)
try:
    build_order({"a": ["a"]})
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("ordering: largest ready node first", "planner.py", "n = ready[0]", "n = ready[-1]"),
        ("logic: dependencies not removed", "planner.py", "            ds.discard(n)\n", "            pass\n"),
        ("missing-edge-case: cycle silently ends", "planner.py", '            raise CycleError("cycle among %s" % sorted(remaining))', "            break"),
        ("missing-edge-case: self dependency", "graph.py", 'if a == b:\n            raise ValueError("self dependency")', "if False:\n            pass"),
        ("missing-edge-case: dependency-only nodes", "graph.py", "        self._edges.setdefault(b, set())\n", ""),
        ("ordering: nodes unsorted", "graph.py", "return sorted(self._edges)", "return list(self._edges)[::-1]"),
        ("ordering: deps unsorted", "graph.py", "return sorted(self._edges.get(a, ()))", "return sorted(self._edges.get(a, ()), reverse=True)"),
        ("logic: edge direction reversed", "planner.py", "g.add_edge(node, d)", "g.add_edge(d, node)"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_mf_library", diff="hard",
    spec="Write tests for the library-loans package (`books.py`, `loans.py`). Dates are `datetime.date` values passed in explicitly.",
    files={"books.py": r'''
class Catalog:
    """Books with a number of copies. add(isbn, copies=1) adds copies (copies >= 1, else ValueError; repeated adds
    accumulate). total(isbn) -> copies owned (KeyError if unknown)."""

    def __init__(self):
        self._copies = {}

    def add(self, isbn, copies=1):
        if copies < 1:
            raise ValueError("copies must be >= 1")
        self._copies[isbn] = self._copies.get(isbn, 0) + copies

    def total(self, isbn):
        return self._copies[isbn]
''', "loans.py": r'''
from datetime import timedelta

LOAN_DAYS = 14
FINE_PER_DAY = 25
MAX_FINE = 1000


class Library:
    """checkout(member, isbn, today) lends a copy if one is free (LookupError('none available') otherwise; unknown
    isbn -> KeyError); a member may hold at most 3 books at once (RuntimeError) and may not hold two copies of the
    same isbn (ValueError). Due date = today + 14 days. checkin(member, isbn, today) returns the fine in cents: 25
    cents per day late, capped at 1000; 0 if on time (the due day itself is on time). Returning a book the member
    does not hold -> KeyError. available(isbn) = copies not currently lent. due_date(member, isbn)."""

    def __init__(self, catalog):
        self.catalog = catalog
        self._loans = {}

    def available(self, isbn):
        lent = sum(1 for (m, i) in self._loans if i == isbn)
        return self.catalog.total(isbn) - lent

    def checkout(self, member, isbn, today):
        if self.available(isbn) < 1:
            raise LookupError("none available")
        if (member, isbn) in self._loans:
            raise ValueError("already has this book")
        if sum(1 for (m, i) in self._loans if m == member) >= 3:
            raise RuntimeError("limit reached")
        self._loans[(member, isbn)] = today + timedelta(days=LOAN_DAYS)

    def due_date(self, member, isbn):
        return self._loans[(member, isbn)]

    def checkin(self, member, isbn, today):
        due = self._loans.pop((member, isbn))
        late = (today - due).days
        return min(MAX_FINE, late * FINE_PER_DAY) if late > 0 else 0
'''},
    tests=r'''
from datetime import date, timedelta
from books import Catalog
from loans import Library

c = Catalog()
c.add("b1")
c.add("b2", 2)
c.add("b2", 3)
assert c.total("b1") == 1 and c.total("b2") == 5
for n in (0, -1):
    try:
        c.add("b3", n)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
try:
    c.total("b3")
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")

c.add("b3")
c.add("b4")
lib = Library(c)
d0 = date(2024, 1, 1)
assert lib.available("b1") == 1
lib.checkout("ann", "b1", d0)
assert lib.available("b1") == 0
assert lib.due_date("ann", "b1") == date(2024, 1, 15)
try:
    lib.checkout("bob", "b1", d0)
except LookupError:
    pass
else:
    raise AssertionError("expected LookupError")
try:
    lib.checkout("ann", "b2", d0) or lib.checkout("ann", "b2", d0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
lib.checkout("ann", "b3", d0)
try:
    lib.checkout("ann", "b4", d0)
except RuntimeError:
    pass
else:
    raise AssertionError("expected RuntimeError")
assert lib.available("b4") == 1
try:
    lib.checkout("bob", "nope", d0)
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
assert lib.checkin("ann", "b1", date(2024, 1, 14)) == 0
assert lib.available("b1") == 1
lib.checkout("ann", "b4", d0)
assert lib.checkin("ann", "b4", date(2024, 1, 15)) == 0
lib.checkout("ann", "b4", d0)
assert lib.checkin("ann", "b4", date(2024, 1, 16)) == 25
assert lib.checkin("ann", "b2", date(2024, 1, 15) + timedelta(days=4)) == 100
lib.checkout("bob", "b1", d0)
assert lib.checkin("bob", "b1", date(2024, 1, 15) + timedelta(days=40)) == 1000
lib.checkout("bob", "b1", d0)
assert lib.checkin("bob", "b1", date(2024, 1, 15) + timedelta(days=39)) == 975
lib.checkout("bob", "b1", d0)
assert lib.checkin("bob", "b1", date(2024, 1, 15) + timedelta(days=41)) == 1000
try:
    lib.checkin("bob", "b1", d0)
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
lib.checkout("cy", "b4", date(2024, 3, 1))
assert lib.due_date("cy", "b4") == date(2024, 3, 15)
lib.checkout("dee", "b2", date(2024, 12, 25))
assert lib.due_date("dee", "b2") == date(2025, 1, 8)
''',
    muts=[
        ("boundary: due day counted as a late day", "loans.py", "late = (today - due).days", "late = (today - due).days + 1"),
        ("boundary: loan limit", "loans.py", "for (m, i) in self._loans if m == member) >= 3", "for (m, i) in self._loans if m == member) >= 4"),
        ("boundary: loan limit too strict", "loans.py", "for (m, i) in self._loans if m == member) >= 3", "for (m, i) in self._loans if m == member) >= 2"),
        ("logic: fine cap missing", "loans.py", "min(MAX_FINE, late * FINE_PER_DAY)", "late * FINE_PER_DAY"),
        ("logic: loan period", "loans.py", "LOAN_DAYS = 14", "LOAN_DAYS = 7"),
        ("missing-edge-case: duplicate copy", "loans.py", '        if (member, isbn) in self._loans:\n            raise ValueError("already has this book")\n', ""),
        ("logic: availability counts per member", "loans.py", "lent = sum(1 for (m, i) in self._loans if i == isbn)", "lent = sum(1 for (m, i) in self._loans if i == isbn and m == 'x')"),
        ("boundary: add 0 copies accepted", "books.py", "if copies < 1:", "if copies < 0:"),
    ],
    weak=14,
))

TASKS.append(dict(
    id="qa_mf_undo_editor", diff="hard",
    spec="Write tests for the text-editor package (`history.py`, `editor.py`). Test `Editor` with undo/redo.",
    files={"history.py": r'''
class History:
    """Undo/redo stack of snapshots. push(state) records a new state (clears the redo stack). undo() / redo()
    return the state to move to or None if there is nothing to undo/redo. `current` is the present state.
    At most `limit` undo steps are kept (oldest forgotten); limit >= 1 else ValueError."""

    def __init__(self, initial, limit=100):
        if limit < 1:
            raise ValueError("limit must be >= 1")
        self.limit = limit
        self.current = initial
        self._undo = []
        self._redo = []

    def push(self, state):
        self._undo.append(self.current)
        if len(self._undo) > self.limit:
            self._undo.pop(0)
        self._redo.clear()
        self.current = state

    def undo(self):
        if not self._undo:
            return None
        self._redo.append(self.current)
        self.current = self._undo.pop()
        return self.current

    def redo(self):
        if not self._redo:
            return None
        self._undo.append(self.current)
        self.current = self._redo.pop()
        return self.current
''', "editor.py": r'''
from history import History


class Editor:
    """Text buffer with undo/redo. insert(pos, text): 0 <= pos <= len else IndexError; delete(start, end): removes
    text[start:end], needs 0 <= start <= end <= len else IndexError; replace_all(old, new) replaces every
    occurrence (old must be non-empty else ValueError) and does NOT record an undo step if nothing changed.
    text property; undo()/redo() return True when something happened."""

    def __init__(self, text="", limit=100):
        self._h = History(text, limit)

    @property
    def text(self):
        return self._h.current

    def insert(self, pos, s):
        t = self.text
        if not 0 <= pos <= len(t):
            raise IndexError(pos)
        self._h.push(t[:pos] + s + t[pos:])

    def delete(self, start, end):
        t = self.text
        if not 0 <= start <= end <= len(t):
            raise IndexError((start, end))
        self._h.push(t[:start] + t[end:])

    def replace_all(self, old, new):
        if not old:
            raise ValueError("old must be non-empty")
        t = self.text
        r = t.replace(old, new)
        if r != t:
            self._h.push(r)

    def undo(self):
        return self._h.undo() is not None

    def redo(self):
        return self._h.redo() is not None
'''},
    tests=r'''
from history import History
from editor import Editor

h = History("a", limit=2)
assert h.current == "a" and h.undo() is None and h.redo() is None
h.push("b")
h.push("c")
assert h.current == "c"
assert h.undo() == "b" and h.current == "b"
assert h.redo() == "c"
assert h.redo() is None
h.undo()
h.push("d")
assert h.redo() is None
assert h.undo() == "b"
assert h.undo() == "a"
assert h.undo() is None
h2 = History(0, limit=2)
for i in (1, 2, 3):
    h2.push(i)
assert h2.undo() == 2 and h2.undo() == 1 and h2.undo() is None
h3 = History(0, limit=1)
h3.push(1)
h3.push(2)
assert h3.undo() == 1 and h3.undo() is None
try:
    History(0, limit=0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
h4 = History(None)
h4.push(None)
assert h4.undo() is None and h4.current is None

e = Editor("hello")
e.insert(5, " world")
assert e.text == "hello world"
e.insert(0, ">> ")
assert e.text == ">> hello world"
e.delete(0, 3)
assert e.text == "hello world"
e.delete(5, 11)
assert e.text == "hello"
e.delete(2, 2)
assert e.text == "hello"
for fn, args in ((e.insert, (-1, "x")), (e.insert, (6, "x")), (e.delete, (3, 2)), (e.delete, (-1, 2)), (e.delete, (0, 6))):
    try:
        fn(*args)
    except IndexError:
        pass
    else:
        raise AssertionError("expected IndexError for %r" % (args,))
assert e.text == "hello"
assert e.undo() is True and e.text == "hello"
assert e.undo() is True and e.text == "hello world"
assert e.undo() is True and e.text == ">> hello world"
assert e.redo() is True and e.text == "hello world"
e2 = Editor("a-b-c")
e2.replace_all("-", "+")
assert e2.text == "a+b+c"
e2.replace_all("zzz", "y")
assert e2.text == "a+b+c"
assert e2.undo() is True and e2.text == "a-b-c"
assert e2.undo() is False
assert e2.redo() is True and e2.text == "a+b+c"
assert e2.redo() is False
try:
    e2.replace_all("", "x")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
e3 = Editor("x", limit=1)
e3.insert(1, "y")
e3.insert(2, "z")
assert e3.undo() is True and e3.text == "xy"
assert e3.undo() is False
''',
    muts=[
        ("missing-edge-case: redo not cleared on push", "history.py", "        self._redo.clear()\n", ""),
        ("off-by-one: undo limit", "history.py", "if len(self._undo) > self.limit:", "if len(self._undo) >= self.limit:"),
        ("logic: undo does not save redo", "history.py", "        self._redo.append(self.current)\n        self.current = self._undo.pop()", "        self.current = self._undo.pop()"),
        ("logic: redo does not save undo", "history.py", "        self._undo.append(self.current)\n        self.current = self._redo.pop()", "        self.current = self._redo.pop()"),
        ("boundary: insert at end rejected", "editor.py", "not 0 <= pos <= len(t)", "not 0 <= pos < len(t)"),
        ("boundary: delete to end rejected", "editor.py", "not 0 <= start <= end <= len(t)", "not 0 <= start <= end < len(t)"),
        ("logic: replace_all without change records a step", "editor.py", "        if r != t:\n            self._h.push(r)", "        self._h.push(r)"),
        ("logic: replace only first", "editor.py", "t.replace(old, new)", "t.replace(old, new, 1)"),
    ],
    weak=22,
))

TASKS.append(dict(
    id="qa_mf_rules", diff="hard",
    spec="Write tests for the rule-engine package (`conditions.py`, `engine.py`). Test `Engine.decide(record)`.",
    files={"conditions.py": r'''
OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a > b,
    "ge": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "le": lambda a, b: a <= b,
    "in": lambda a, b: a in b,
}


def check(cond, record):
    """cond = (field, op, value). A record missing the field never matches (False) -- except op 'ne', which is True
    for a missing field. Unknown op -> ValueError. Comparing incomparable types (TypeError) -> False."""
    field, op, value = cond
    if op not in OPS:
        raise ValueError("unknown op %r" % op)
    if field not in record:
        return op == "ne"
    try:
        return bool(OPS[op](record[field], value))
    except TypeError:
        return False
''', "engine.py": r'''
from conditions import check


class Engine:
    """Ordered rules: add_rule(name, conditions, outcome, priority=0). decide(record) evaluates the rules whose
    conditions ALL match (an empty condition list always matches); the winner is the matching rule with the highest
    priority, ties go to the rule added first. Returns (name, outcome), or (None, default) when no rule matches."""

    def __init__(self, default=None):
        self.default = default
        self._rules = []

    def add_rule(self, name, conditions, outcome, priority=0):
        self._rules.append((priority, len(self._rules), name, conditions, outcome))

    def decide(self, record):
        best = None
        for priority, order, name, conds, outcome in self._rules:
            if all(check(c, record) for c in conds):
                if best is None or priority > best[0]:
                    best = (priority, order, name, outcome)
        if best is None:
            return None, self.default
        return best[2], best[3]
'''},
    tests=r'''
from conditions import check
from engine import Engine

r = {"age": 30, "country": "US", "tags": ["a"]}
assert check(("age", "eq", 30), r) and not check(("age", "eq", 31), r)
assert check(("age", "ne", 31), r) and not check(("age", "ne", 30), r)
assert check(("age", "gt", 29), r) and not check(("age", "gt", 30), r)
assert check(("age", "ge", 30), r) and not check(("age", "ge", 31), r)
assert check(("age", "lt", 31), r) and not check(("age", "lt", 30), r)
assert check(("age", "le", 30), r) and not check(("age", "le", 29), r)
assert check(("country", "in", ["US", "CA"]), r) and not check(("country", "in", ["FR"]), r)
assert check(("missing", "eq", None), r) is False
assert check(("missing", "gt", 1), r) is False
assert check(("missing", "in", [1]), r) is False
assert check(("missing", "ne", 5), r) is True
assert check(("country", "gt", 5), r) is False
assert check(("age", "lt", "x"), r) is False
try:
    check(("age", "like", 1), r)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
try:
    check(("missing", "like", 1), r)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")

e = Engine(default="review")
assert e.decide({}) == (None, "review")
e.add_rule("minor", [("age", "lt", 18)], "deny")
e.add_rule("us_adult", [("age", "ge", 18), ("country", "eq", "US")], "allow")
e.add_rule("any_adult", [("age", "ge", 18)], "manual", priority=-1)
assert e.decide({"age": 10, "country": "US"}) == ("minor", "deny")
assert e.decide({"age": 30, "country": "US"}) == ("us_adult", "allow")
assert e.decide({"age": 30, "country": "FR"}) == ("any_adult", "manual")
assert e.decide({"country": "US"}) == (None, "review")
assert e.decide({"age": 18, "country": "US"}) == ("us_adult", "allow")
e.add_rule("vip", [("vip", "eq", True)], "allow+", priority=5)
assert e.decide({"age": 30, "country": "US", "vip": True}) == ("vip", "allow+")
assert e.decide({"age": 10, "vip": True}) == ("vip", "allow+")
e.add_rule("always", [], "fallback", priority=-10)
assert e.decide({}) == ("always", "fallback")
assert e.decide({"age": 30, "country": "FR"}) == ("any_adult", "manual")
t = Engine()
t.add_rule("first", [], 1)
t.add_rule("second", [], 2)
assert t.decide({}) == ("first", 1)
t.add_rule("third", [], 3, priority=1)
assert t.decide({}) == ("third", 3)
t.add_rule("fourth", [], 4, priority=1)
assert t.decide({}) == ("third", 3)
assert Engine().decide({"x": 1}) == (None, None)
''',
    muts=[
        ("boundary: ge as gt", "conditions.py", '"ge": lambda a, b: a >= b,', '"ge": lambda a, b: a > b,'),
        ("boundary: le as lt", "conditions.py", '"le": lambda a, b: a <= b,', '"le": lambda a, b: a < b,'),
        ("logic: missing field with ne", "conditions.py", 'return op == "ne"', "return False"),
        ("missing-edge-case: type errors propagate", "conditions.py", "    except TypeError:\n        return False", "    except ZeroDivisionError:\n        return False"),
        ("logic: any instead of all", "engine.py", "if all(check(c, record) for c in conds):", "if any(check(c, record) for c in conds) or not conds:"),
        ("comparison: ties go to last rule", "engine.py", "priority > best[0]", "priority >= best[0]"),
        ("ordering: lowest priority wins", "engine.py", "priority > best[0]", "priority < best[0]"),
        ("wrong-default: default ignored", "engine.py", "return None, self.default", "return None, None"),
    ],
    weak=17,
))

TASKS.append(dict(
    id="qa_mf_text_stats", diff="medium",
    spec="Write tests for the text-statistics package (`normalize.py`, `stats.py`). Test `word_counts`, `top_n` and `reading_time`.",
    files={"normalize.py": r'''
import re


def words(text):
    """Lower-cased words: runs of letters, digits and apostrophes ('don't' stays one word); apostrophes at the
    start or end of a word are stripped; pure-apostrophe runs are dropped."""
    out = []
    for w in re.findall(r"[A-Za-z0-9']+", text):
        w = w.strip("'").lower()
        if w:
            out.append(w)
    return out
''', "stats.py": r'''
from normalize import words


def word_counts(text, stopwords=()):
    """Dict word -> count, skipping stopwords (compared lower-case)."""
    stop = {s.lower() for s in stopwords}
    counts = {}
    for w in words(text):
        if w not in stop:
            counts[w] = counts.get(w, 0) + 1
    return counts


def top_n(text, n, stopwords=()):
    """The n most frequent (word, count) pairs, ordered by count descending then word ascending.
    n < 0 -> ValueError; n == 0 -> []."""
    if n < 0:
        raise ValueError("n must be >= 0")
    items = sorted(word_counts(text, stopwords).items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:n]


def reading_time(text, wpm=200):
    """Minutes to read, rounded UP to a whole minute, at least 1 for any non-empty text, 0 for no words.
    wpm <= 0 -> ValueError."""
    if wpm <= 0:
        raise ValueError("wpm must be positive")
    n = len(words(text))
    if n == 0:
        return 0
    return max(1, -(-n // wpm))
'''},
    tests=r'''
from normalize import words
from stats import word_counts, top_n, reading_time

assert words("") == []
assert words("Hello, World!") == ["hello", "world"]
assert words("don't stop") == ["don't", "stop"]
assert words("'quoted' words") == ["quoted", "words"]
assert words("rock 'n' roll") == ["rock", "n", "roll"]
assert words("a1 b2") == ["a1", "b2"]
assert words("'' ' ''") == []
assert words("x--y") == ["x", "y"]
assert words("MiXeD") == ["mixed"]
assert word_counts("a b a") == {"a": 2, "b": 1}
assert word_counts("The the THE cat", stopwords=["the"]) == {"cat": 1}
assert word_counts("The cat", stopwords=["THE"]) == {"cat": 1}
assert word_counts("") == {}
assert top_n("a b b c c c", 2) == [("c", 3), ("b", 2)]
assert top_n("b a", 5) == [("a", 1), ("b", 1)]
assert top_n("b a c", 2) == [("a", 1), ("b", 1)]
assert top_n("a a", 0) == []
assert top_n("the a a", 1, stopwords=["a"]) == [("the", 1)]
assert top_n("", 3) == []
try:
    top_n("a", -1)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert reading_time("") == 0
assert reading_time("!!!") == 0
assert reading_time("word") == 1
assert reading_time("w " * 200) == 1
assert reading_time("w " * 201) == 2
assert reading_time("w " * 400) == 2
assert reading_time("w " * 401) == 3
assert reading_time("w " * 100, wpm=50) == 2
assert reading_time("w " * 101, wpm=50) == 3
try:
    reading_time("a", wpm=0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("missing-edge-case: apostrophes at edges", "normalize.py", 'w = w.strip("\'").lower()', "w = w.lower()"),
        ("missing-edge-case: apostrophe-only runs", "normalize.py", "        if w:\n            out.append(w)", "        out.append(w)"),
        ("logic: contractions split", "normalize.py", "[A-Za-z0-9']+", "[A-Za-z0-9]+"),
        ("logic: digits dropped", "normalize.py", "[A-Za-z0-9']+", "[A-Za-z']+"),
        ("logic: stopwords case-sensitive", "stats.py", "stop = {s.lower() for s in stopwords}", "stop = set(stopwords)"),
        ("ordering: ties unsorted", "stats.py", "key=lambda kv: (-kv[1], kv[0])", "key=lambda kv: -kv[1]"),
        ("rounding: reading time truncated", "stats.py", "max(1, -(-n // wpm))", "max(1, n // wpm)"),
        ("boundary: n=0 mishandled", "stats.py", "if n < 0:", "if n < 1:"),
    ],
    weak=10,
))
