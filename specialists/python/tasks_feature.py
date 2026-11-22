"""Extend-existing-code tasks: working code that must gain behaviour without breaking what it already does."""
from common import feat

TASKS_FEATURE = [
    feat("py_feat_stack_iter", "easy", "data-structures",
         {"stack.py": r'''
class Stack:
    def __init__(self):
        self._items = []

    def push(self, x):
        self._items.append(x)

    def pop(self):
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def __len__(self):
        return len(self._items)
'''},
         "Add to Stack: `peek()` (top item, IndexError if empty), `__iter__` (iterates from the top down, without removing anything), `__bool__` "
         "(True when non-empty) and `clear()`. Existing behaviour must stay.",
         "from stack import Stack\ns = Stack(); s.push(1); s.push(2)\nassert s.peek() == 2 and list(s) == [2, 1]\n",
         r'''
from stack import Stack
s = Stack()
assert not s and len(s) == 0
for x in (1, 2, 3):
    s.push(x)
assert s and s.peek() == 3 and list(s) == [3, 2, 1] and len(s) == 3
assert s.pop() == 3 and list(s) == [2, 1]
s.clear()
assert len(s) == 0 and not s and list(s) == []
for f in (s.peek, s.pop):
    try:
        f()
        assert False
    except IndexError:
        pass
''',
         append={"stack.py": '''
    def peek(self):
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def __iter__(self):
        return iter(reversed(self._items))

    def __bool__(self):
        return bool(self._items)

    def clear(self):
        self._items.clear()
'''}),
    feat("py_feat_counter_ops", "easy", "dicts",
         {"counter.py": r'''
class Counter:
    def __init__(self, items=()):
        self.counts = {}
        for x in items:
            self.add(x)

    def add(self, x, n=1):
        self.counts[x] = self.counts.get(x, 0) + n

    def count(self, x):
        return self.counts.get(x, 0)
'''},
         "Add to Counter: `total()` (sum of all counts), `most_common(n=None)` (list of (item, count) sorted by count descending, ties by first-added; at most n entries "
         "when n is given), `__add__(other)` returning a NEW Counter with counts summed, and `remove(x, n=1)` which lowers a count (never below zero; an item reaching "
         "zero is deleted from `counts`; removing an absent item raises KeyError).",
         "from counter import Counter\nc = Counter('aab')\nassert c.most_common(1) == [('a', 2)] and c.total() == 3\n",
         r'''
from counter import Counter
c = Counter("abracadabra")
assert c.total() == 11
assert c.most_common() == [("a", 5), ("b", 2), ("r", 2), ("c", 1), ("d", 1)]
assert c.most_common(2) == [("a", 5), ("b", 2)]
d = Counter("xxa")
e = c + d
assert e.count("a") == 6 and e.count("x") == 2 and c.count("x") == 0 and e.total() == 14
c.remove("a", 2)
assert c.count("a") == 3
c.remove("c")
assert "c" not in c.counts
c.remove("b", 10)
assert "b" not in c.counts
try:
    c.remove("zzz")
    assert False
except KeyError:
    pass
assert Counter().most_common() == [] and Counter().total() == 0
''',
         append={"counter.py": '''
    def total(self):
        return sum(self.counts.values())

    def most_common(self, n=None):
        items = sorted(self.counts.items(), key=lambda kv: -kv[1])
        return items if n is None else items[:n]

    def __add__(self, other):
        out = Counter()
        for src in (self, other):
            for k, v in src.counts.items():
                out.add(k, v)
        return out

    def remove(self, x, n=1):
        if x not in self.counts:
            raise KeyError(x)
        self.counts[x] -= n
        if self.counts[x] <= 0:
            del self.counts[x]
'''}),
    feat("py_feat_linked_list", "medium", "data-structures",
         {"llist.py": r'''
class Node:
    def __init__(self, value, next=None):
        self.value = value
        self.next = next


class LinkedList:
    def __init__(self):
        self.head = None
        self._size = 0

    def push_front(self, value):
        self.head = Node(value, self.head)
        self._size += 1

    def push_back(self, value):
        node = Node(value)
        if self.head is None:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node
        self._size += 1

    def __len__(self):
        return self._size

    def __iter__(self):
        cur = self.head
        while cur:
            yield cur.value
            cur = cur.next
'''},
         "Add to LinkedList: `remove(value)` (removes the first node with that value and returns True, else False), `insert_at(index, value)` (0..len inclusive; "
         "otherwise IndexError), `reverse()` (in place, by relinking nodes), `find(value)` (index of first match or -1). Keep `__len__` correct after every operation.",
         "from llist import LinkedList\nl = LinkedList(); l.push_back(1); l.push_back(2); l.reverse()\nassert list(l) == [2, 1]\n",
         r'''
from llist import LinkedList
l = LinkedList()
for x in (1, 2, 3, 2):
    l.push_back(x)
assert list(l) == [1, 2, 3, 2] and len(l) == 4
assert l.find(2) == 1 and l.find(3) == 2 and l.find(9) == -1
assert l.remove(2) is True and list(l) == [1, 3, 2] and len(l) == 3
assert l.remove(9) is False and len(l) == 3
assert l.remove(1) is True and list(l) == [3, 2]
l.insert_at(0, "a"); l.insert_at(3, "z"); l.insert_at(2, "m")
assert list(l) == ["a", 3, "m", 2, "z"] and len(l) == 5
for bad in (-1, 6):
    try:
        l.insert_at(bad, 0)
        assert False
    except IndexError:
        pass
l.reverse()
assert list(l) == ["z", 2, "m", 3, "a"]
l.push_back("end")
assert list(l)[-1] == "end"
e = LinkedList(); e.reverse()
assert list(e) == [] and e.remove(1) is False
e.insert_at(0, 5)
assert list(e) == [5] and len(e) == 1
''',
         append={"llist.py": '''
    def remove(self, value):
        prev, cur = None, self.head
        while cur:
            if cur.value == value:
                if prev:
                    prev.next = cur.next
                else:
                    self.head = cur.next
                self._size -= 1
                return True
            prev, cur = cur, cur.next
        return False

    def insert_at(self, index, value):
        if not 0 <= index <= self._size:
            raise IndexError(index)
        if index == 0:
            self.push_front(value)
            return
        prev = self.head
        for _ in range(index - 1):
            prev = prev.next
        prev.next = Node(value, prev.next)
        self._size += 1

    def reverse(self):
        prev, cur = None, self.head
        while cur:
            cur.next, prev, cur = prev, cur, cur.next
        self.head = prev

    def find(self, value):
        for i, v in enumerate(self):
            if v == value:
                return i
        return -1
'''}),
    feat("py_feat_bst_delete", "hard", "trees",
         {"bst.py": r'''
class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


class BST:
    def __init__(self):
        self.root = None
        self.size = 0

    def insert(self, key):
        """Insert key; duplicates are ignored. Returns True if the key was added."""
        if self.root is None:
            self.root = Node(key)
            self.size = 1
            return True
        cur = self.root
        while True:
            if key == cur.key:
                return False
            side = "left" if key < cur.key else "right"
            nxt = getattr(cur, side)
            if nxt is None:
                setattr(cur, side, Node(key))
                self.size += 1
                return True
            cur = nxt

    def __contains__(self, key):
        cur = self.root
        while cur:
            if key == cur.key:
                return True
            cur = cur.left if key < cur.key else cur.right
        return False

    def __len__(self):
        return self.size
'''},
         "Add to BST: `delete(key)` (standard BST deletion, replacing a two-child node by its in-order successor; returns True if removed else False; keep `size` correct), "
         "`inorder()` (sorted list of keys), `height()` (number of nodes on the longest root-to-leaf path, 0 when empty), `min()` and `max()` (ValueError when empty) "
         "and `successor(key)` (smallest key strictly greater than `key`, or None; `key` need not be in the tree). Use iteration where the tree can be deep: a tree "
         "built by inserting 2000 increasing numbers must still work for inorder, height and delete.",
         "from bst import BST\nt = BST()\nfor k in (2, 1, 3):\n    t.insert(k)\nassert t.delete(2) and t.inorder() == [1, 3]\n",
         r'''
from bst import BST
t = BST()
for k in (50, 30, 70, 20, 40, 60, 80, 35, 45):
    assert t.insert(k)
assert not t.insert(40)
assert t.inorder() == [20, 30, 35, 40, 45, 50, 60, 70, 80] and len(t) == 9
assert t.height() == 4 and t.min() == 20 and t.max() == 80
assert t.successor(50) == 60 and t.successor(45) == 50 and t.successor(80) is None and t.successor(55) == 60 and t.successor(0) == 20
assert t.delete(20) and t.inorder()[0] == 30 and len(t) == 8
assert t.delete(30) and 30 not in t and 35 in t and 40 in t
assert t.delete(50) and 50 not in t and t.root.key == 60
assert not t.delete(999) and len(t) == 6
assert t.inorder() == [35, 40, 45, 60, 70, 80]
for k in (35, 40, 45, 60, 70, 80):
    assert t.delete(k)
assert len(t) == 0 and t.inorder() == [] and t.height() == 0 and t.root is None
for f in (t.min, t.max):
    try:
        f()
        assert False
    except ValueError:
        pass
assert t.successor(1) is None
big = BST()
for k in range(2000):
    big.insert(k)
assert big.height() == 2000 and big.inorder() == list(range(2000))
assert big.delete(1000) and len(big) == 1999 and big.successor(999) == 1001
''',
         append={"bst.py": '''
    def _find(self, key):
        parent, cur = None, self.root
        while cur and cur.key != key:
            parent, cur = cur, (cur.left if key < cur.key else cur.right)
        return parent, cur

    def delete(self, key):
        parent, node = self._find(key)
        if node is None:
            return False
        if node.left and node.right:
            sp, succ = node, node.right
            while succ.left:
                sp, succ = succ, succ.left
            node.key = succ.key
            parent, node = sp, succ
        child = node.left or node.right
        if parent is None:
            self.root = child
        elif parent.left is node:
            parent.left = child
        else:
            parent.right = child
        self.size -= 1
        return True

    def inorder(self):
        out, st, cur = [], [], self.root
        while st or cur:
            while cur:
                st.append(cur)
                cur = cur.left
            cur = st.pop()
            out.append(cur.key)
            cur = cur.right
        return out

    def height(self):
        best, st = 0, ([(self.root, 1)] if self.root else [])
        while st:
            n, d = st.pop()
            best = max(best, d)
            for c in (n.left, n.right):
                if c:
                    st.append((c, d + 1))
        return best

    def min(self):
        if not self.root:
            raise ValueError("empty tree")
        cur = self.root
        while cur.left:
            cur = cur.left
        return cur.key

    def max(self):
        if not self.root:
            raise ValueError("empty tree")
        cur = self.root
        while cur.right:
            cur = cur.right
        return cur.key

    def successor(self, key):
        best, cur = None, self.root
        while cur:
            if cur.key > key:
                best, cur = cur.key, cur.left
            else:
                cur = cur.right
        return best
'''}),
    feat("py_feat_tokenizer_strings", "medium", "parsing",
         {"lexer.py": r'''
def tokenize(src):
    """Split source into (kind, text) tokens: NUM, NAME, OP; whitespace is skipped."""
    tokens = []
    i = 0
    while i < len(src):
        c = src[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit():
                j += 1
            tokens.append(("NUM", src[i:j]))
            i = j
        elif c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            tokens.append(("NAME", src[i:j]))
            i = j
        elif c in "+-*/=()<>,":
            tokens.append(("OP", c))
            i += 1
        else:
            raise ValueError("unexpected character %r at %d" % (c, i))
    return tokens
'''},
         "Extend `tokenize`: (1) double-quoted string literals produce ('STR', contents) with the escapes \\\" and \\\\ resolved (an unterminated string raises ValueError); "
         "(2) `#` starts a comment that runs to the end of the line and produces no token; (3) decimal numbers like 3.14 are a single NUM token ('3.14'); (4) two-character "
         "operators `==`, `<=`, `>=`, `!=` are single OP tokens. Everything that worked before must keep working (including the ValueError for unknown characters).",
         "from lexer import tokenize\nassert tokenize('x = \"hi\" # c') == [('NAME', 'x'), ('OP', '='), ('STR', 'hi')]\n",
         r'''
from lexer import tokenize
assert tokenize("x = \"hi\" # c") == [("NAME", "x"), ("OP", "="), ("STR", "hi")]
assert tokenize("a<=b == c != d >= e") == [("NAME", "a"), ("OP", "<="), ("NAME", "b"), ("OP", "=="), ("NAME", "c"), ("OP", "!="), ("NAME", "d"), ("OP", ">="), ("NAME", "e")]
assert tokenize("3.14*2") == [("NUM", "3.14"), ("OP", "*"), ("NUM", "2")]
assert tokenize("a = b # comment\nc") == [("NAME", "a"), ("OP", "="), ("NAME", "b"), ("NAME", "c")]
assert tokenize('print("a # not comment", 1)') == [("NAME", "print"), ("OP", "("), ("STR", "a # not comment"), ("OP", ","), ("NUM", "1"), ("OP", ")")]
assert tokenize(r'"q\"uote\\"') == [("STR", 'q"uote\\')]
assert tokenize('""') == [("STR", "")]
assert tokenize("<") == [("OP", "<")] and tokenize("=") == [("OP", "=")]
assert tokenize("1 + foo_2") == [("NUM", "1"), ("OP", "+"), ("NAME", "foo_2")]
assert tokenize("# only comment") == [] and tokenize("") == []
for bad in ['"open', "a $ b", "!"]:
    try:
        tokenize(bad)
        assert False, bad
    except ValueError:
        pass
''',
         replace={"lexer.py": r'''
def tokenize(src):
    """Split source into (kind, text) tokens: NUM, NAME, STR, OP; whitespace and comments are skipped."""
    tokens = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
        elif c == "#":
            while i < n and src[i] != "\n":
                i += 1
        elif c.isdigit():
            j = i
            while j < n and src[j].isdigit():
                j += 1
            if j + 1 < n and src[j] == "." and src[j + 1].isdigit():
                j += 1
                while j < n and src[j].isdigit():
                    j += 1
            tokens.append(("NUM", src[i:j]))
            i = j
        elif c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            tokens.append(("NAME", src[i:j]))
            i = j
        elif c == '"':
            j = i + 1
            buf = []
            while True:
                if j >= n:
                    raise ValueError("unterminated string at %d" % i)
                d = src[j]
                if d == '"':
                    break
                if d == "\\" and j + 1 < n and src[j + 1] in '"\\':
                    buf.append(src[j + 1])
                    j += 2
                else:
                    buf.append(d)
                    j += 1
            tokens.append(("STR", "".join(buf)))
            i = j + 1
        elif src[i:i + 2] in ("==", "<=", ">=", "!="):
            tokens.append(("OP", src[i:i + 2]))
            i += 2
        elif c in "+-*/=()<>,":
            tokens.append(("OP", c))
            i += 1
        else:
            raise ValueError("unexpected character %r at %d" % (c, i))
    return tokens
'''}),
    feat("py_feat_event_emitter", "medium", "design",
         {"emitter.py": r'''
class Emitter:
    def __init__(self):
        self._handlers = {}

    def on(self, event, fn):
        self._handlers.setdefault(event, []).append(fn)

    def emit(self, event, *args):
        for fn in list(self._handlers.get(event, [])):
            fn(*args)
'''},
         "Extend Emitter: `emit` must return the number of handlers that were called; `once(event, fn)` registers a handler that is removed after its first call; "
         "`off(event, fn=None)` removes that handler (first occurrence) or all handlers of the event when fn is None, and returns True if something was removed; "
         "`listeners(event)` returns a list copy of the handlers in registration order. If a handler raises, the remaining handlers must still run, and after all of "
         "them ran the FIRST exception is re-raised.",
         "from emitter import Emitter\ne = Emitter(); e.on('x', print)\nassert e.emit('x') == 1\n",
         r'''
from emitter import Emitter
e = Emitter()
log = []
a = lambda *x: log.append(("a",) + x)
b = lambda *x: log.append(("b",) + x)
e.on("go", a); e.on("go", b)
assert e.emit("go", 1) == 2 and log == [("a", 1), ("b", 1)]
assert e.emit("none") == 0
log.clear()
e.once("go", lambda *x: log.append("once"))
assert e.emit("go") == 3 and log[-1] == "once"
log.clear()
assert e.emit("go") == 2 and "once" not in log
assert e.listeners("go") == [a, b]
l = e.listeners("go"); l.clear()
assert len(e.listeners("go")) == 2
assert e.off("go", a) is True and e.off("go", a) is False and e.listeners("go") == [b]
assert e.off("go") is True and e.listeners("go") == [] and e.off("go") is False
ran = []
def boom(): raise RuntimeError("first")
def boom2(): raise KeyError("second")
e.on("x", boom); e.on("x", lambda: ran.append(1)); e.on("x", boom2)
try:
    e.emit("x")
    assert False
except RuntimeError as ex:
    assert str(ex) == "first"
assert ran == [1]
e2 = Emitter()
def self_remove():
    e2.off("y", self_remove)
e2.on("y", self_remove); e2.on("y", lambda: ran.append(2))
assert e2.emit("y") == 2
assert e2.emit("y") == 1
''',
         replace={"emitter.py": r'''
class Emitter:
    def __init__(self):
        self._handlers = {}

    def on(self, event, fn):
        self._handlers.setdefault(event, []).append(fn)

    def once(self, event, fn):
        def wrapper(*args):
            self.off(event, wrapper)
            return fn(*args)
        wrapper._orig = fn
        self.on(event, wrapper)

    def off(self, event, fn=None):
        hs = self._handlers.get(event, [])
        if fn is None:
            had = bool(hs)
            self._handlers[event] = []
            return had
        for i, h in enumerate(hs):
            if h is fn or getattr(h, "_orig", None) is fn:
                del hs[i]
                return True
        return False

    def listeners(self, event):
        return list(self._handlers.get(event, []))

    def emit(self, event, *args):
        first = None
        n = 0
        for fn in list(self._handlers.get(event, [])):
            n += 1
            try:
                fn(*args)
            except Exception as ex:
                if first is None:
                    first = ex
        if first is not None:
            raise first
        return n
'''}),
    feat("py_feat_vec2", "easy", "classes",
         {"vec.py": r'''
import math


class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __repr__(self):
        return "Vec2(%r, %r)" % (self.x, self.y)
'''},
         "Add to Vec2: `__eq__` (component-wise; compare with non-Vec2 gives NotImplemented/False) plus a consistent `__hash__`, `__sub__`, `__neg__`, `__mul__` and `__rmul__` "
         "by a scalar, `dot(other)`, `length()` (math.hypot), and `normalized()` returning a unit-length Vec2 (ValueError for the zero vector).",
         "from vec import Vec2\nassert Vec2(1, 2) - Vec2(1, 1) == Vec2(0, 1)\n",
         r'''
from vec import Vec2
a, b = Vec2(3, 4), Vec2(1, 2)
assert a + b == Vec2(4, 6) and a - b == Vec2(2, 2) and -a == Vec2(-3, -4)
assert a * 2 == Vec2(6, 8) and 2 * a == Vec2(6, 8)
assert a.dot(b) == 11 and a.length() == 5.0
n = a.normalized()
assert abs(n.x - 0.6) < 1e-12 and abs(n.y - 0.8) < 1e-12
assert a == Vec2(3, 4) and a != b and a != (3, 4)
assert hash(a) == hash(Vec2(3, 4)) and len({a, Vec2(3, 4), b}) == 2
try:
    Vec2(0, 0).normalized()
    assert False
except ValueError:
    pass
assert repr(a) == "Vec2(3, 4)"
''',
         append={"vec.py": '''
    def __eq__(self, other):
        if not isinstance(other, Vec2):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __neg__(self):
        return Vec2(-self.x, -self.y)

    def __mul__(self, k):
        return Vec2(self.x * k, self.y * k)

    __rmul__ = __mul__

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def length(self):
        return math.hypot(self.x, self.y)

    def normalized(self):
        n = self.length()
        if n == 0:
            raise ValueError("zero vector")
        return Vec2(self.x / n, self.y / n)
'''}),
    feat("py_feat_account_overdraft", "medium", "multi-file",
         {"account.py": r'''
class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance:
            raise ValueError("insufficient funds")
        self.balance -= amount
''', "bank.py": r'''
from account import Account


class Bank:
    def __init__(self):
        self.accounts = {}

    def open(self, owner, balance=0):
        if owner in self.accounts:
            raise ValueError("account exists")
        self.accounts[owner] = Account(owner, balance)
        return self.accounts[owner]

    def transfer(self, src, dst, amount):
        self.accounts[src].withdraw(amount)
        self.accounts[dst].deposit(amount)
'''},
         "Extend both files. Account: an optional `overdraft` limit (constructor arg, default 0) so withdraw may take the balance down to -overdraft; a `history` list of "
         "(kind, amount, balance_after) tuples with kind 'deposit' or 'withdraw' recorded after every successful operation (initial balance is not recorded). "
         "Bank: `open(owner, balance=0, overdraft=0)`; `transfer` must record kind 'transfer_out' on the source and 'transfer_in' on the destination (not "
         "'withdraw'/'deposit'), must leave BOTH accounts untouched if it fails (unknown account -> KeyError, insufficient funds -> ValueError), and returns None. "
         "Add `Bank.total()` (sum of all balances).",
         "from bank import Bank\nb = Bank(); b.open('a', 5, overdraft=5)\nb.accounts['a'].withdraw(8)\nassert b.accounts['a'].balance == -3\n",
         r'''
from bank import Bank
from account import Account
a = Account("x", 10, overdraft=5)
a.withdraw(12)
assert a.balance == -2
try:
    a.withdraw(4)
    assert False
except ValueError:
    pass
assert a.balance == -2
a.deposit(7)
assert a.history == [("withdraw", 12, -2), ("deposit", 7, 5)]
assert Account("y").overdraft == 0
b = Bank()
b.open("ann", 100); b.open("bob", 20, overdraft=10)
b.transfer("ann", "bob", 30)
assert b.accounts["ann"].balance == 70 and b.accounts["bob"].balance == 50
assert b.accounts["ann"].history == [("transfer_out", 30, 70)]
assert b.accounts["bob"].history == [("transfer_in", 30, 50)]
b.transfer("bob", "ann", 55)
assert b.accounts["bob"].balance == -5 and b.total() == 120 + 0
try:
    b.transfer("bob", "ann", 10)
    assert False
except ValueError:
    pass
assert b.accounts["bob"].balance == -5 and b.accounts["ann"].balance == 125
try:
    b.transfer("ann", "nobody", 1)
    assert False
except KeyError:
    pass
assert b.accounts["ann"].balance == 125 and len(b.accounts["ann"].history) == 2
try:
    b.open("ann")
    assert False
except ValueError:
    pass
''',
         replace={"account.py": r'''
class Account:
    def __init__(self, owner, balance=0, overdraft=0):
        self.owner = owner
        self.balance = balance
        self.overdraft = overdraft
        self.history = []

    def _apply(self, delta, kind):
        self.balance += delta
        self.history.append((kind, abs(delta), self.balance))

    def deposit(self, amount, kind="deposit"):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._apply(amount, kind)

    def withdraw(self, amount, kind="withdraw"):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance + self.overdraft:
            raise ValueError("insufficient funds")
        self._apply(-amount, kind)
''', "bank.py": r'''
from account import Account


class Bank:
    def __init__(self):
        self.accounts = {}

    def open(self, owner, balance=0, overdraft=0):
        if owner in self.accounts:
            raise ValueError("account exists")
        self.accounts[owner] = Account(owner, balance, overdraft)
        return self.accounts[owner]

    def transfer(self, src, dst, amount):
        a, b = self.accounts[src], self.accounts[dst]
        a.withdraw(amount, "transfer_out")
        b.deposit(amount, "transfer_in")

    def total(self):
        return sum(a.balance for a in self.accounts.values())
'''}),
    feat("py_feat_cursor_pages", "medium", "multi-file",
         {"store.py": r'''
class Store:
    def __init__(self, rows):
        self.rows = sorted(rows, key=lambda r: r["id"])

    def after(self, last_id, limit):
        """Rows with id > last_id (all rows if last_id is None), at most `limit`."""
        out = [r for r in self.rows if last_id is None or r["id"] > last_id]
        return out[:limit]
''', "api.py": r'''
from store import Store


def list_items(store, limit=10):
    rows = store.after(None, limit)
    return {"items": rows}
'''},
         "Add cursor pagination to api.py: `list_items(store, limit=10, cursor=None)` returns {'items': [...], 'next_cursor': X}, where `cursor` is the id of the last item "
         "of the previous page and X is the id of the last item on this page when more items remain after it, else None. limit < 1 raises ValueError. In store.py add "
         "`count_after(last_id)` returning how many rows have id > last_id (all rows when None) and use it (do not fetch limit+1 rows). Existing calls without cursor "
         "must keep working.",
         "from store import Store\nfrom api import list_items\nr = list_items(Store([{'id': i} for i in range(5)]), 2)\nassert r['next_cursor'] == 1\n",
         r'''
from store import Store
from api import list_items
s = Store([{"id": i, "v": i * i} for i in (5, 1, 3, 2, 4)])
assert s.count_after(None) == 5 and s.count_after(3) == 2 and s.count_after(5) == 0
p1 = list_items(s, 2)
assert [r["id"] for r in p1["items"]] == [1, 2] and p1["next_cursor"] == 2
p2 = list_items(s, 2, cursor=p1["next_cursor"])
assert [r["id"] for r in p2["items"]] == [3, 4] and p2["next_cursor"] == 4
p3 = list_items(s, 2, cursor=4)
assert [r["id"] for r in p3["items"]] == [5] and p3["next_cursor"] is None
assert list_items(s, 5)["next_cursor"] is None
assert list_items(s)["items"] == s.rows
assert list_items(Store([]))["items"] == [] and list_items(Store([]))["next_cursor"] is None
assert list_items(s, 1, cursor=99) == {"items": [], "next_cursor": None}
try:
    list_items(s, 0)
    assert False
except ValueError:
    pass
''',
         append={"store.py": '''
    def count_after(self, last_id):
        return sum(1 for r in self.rows if last_id is None or r["id"] > last_id)
'''},
         replace={"api.py": r'''
from store import Store


def list_items(store, limit=10, cursor=None):
    if limit < 1:
        raise ValueError("limit must be >= 1")
    rows = store.after(cursor, limit)
    more = bool(rows) and store.count_after(rows[-1]["id"]) > 0
    return {"items": rows, "next_cursor": rows[-1]["id"] if more else None}
'''}),
    feat("py_feat_lru_stats", "medium", "caching",
         {"lru.py": r'''
from collections import OrderedDict


class LRU:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._d = OrderedDict()

    def get(self, key, default=None):
        if key not in self._d:
            return default
        self._d.move_to_end(key)
        return self._d[key]

    def put(self, key, value):
        self._d[key] = value
        self._d.move_to_end(key)
        if len(self._d) > self.capacity:
            self._d.popitem(last=False)

    def __len__(self):
        return len(self._d)
'''},
         "Extend LRU: constructor takes an optional `on_evict(key, value)` callback called whenever an entry is evicted for capacity (including when `resize` shrinks the cache); track `hits` and `misses` attributes (get on present key = hit, absent = miss; `put` does not count); `hit_rate()` returns hits/(hits+misses) "
         "or 0.0 with no lookups; `resize(new_capacity)` changes capacity (ValueError if < 1), evicting the least recently used entries as needed; `pop(key, default=None)` "
         "removes and returns a value WITHOUT calling on_evict and without changing stats.",
         "from lru import LRU\nc = LRU(1); c.put('a', 1); c.get('a'); c.get('b')\nassert (c.hits, c.misses) == (1, 1)\n",
         r'''
from lru import LRU
ev = []
c = LRU(2, on_evict=lambda k, v: ev.append((k, v)))
c.put("a", 1); c.put("b", 2)
assert c.get("a") == 1 and c.get("z") is None and c.get("z", 7) == 7
assert (c.hits, c.misses) == (1, 2) and abs(c.hit_rate() - 1 / 3) < 1e-9
c.put("c", 3)
assert ev == [("b", 2)] and "b" not in c._d
c.put("c", 33)
assert ev == [("b", 2)] and len(c) == 2
c.put("d", 4)
assert ev == [("b", 2), ("a", 1)]
c.resize(1)
assert ev == [("b", 2), ("a", 1), ("c", 33)] and len(c) == 1 and c.capacity == 1
c.resize(3)
c.put("e", 5); c.put("f", 6)
assert len(c) == 3 and len(ev) == 3
assert c.pop("e") == 5 and c.pop("e", "none") == "none" and len(ev) == 3 and len(c) == 2
h, m = c.hits, c.misses
c.pop("f")
assert (c.hits, c.misses) == (h, m)
try:
    c.resize(0)
    assert False
except ValueError:
    pass
assert LRU(1).hit_rate() == 0.0
d = LRU(1)
d.put(1, 1); d.put(2, 2)
assert len(d) == 1
''',
         replace={"lru.py": r'''
from collections import OrderedDict


class LRU:
    def __init__(self, capacity, on_evict=None):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self.on_evict = on_evict
        self.hits = 0
        self.misses = 0
        self._d = OrderedDict()

    def get(self, key, default=None):
        if key not in self._d:
            self.misses += 1
            return default
        self.hits += 1
        self._d.move_to_end(key)
        return self._d[key]

    def _trim(self):
        while len(self._d) > self.capacity:
            k, v = self._d.popitem(last=False)
            if self.on_evict:
                self.on_evict(k, v)

    def put(self, key, value):
        self._d[key] = value
        self._d.move_to_end(key)
        self._trim()

    def resize(self, new_capacity):
        if new_capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = new_capacity
        self._trim()

    def pop(self, key, default=None):
        return self._d.pop(key, default)

    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def __len__(self):
        return len(self._d)
'''}),
    feat("py_feat_calc_power", "hard", "parsing",
         {"calc.py": r'''
class Parser:
    def __init__(self, text):
        self.s = text.replace(" ", "")
        self.i = 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def take(self):
        c = self.peek()
        self.i += 1
        return c

    def parse(self):
        v = self.expr()
        if self.i != len(self.s):
            raise ValueError("unexpected " + self.peek())
        return v

    def expr(self):
        v = self.term()
        while self.peek() in ("+", "-"):
            if self.take() == "+":
                v += self.term()
            else:
                v -= self.term()
        return v

    def term(self):
        v = self.atom()
        while self.peek() in ("*", "/"):
            if self.take() == "*":
                v *= self.atom()
            else:
                v /= self.atom()
        return v

    def atom(self):
        if self.peek() == "(":
            self.take()
            v = self.expr()
            if self.take() != ")":
                raise ValueError("missing )")
            return v
        j = self.i
        while self.peek().isdigit() or self.peek() == ".":
            self.take()
        if j == self.i:
            raise ValueError("expected number")
        return float(self.s[j:self.i])


def calc(text):
    return Parser(text).parse()
'''},
         "Extend the calculator: add `**` (exponent; right-associative; Python rules: "
         "-2**2 == -4 and 2**-1 == 0.5), unary minus and plus (`-3`, `+3`, `--3`, `2*-3`), and the `%` modulo operator (same precedence as * and /, Python semantics). "
         "Division or modulo by zero must raise ZeroDivisionError. Existing behaviour (precedence, parentheses, errors as ValueError) must stay.",
         "from calc import calc\nassert calc('2**3**2') == 512 and calc('-2**2') == -4\n",
         r'''
from calc import calc
assert calc("2**3**2") == 512
assert calc("-2**2") == -4
assert calc("2**-1") == 0.5
assert calc("(-2)**2") == 4
assert calc("2*3**2") == 18
assert calc("--3") == 3 and calc("+3") == 3 and calc("2*-3") == -6 and calc("3 - -3") == 6
assert calc("10 % 4") == 2 and calc("-7 % 3") == 2 and calc("2 + 7 % 4 * 2") == 8
assert calc("1+2*3") == 7 and calc("(1+2)*3") == 9 and calc("8/2/2") == 2
assert abs(calc("2**0.5**2") - 2 ** 0.25) < 1e-12
for bad, exc in [("1/0", ZeroDivisionError), ("5%0", ZeroDivisionError), ("2**", ValueError), ("(1", ValueError), ("1 +", ValueError), ("*3", ValueError), ("", ValueError)]:
    try:
        calc(bad)
        assert False, bad
    except exc:
        pass
''',
         patches=[("calc.py", '''        while self.peek() in ("*", "/"):
            if self.take() == "*":
                v *= self.atom()
            else:
                v /= self.atom()
        return v

    def atom(self):
        if self.peek() == "(":''', '''        while self.peek() in ("*", "/", "%"):
            if self.peek() == "*" and self.s[self.i:self.i + 2] == "**":
                break
            op = self.take()
            r = self.unary()
            if op == "*":
                v *= r
            elif op == "/":
                v /= r
            else:
                v %= r
        return v

    def unary(self):
        if self.peek() == "-":
            self.take()
            return -self.unary()
        if self.peek() == "+":
            self.take()
            return self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.s[self.i:self.i + 2] == "**":
            self.i += 2
            return base ** self.unary()
        return base

    def atom(self):
        if self.peek() == "(":'''),
                  ("calc.py", "        v = self.atom()\n        while self.peek() in", "        v = self.unary()\n        while self.peek() in")]),
    feat("py_feat_weighted_graph", "medium", "graphs",
         {"wgraph.py": r'''
from collections import deque


class Graph:
    def __init__(self):
        self.adj = {}

    def add_edge(self, u, v):
        self.adj.setdefault(u, set()).add(v)
        self.adj.setdefault(v, set()).add(u)

    def neighbors(self, u):
        return sorted(self.adj.get(u, ()))

    def hops(self, src, dst):
        """Fewest edges between src and dst, or -1."""
        if src not in self.adj or dst not in self.adj:
            return -1
        seen, q = {src}, deque([(src, 0)])
        while q:
            u, d = q.popleft()
            if u == dst:
                return d
            for v in self.neighbors(u):
                if v not in seen:
                    seen.add(v)
                    q.append((v, d + 1))
        return -1
'''},
         "Extend Graph with optional weights: `add_edge(u, v, w=1)` (undirected; adding the same edge again overwrites its weight; w must be > 0 else ValueError), "
         "`weight(u, v)` (KeyError if no such edge), `remove_edge(u, v)` (KeyError if missing; nodes stay), `cheapest(src, dst)` returning `(cost, path)` for the minimum total weight "
         "path (ties: the path with fewer hops, then lexicographically smaller node list) or None if unreachable or a node is unknown. `neighbors` and `hops` keep working unchanged.",
         "from wgraph import Graph\ng = Graph(); g.add_edge('a', 'b', 2)\nassert g.cheapest('a', 'b') == (2, ['a', 'b'])\n",
         r'''
from wgraph import Graph
g = Graph()
for u, v, w in [("a", "b", 1), ("b", "c", 1), ("a", "c", 5), ("c", "d", 2), ("a", "d", 4)]:
    g.add_edge(u, v, w)
assert g.neighbors("a") == ["b", "c", "d"] and g.hops("a", "d") == 1
assert g.weight("a", "c") == 5 and g.weight("c", "a") == 5
assert g.cheapest("a", "c") == (2, ["a", "b", "c"])
assert g.cheapest("a", "d") == (4, ["a", "d"])
g.add_edge("a", "d", 9)
assert g.weight("d", "a") == 9 and g.cheapest("a", "d") == (4, ["a", "b", "c", "d"])
g.remove_edge("b", "c")
assert g.cheapest("a", "c") == (5, ["a", "c"]) and g.neighbors("b") == ["a"]
assert g.cheapest("a", "a") == (0, ["a"])
g.add_edge("x", "y")
assert g.cheapest("a", "y") is None and g.cheapest("a", "nope") is None
assert g.hops("a", "y") == -1
for f in (lambda: g.weight("a", "y"), lambda: g.remove_edge("a", "y")):
    try:
        f()
        assert False
    except KeyError:
        pass
for w in (0, -1):
    try:
        g.add_edge("p", "q", w)
        assert False
    except ValueError:
        pass
h = Graph()
for u, v in [("s", "a"), ("a", "t"), ("s", "b"), ("b", "t")]:
    h.add_edge(u, v, 1)
assert h.cheapest("s", "t") == (2, ["s", "a", "t"])
k = Graph()
for u, v, w in [("s", "t", 3), ("s", "m", 1), ("m", "t", 2)]:
    k.add_edge(u, v, w)
assert k.cheapest("s", "t") == (3, ["s", "t"])
''',
         patches=[("wgraph.py", '''    def add_edge(self, u, v):
        self.adj.setdefault(u, set()).add(v)
        self.adj.setdefault(v, set()).add(u)

    def neighbors(self, u):
        return sorted(self.adj.get(u, ()))
''', '''    def add_edge(self, u, v, w=1):
        if w <= 0:
            raise ValueError("weight must be positive")
        self.adj.setdefault(u, {})[v] = w
        self.adj.setdefault(v, {})[u] = w

    def weight(self, u, v):
        return self.adj[u][v]

    def remove_edge(self, u, v):
        if v not in self.adj.get(u, {}):
            raise KeyError((u, v))
        del self.adj[u][v]
        del self.adj[v][u]

    def neighbors(self, u):
        return sorted(self.adj.get(u, ()))

    def cheapest(self, src, dst):
        import heapq
        if src not in self.adj or dst not in self.adj:
            return None
        best = {}
        h = [(0, 1, [src])]
        while h:
            cost, hops, path = heapq.heappop(h)
            u = path[-1]
            if u in best:
                continue
            best[u] = (cost, path)
            if u == dst:
                return cost, path
            for v in self.adj[u]:
                if v not in best:
                    heapq.heappush(h, (cost + self.adj[u][v], hops + 1, path + [v]))
        return None
''')]),
    feat("py_feat_tictactoe", "medium", "classes",
         {"ttt.py": r'''
class Board:
    LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]

    def __init__(self):
        self.cells = [" "] * 9
        self.turn = "X"

    def play(self, pos):
        """Place the current player's mark at pos (0-8); IndexError for bad pos, ValueError if taken."""
        if not 0 <= pos < 9:
            raise IndexError(pos)
        if self.cells[pos] != " ":
            raise ValueError("cell taken")
        self.cells[pos] = self.turn
        self.turn = "O" if self.turn == "X" else "X"
'''},
         "Extend Board: `winner()` returns 'X', 'O' or None; `is_draw()` (board full and no winner); `over()`; `play` must raise ValueError once the game is over; "
         "`undo()` takes back the last move (restoring whose turn it is; IndexError if there are no moves); `moves()` returns the list of empty positions in ascending order "
         "(empty list when the game is over); `__str__` renders three rows 'X|O| ' separated by newlines with no trailing newline.",
         "from ttt import Board\nb = Board(); b.play(0)\nassert b.winner() is None and b.moves()[0] == 1\n",
         r'''
from ttt import Board
b = Board()
for p in (0, 3, 1, 4):
    b.play(p)
assert b.winner() is None and not b.over() and b.moves() == [2, 5, 6, 7, 8]
assert str(b) == "X|X| \nO|O| \n | | "
b.play(2)
assert b.winner() == "X" and b.over() and not b.is_draw() and b.moves() == []
try:
    b.play(8)
    assert False
except ValueError:
    pass
b.undo()
assert b.winner() is None and b.turn == "X" and b.cells[2] == " "
b.play(5)
assert b.turn == "O"
b.undo(); b.undo(); b.undo(); b.undo(); b.undo()
assert b.cells == [" "] * 9 and b.turn == "X"
try:
    b.undo()
    assert False
except IndexError:
    pass
d = Board()
for p in (0, 1, 2, 4, 3, 5, 7, 6, 8):
    d.play(p)
assert d.winner() is None and d.is_draw() and d.over()
o = Board()
for p in (0, 3, 1, 4, 8, 5):
    o.play(p)
assert o.winner() == "O"
try:
    o.play(0)
    assert False
except ValueError:
    pass
try:
    Board().play(9)
    assert False
except IndexError:
    pass
''',
         replace={"ttt.py": r'''
class Board:
    LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]

    def __init__(self):
        self.cells = [" "] * 9
        self.turn = "X"
        self._history = []

    def winner(self):
        for a, b, c in self.LINES:
            if self.cells[a] != " " and self.cells[a] == self.cells[b] == self.cells[c]:
                return self.cells[a]
        return None

    def is_draw(self):
        return " " not in self.cells and self.winner() is None

    def over(self):
        return self.winner() is not None or " " not in self.cells

    def play(self, pos):
        """Place the current player's mark at pos (0-8); IndexError for bad pos, ValueError if taken or game over."""
        if not 0 <= pos < 9:
            raise IndexError(pos)
        if self.over():
            raise ValueError("game over")
        if self.cells[pos] != " ":
            raise ValueError("cell taken")
        self.cells[pos] = self.turn
        self._history.append(pos)
        self.turn = "O" if self.turn == "X" else "X"

    def undo(self):
        if not self._history:
            raise IndexError("no moves")
        pos = self._history.pop()
        self.turn = self.cells[pos]
        self.cells[pos] = " "

    def moves(self):
        return [] if self.over() else [i for i, c in enumerate(self.cells) if c == " "]

    def __str__(self):
        return "\n".join("|".join(self.cells[r * 3:r * 3 + 3]) for r in range(3))
'''}),
    feat("py_feat_money_allocate", "hard", "classes",
         {"money.py": r'''
class Money:
    """Amount in integer cents."""

    def __init__(self, cents, currency="USD"):
        self.cents = int(cents)
        self.currency = currency

    def __add__(self, other):
        self._check(other)
        return Money(self.cents + other.cents, self.currency)

    def _check(self, other):
        if self.currency != other.currency:
            raise ValueError("currency mismatch")

    def __repr__(self):
        return "Money(%d, %r)" % (self.cents, self.currency)
'''},
         "Add to Money: `__eq__`/`__hash__`, `__sub__`, `__neg__`, `__lt__`/`__le__` (same currency only, else ValueError), `__mul__` by an int or float (round half away from zero "
         "to whole cents) and `format()` -> '$12.34' for USD, '-$0.05' for negatives, '12.34 EUR' for other currencies (thousands separators not needed). "
         "Add `allocate(ratios)` splitting the amount into len(ratios) Money parts proportional to the non-negative int ratios so the parts sum exactly to the original: give "
         "each part floor(total*ratio/sum) then hand out the leftover cents one at a time to the parts with the largest fractional remainder (ties: earlier part first). "
         "Works for negative amounts by allocating the absolute value and negating. Empty ratios, negative ratios or all-zero ratios raise ValueError.",
         "from money import Money\nassert [m.cents for m in Money(100).allocate([1, 1, 1])] == [34, 33, 33]\n",
         r'''
from money import Money
assert Money(100).allocate([1, 1, 1]) == [Money(34), Money(33), Money(33)]
assert Money(5).allocate([3, 7]) == [Money(2), Money(3)]
assert [m.cents for m in Money(101).allocate([1, 1])] == [51, 50]
assert [m.cents for m in Money(100).allocate([0, 1])] == [0, 100]
assert [m.cents for m in Money(-100).allocate([1, 1, 1])] == [-34, -33, -33]
assert sum(m.cents for m in Money(12345).allocate([5, 3, 2, 1, 1])) == 12345
assert Money(7, "EUR").allocate([1])[0] == Money(7, "EUR")
assert Money(1).allocate([1, 1, 1]) == [Money(1), Money(0), Money(0)]
for bad in ([], [-1, 2], [0, 0]):
    try:
        Money(10).allocate(bad)
        assert False, bad
    except ValueError:
        pass
a, b = Money(1050), Money(250)
assert a - b == Money(800) and -b == Money(-250) and a + b == Money(1300)
assert b < a and b <= b and not a < b
assert a == Money(1050) and a != Money(1050, "EUR") and hash(a) == hash(Money(1050)) and a != 1050
for f in (lambda: a < Money(1, "EUR"), lambda: a - Money(1, "EUR")):
    try:
        f()
        assert False
    except ValueError:
        pass
assert Money(1000) * 2 == Money(2000) and Money(1000) * 0.125 == Money(125) and Money(5) * 0.5 == Money(3) and Money(-5) * 0.5 == Money(-3)
assert Money(1234).format() == "$12.34" and Money(-5).format() == "-$0.05" and Money(1234, "EUR").format() == "12.34 EUR"
assert Money(0).format() == "$0.00" and Money(100).format() == "$1.00"
''',
         append={"money.py": '''
    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return self.cents == other.cents and self.currency == other.currency

    def __hash__(self):
        return hash((self.cents, self.currency))

    def __sub__(self, other):
        self._check(other)
        return Money(self.cents - other.cents, self.currency)

    def __neg__(self):
        return Money(-self.cents, self.currency)

    def __lt__(self, other):
        self._check(other)
        return self.cents < other.cents

    def __le__(self, other):
        self._check(other)
        return self.cents <= other.cents

    def __mul__(self, k):
        import math
        x = self.cents * k
        r = math.floor(abs(x) + 0.5)
        return Money(-r if x < 0 else r, self.currency)

    def format(self):
        sign = "-" if self.cents < 0 else ""
        whole, frac = divmod(abs(self.cents), 100)
        if self.currency == "USD":
            return "%s$%d.%02d" % (sign, whole, frac)
        return "%s%d.%02d %s" % (sign, whole, frac, self.currency)

    def allocate(self, ratios):
        if not ratios or any(r < 0 for r in ratios) or sum(ratios) == 0:
            raise ValueError("bad ratios")
        total = abs(self.cents)
        s = sum(ratios)
        parts = [total * r // s for r in ratios]
        rems = [(total * r % s, -i) for i, r in enumerate(ratios)]
        left = total - sum(parts)
        for _, ni in sorted(rems, reverse=True)[:left]:
            parts[-ni] += 1
        sign = -1 if self.cents < 0 else 1
        return [Money(sign * p, self.currency) for p in parts]
'''}),
    feat("py_feat_interval_set", "hard", "intervals",
         {"iset.py": r'''
class IntervalSet:
    """A set of integers stored as sorted, disjoint, non-adjacent half-open ranges [start, end)."""

    def __init__(self):
        self.ranges = []

    def add(self, start, end):
        if start >= end:
            return
        out = []
        placed = False
        for s, e in self.ranges:
            if e < start:
                out.append((s, e))
            elif s > end:
                if not placed:
                    out.append((start, end))
                    placed = True
                out.append((s, e))
            else:
                start, end = min(start, s), max(end, e)
        if not placed:
            out.append((start, end))
        self.ranges = out

    def __contains__(self, x):
        return any(s <= x < e for s, e in self.ranges)

    def total(self):
        return sum(e - s for s, e in self.ranges)
'''},
         "Add to IntervalSet: `remove(start, end)` (delete that half-open range from the set, splitting ranges as needed; no-op for an empty range) and "
         "`intersection(other)` returning a NEW IntervalSet of the points present in both, `union(other)` (new set), `gaps(lo, hi)` returning the list of (s, e) "
         "ranges inside [lo, hi) that are NOT covered, and `__eq__` (same ranges). Representation invariant must hold after every operation (sorted, disjoint, non-adjacent: "
         "(1,3) and (3,5) are stored as (1,5)).",
         "from iset import IntervalSet\ns = IntervalSet(); s.add(0, 10); s.remove(3, 5)\nassert s.ranges == [(0, 3), (5, 10)]\n",
         r'''
from iset import IntervalSet


def mk(*rs):
    s = IntervalSet()
    for a, b in rs:
        s.add(a, b)
    return s


s = mk((0, 10))
s.remove(3, 5)
assert s.ranges == [(0, 3), (5, 10)] and s.total() == 8
s.remove(0, 3)
assert s.ranges == [(5, 10)]
s.remove(7, 7)
assert s.ranges == [(5, 10)]
s.remove(-5, 6)
assert s.ranges == [(6, 10)]
s.remove(9, 100)
assert s.ranges == [(6, 9)] and 8 in s and 9 not in s
s.remove(0, 100)
assert s.ranges == [] and s.total() == 0
a = mk((1, 5), (8, 12), (20, 25))
b = mk((3, 9), (11, 21), (30, 40))
assert a.intersection(b).ranges == [(3, 5), (8, 9), (11, 12), (20, 21)]
assert b.intersection(a).ranges == a.intersection(b).ranges
assert a.union(b).ranges == [(1, 25), (30, 40)]
assert a.ranges == [(1, 5), (8, 12), (20, 25)]
assert mk((1, 3), (3, 5)).ranges == [(1, 5)]
assert mk((0, 2)).union(mk((2, 4))).ranges == [(0, 4)]
assert mk((0, 2)).intersection(mk((2, 4))).ranges == []
assert a.gaps(0, 30) == [(0, 1), (5, 8), (12, 20), (25, 30)]
assert a.gaps(2, 4) == [] and a.gaps(5, 8) == [(5, 8)] and a.gaps(3, 10) == [(5, 8)]
assert IntervalSet().gaps(1, 4) == [(1, 4)]
assert a == mk((20, 25), (8, 12), (1, 5)) and a != b
assert 3 in a and 5 not in a
''',
         append={"iset.py": '''
    def remove(self, start, end):
        if start >= end:
            return
        out = []
        for s, e in self.ranges:
            if e <= start or s >= end:
                out.append((s, e))
                continue
            if s < start:
                out.append((s, start))
            if e > end:
                out.append((end, e))
        self.ranges = out

    def intersection(self, other):
        res = IntervalSet()
        for s, e in self.ranges:
            for s2, e2 in other.ranges:
                lo, hi = max(s, s2), min(e, e2)
                if lo < hi:
                    res.add(lo, hi)
        return res

    def union(self, other):
        res = IntervalSet()
        for s, e in self.ranges + other.ranges:
            res.add(s, e)
        return res

    def gaps(self, lo, hi):
        out = []
        cur = lo
        for s, e in self.ranges:
            if e <= cur:
                continue
            if s >= hi:
                break
            if s > cur:
                out.append((cur, s))
            cur = max(cur, e)
        if cur < hi:
            out.append((cur, hi))
        return out

    def __eq__(self, other):
        return isinstance(other, IntervalSet) and self.ranges == other.ranges
'''}),
    feat("py_feat_trie_wildcard", "medium", "tries",
         {"trie.py": r'''
class TrieNode:
    def __init__(self):
        self.kids = {}
        self.end = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def add(self, word):
        node = self.root
        for ch in word:
            node = node.kids.setdefault(ch, TrieNode())
        node.end = True

    def has(self, word):
        node = self.root
        for ch in word:
            node = node.kids.get(ch)
            if node is None:
                return False
        return node.end
'''},
         "Add to Trie: `search(pattern)` where '.' matches any single character (True/False, whole word must match); `with_prefix(prefix)` returning the sorted list of all "
         "stored words that start with prefix (empty prefix gives all words); `longest_common_prefix()` of all stored words ('' when empty). Must not recurse more than the "
         "word length (words up to 3000 chars must work).",
         "from trie import Trie\nt = Trie(); t.add('cat')\nassert t.search('c.t') and not t.search('c.')\n",
         r'''
from trie import Trie
t = Trie()
for w in ["bad", "dad", "mad", "pad", "padding", "pa"]:
    t.add(w)
assert t.search("pad") and t.search(".ad") and t.search("b..") and t.search("pa") and t.search("p.dding")
assert not t.search("b.") and not t.search("x..") and not t.search("pad.") and not t.search("")
assert t.with_prefix("pa") == ["pa", "pad", "padding"]
assert t.with_prefix("") == ["bad", "dad", "mad", "pa", "pad", "padding"]
assert t.with_prefix("z") == [] and t.with_prefix("padding") == ["padding"]
assert t.has("pa") and not t.has("p")
assert t.longest_common_prefix() == ""
u = Trie()
assert u.longest_common_prefix() == ""
for w in ["flower", "flow", "flight"]:
    u.add(w)
assert u.longest_common_prefix() == "fl"
v = Trie(); v.add("solo")
assert v.longest_common_prefix() == "solo"
v.add("sol")
assert v.longest_common_prefix() == "sol"
long = "a" * 3000
w = Trie(); w.add(long)
assert w.search("." * 3000) and not w.search("." * 2999) and w.with_prefix("a") == [long] and w.longest_common_prefix() == long
''',
         append={"trie.py": '''
    def search(self, pattern):
        level = [self.root]
        for ch in pattern:
            nxt = []
            for node in level:
                if ch == ".":
                    nxt.extend(node.kids.values())
                elif ch in node.kids:
                    nxt.append(node.kids[ch])
            level = nxt
            if not level:
                return False
        return bool(pattern) and any(n.end for n in level)

    def with_prefix(self, prefix):
        node = self.root
        for ch in prefix:
            node = node.kids.get(ch)
            if node is None:
                return []
        out, st = [], [(node, prefix)]
        while st:
            n, w = st.pop()
            if n.end:
                out.append(w)
            for ch, k in n.kids.items():
                st.append((k, w + ch))
        return sorted(out)

    def longest_common_prefix(self):
        node, out = self.root, []
        while len(node.kids) == 1 and not node.end:
            ch, node = next(iter(node.kids.items()))
            out.append(ch)
        return "".join(out)
'''}),
    feat("py_feat_pq_remove", "hard", "heaps",
         {"pq.py": r'''
import heapq


class PriorityQueue:
    """Min-priority queue of (priority, item); ties pop in insertion order."""

    def __init__(self):
        self._h = []
        self._n = 0

    def push(self, item, priority):
        heapq.heappush(self._h, (priority, self._n, item))
        self._n += 1

    def pop(self):
        if not self._h:
            raise IndexError("pop from empty queue")
        return heapq.heappop(self._h)[2]

    def __len__(self):
        return len(self._h)
'''},
         "Items are now unique: `push(item, priority)` on an item that is already queued replaces its priority (it counts as a new insertion for tie-breaking). Add `remove(item)` "
         "(KeyError if absent), `__contains__`, `priority(item)` (KeyError if absent) and `peek()` returning the next item without removing it (IndexError if empty). "
         "`__len__` must count only live items and `pop` must never return a removed or superseded entry. Use lazy deletion (no O(n) rebuild per call): 20000 updates must be fast. "
         "Items are hashable.",
         "from pq import PriorityQueue\nq = PriorityQueue(); q.push('a', 5); q.push('a', 1)\nassert len(q) == 1 and q.pop() == 'a'\n",
         r'''
from pq import PriorityQueue
q = PriorityQueue()
q.push("a", 5); q.push("b", 2); q.push("c", 9)
assert len(q) == 3 and q.peek() == "b" and "a" in q and q.priority("c") == 9
q.push("a", 1)
assert len(q) == 3 and q.peek() == "a" and q.priority("a") == 1
q.remove("b")
assert "b" not in q and len(q) == 2
assert q.pop() == "a" and q.pop() == "c" and len(q) == 0
for f in (q.pop, q.peek, lambda: q.remove("a"), lambda: q.priority("a")):
    try:
        f()
        assert False
    except (IndexError, KeyError):
        pass
t = PriorityQueue()
t.push("x", 1); t.push("y", 1); t.push("z", 1)
t.push("x", 1)
assert [t.pop() for _ in range(3)] == ["y", "z", "x"]
u = PriorityQueue()
for i in range(20000):
    u.push(i % 100, 20000 - i)
assert len(u) == 100
first = u.pop()
assert first == 99 and len(u) == 99
u.remove(98)
assert u.pop() == 97
r = PriorityQueue()
r.push("k", 3); r.remove("k"); r.push("k", 4)
assert len(r) == 1 and r.pop() == "k" and len(r) == 0
''',
         replace={"pq.py": r'''
import heapq


class PriorityQueue:
    """Min-priority queue of unique items; ties pop in insertion order."""

    def __init__(self):
        self._h = []
        self._live = {}
        self._n = 0

    def push(self, item, priority):
        self._n += 1
        self._live[item] = (priority, self._n)
        heapq.heappush(self._h, (priority, self._n, item))

    def _clean(self):
        while self._h and self._live.get(self._h[0][2]) != (self._h[0][0], self._h[0][1]):
            heapq.heappop(self._h)

    def pop(self):
        self._clean()
        if not self._h:
            raise IndexError("pop from empty queue")
        _, _, item = heapq.heappop(self._h)
        del self._live[item]
        return item

    def peek(self):
        self._clean()
        if not self._h:
            raise IndexError("peek at empty queue")
        return self._h[0][2]

    def remove(self, item):
        del self._live[item]

    def priority(self, item):
        return self._live[item][0]

    def __contains__(self, item):
        return item in self._live

    def __len__(self):
        return len(self._live)
'''}),
    feat("py_feat_ini_dump", "medium", "parsing",
         {"ini.py": r'''
def parse(text):
    """Parse INI text into {section: {key: value}} (strings). Keys before any section go under ''."""
    out = {}
    cur = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in ";#":
            continue
        if line[0] == "[" and line[-1] == "]":
            cur = line[1:-1].strip()
            out.setdefault(cur, {})
        elif "=" in line:
            k, v = line.split("=", 1)
            out.setdefault(cur, {})[k.strip()] = v.strip()
        else:
            raise ValueError("bad line: " + raw)
    return out
'''},
         "Add to ini.py: `dump(data)` turning {section: {key: value}} back into INI text so that parse(dump(d)) == d. Format: the '' section (if present and non-empty) first as "
         "bare `key = value` lines, then each other section in the dict's order as `[name]` followed by its `key = value` lines, with one blank line between blocks and a single "
         "trailing newline. Values are written with str(); keys or section names containing '=', ']' or a newline, and values containing a newline, raise ValueError. "
         "Also add `get(data, section, key, kind=str, default=None)`: returns the converted value, `default` if the section or key is missing, and for kind=bool accepts "
         "1/true/yes/on and 0/false/no/off (case-insensitive), raising ValueError otherwise.",
         "import ini\nassert ini.dump({'a': {'x': 1}}) == '[a]\\nx = 1\\n'\n",
         r'''
import ini
assert ini.dump({"a": {"x": 1}}) == "[a]\nx = 1\n"
d = {"": {"top": "1"}, "db": {"host": "h", "port": 5432}, "empty": {}}
t = ini.dump(d)
assert t == "top = 1\n\n[db]\nhost = h\nport = 5432\n\n[empty]\n"
assert ini.parse(t) == {"": {"top": "1"}, "db": {"host": "h", "port": "5432"}, "empty": {}}
assert ini.dump({}) == "" and ini.dump({"": {}}) == ""
assert ini.dump({"s": {"a": "x"}, "t": {"b": "y"}}) == "[s]\na = x\n\n[t]\nb = y\n"
for bad in ({"s": {"a=b": 1}}, {"s]": {}}, {"s": {"a": "x\ny"}}, {"s": {"a\nb": 1}}):
    try:
        ini.dump(bad)
        assert False, bad
    except ValueError:
        pass
data = ini.parse("[a]\nn = 42\nf = 2.5\nflag = Yes\noff = 0\nbad = maybe\n")
assert ini.get(data, "a", "n", int) == 42 and ini.get(data, "a", "f", float) == 2.5
assert ini.get(data, "a", "flag", bool) is True and ini.get(data, "a", "off", bool) is False
assert ini.get(data, "a", "n") == "42"
assert ini.get(data, "zz", "n", int, default=7) == 7 and ini.get(data, "a", "nope") is None and ini.get(data, "a", "nope", int, 0) == 0
try:
    ini.get(data, "a", "bad", bool)
    assert False
except ValueError:
    pass
assert ini.parse("[x]\ny = 1") == {"x": {"y": "1"}}
''',
         append={"ini.py": '''

def dump(data):
    blocks = []
    for section, items in data.items():
        if any(c in str(section) for c in "]\\n"):
            raise ValueError("bad section name")
        lines = []
        for k, v in items.items():
            if any(c in str(k) for c in "=\\n") or "\\n" in str(v):
                raise ValueError("bad key or value")
            lines.append("%s = %s" % (k, v))
        if section == "":
            if lines:
                blocks.insert(0, "\\n".join(lines))
        else:
            blocks.append("\\n".join(["[%s]" % section] + lines))
    return "\\n\\n".join(blocks) + "\\n" if blocks else ""


def get(data, section, key, kind=str, default=None):
    if section not in data or key not in data[section]:
        return default
    raw = data[section][key]
    if kind is bool:
        low = raw.strip().lower()
        if low in ("1", "true", "yes", "on"):
            return True
        if low in ("0", "false", "no", "off"):
            return False
        raise ValueError(raw)
    return kind(raw)
'''}),
]
