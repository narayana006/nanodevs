TASKS = []

TASKS.append(dict(
    id="qa_token_bucket", diff="hard",
    spec="Write tests for the `TokenBucket` class in bucket.py. Time is passed in explicitly, so tests are deterministic.",
    files={"bucket.py": r'''
class TokenBucket:
    """Token-bucket rate limiter. Holds up to `capacity` tokens, refilled at `rate` tokens per second, and starts
    full. allow(now, cost=1) takes `cost` tokens and returns True if enough are available, else returns False
    and takes nothing. `now` is a float of seconds and never goes backwards (a smaller `now` than the last call is
    treated as no time passing). cost > capacity can never succeed. capacity < 1, rate <= 0 or cost < 1 -> ValueError."""

    def __init__(self, capacity, rate):
        if capacity < 1 or rate <= 0:
            raise ValueError("bad bucket")
        self.capacity = capacity
        self.rate = rate
        self.tokens = float(capacity)
        self.last = None

    def allow(self, now, cost=1):
        if cost < 1:
            raise ValueError("bad cost")
        if self.last is not None and now > self.last:
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        if self.last is None or now > self.last:
            self.last = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
'''},
    tests=r'''
from bucket import TokenBucket

b = TokenBucket(3, 1)
assert [b.allow(0) for _ in range(4)] == [True, True, True, False]
assert b.allow(0.5) is False
assert b.allow(1) is True
assert b.allow(1) is False
assert b.allow(100) is True
assert [b.allow(100) for _ in range(3)] == [True, True, False]

b = TokenBucket(2, 2)
assert b.allow(0, cost=2) is True
assert b.allow(0) is False
assert b.allow(0.5) is True
assert b.allow(0.5) is False
assert b.allow(1.0) is True

b = TokenBucket(5, 1)
assert b.allow(0, cost=6) is False
assert b.allow(0, cost=5) is True
assert b.allow(3, cost=3) is True
assert b.allow(3, cost=1) is False

b = TokenBucket(1, 1)
assert b.allow(10) is True
assert b.allow(5) is False
assert b.allow(10.5) is False
assert b.allow(11) is True

b = TokenBucket(2, 1)
b.allow(0)
b.allow(0)
assert b.allow(0, cost=2) is False
assert b.allow(1, cost=2) is False
assert b.allow(2, cost=2) is True

for args in ((0, 1), (1, 0), (1, -1)):
    try:
        TokenBucket(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
try:
    TokenBucket(1, 1).allow(0, cost=0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("logic: capacity not capped", "min(self.capacity, self.tokens + (now - self.last) * self.rate)", "self.tokens + (now - self.last) * self.rate"),
        ("boundary: exact tokens refused", "if self.tokens >= cost:", "if self.tokens > cost:"),
        ("logic: failed request consumes", "        return False\n", "        self.tokens = max(0, self.tokens - cost)\n        return False\n"),
        ("logic: refill rate ignored", "(now - self.last) * self.rate", "(now - self.last)"),
        ("logic: starts empty", "self.tokens = float(capacity)", "self.tokens = 0.0"),
        ("missing-edge-case: time going backwards", "if self.last is None or now > self.last:\n            self.last = now", "if True:\n            self.last = now"),
        ("logic: cost ignored", "self.tokens -= cost", "self.tokens -= 1"),
        ("boundary: rate 0 accepted", "if capacity < 1 or rate <= 0:", "if capacity < 1 or rate < 0:"),
    ],
    weak=7,
))

TASKS.append(dict(
    id="qa_sliding_window", diff="hard",
    spec="Write tests for the `SlidingWindowLimiter` class in window.py (time is passed in explicitly).",
    files={"window.py": r'''
from collections import deque


class SlidingWindowLimiter:
    """Allow at most `limit` events in any window of `window` seconds. allow(now) records the event and returns True
    if fewer than `limit` events happened in the half-open interval (now - window, now], else returns False and does
    not record it. Events are given with non-decreasing `now`. remaining(now) = how many more events would be
    allowed right now. limit < 1 or window <= 0 -> ValueError."""

    def __init__(self, limit, window):
        if limit < 1 or window <= 0:
            raise ValueError("bad limiter")
        self.limit = limit
        self.window = window
        self._events = deque()

    def _expire(self, now):
        while self._events and self._events[0] <= now - self.window:
            self._events.popleft()

    def allow(self, now):
        self._expire(now)
        if len(self._events) >= self.limit:
            return False
        self._events.append(now)
        return True

    def remaining(self, now):
        self._expire(now)
        return self.limit - len(self._events)
'''},
    tests=r'''
from window import SlidingWindowLimiter

s = SlidingWindowLimiter(3, 10)
assert s.remaining(0) == 3
assert s.allow(0) is True
assert s.allow(1) is True
assert s.remaining(1) == 1
assert s.allow(2) is True
assert s.remaining(2) == 0
assert s.allow(3) is False
assert s.allow(9.9) is False
assert s.remaining(9.9) == 0
assert s.allow(10) is True
assert s.remaining(10) == 0
assert s.allow(10.5) is False
assert s.allow(11) is True
assert s.remaining(11) == 0
assert s.remaining(21) == 3

s = SlidingWindowLimiter(1, 5)
assert s.allow(0) is True
assert s.allow(4.999) is False
assert s.allow(5) is True
assert s.allow(9.999) is False
assert s.allow(10) is True

s = SlidingWindowLimiter(2, 1)
assert s.allow(0) is True
assert s.allow(0) is True
assert s.allow(0) is False
assert s.allow(1) is True
assert s.remaining(1) == 0 or s.remaining(1) == 1
assert s.allow(1) is True
assert s.allow(1) is False
for args in ((0, 1), (1, 0), (1, -1)):
    try:
        SlidingWindowLimiter(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("boundary: event at exactly window age kept", "self._events[0] <= now - self.window", "self._events[0] < now - self.window"),
        ("boundary: limit off-by-one", "len(self._events) >= self.limit", "len(self._events) > self.limit"),
        ("logic: rejected events recorded", "        if len(self._events) >= self.limit:\n            return False\n", "        if len(self._events) >= self.limit:\n            self._events.append(now)\n            return False\n"),
        ("missing-edge-case: remaining does not expire", "    def remaining(self, now):\n        self._expire(now)\n", "    def remaining(self, now):\n"),
        ("logic: remaining off-by-one", "return self.limit - len(self._events)", "return self.limit - len(self._events) - 1"),
        ("logic: window reset instead of slide", "self._events[0] <= now - self.window", "self._events[-1] <= now - self.window"),
        ("boundary: window 0 accepted", "if limit < 1 or window <= 0:", "if limit < 1 or window < 0:"),
    ],
    weak=6,
))

TASKS.append(dict(
    id="qa_circuit_breaker", diff="hard",
    spec="Write tests for the `CircuitBreaker` class in breaker.py. Time is passed in explicitly.",
    files={"breaker.py": r'''
class CircuitBreaker:
    """States: 'closed' (calls allowed), 'open' (calls refused), 'half_open' (one trial call allowed).
    - closed: record_failure() counts consecutive failures; reaching `threshold` opens the circuit at that time.
      record_success() resets the count.
    - open: allow(now) is False until `cooldown` seconds have passed since opening; then the state becomes
      'half_open' and allow() returns True.
    - half_open: record_success() closes the circuit; record_failure() re-opens it (cooldown restarts at that time).
    state(now) returns the current state name (it performs the open -> half_open transition when cooldown is over).
    threshold < 1 or cooldown <= 0 -> ValueError."""

    def __init__(self, threshold, cooldown):
        if threshold < 1 or cooldown <= 0:
            raise ValueError("bad breaker")
        self.threshold = threshold
        self.cooldown = cooldown
        self._state = "closed"
        self._failures = 0
        self._opened_at = None

    def state(self, now):
        if self._state == "open" and now - self._opened_at >= self.cooldown:
            self._state = "half_open"
        return self._state

    def allow(self, now):
        return self.state(now) != "open"

    def record_success(self):
        self._failures = 0
        self._state = "closed"

    def record_failure(self, now):
        if self._state == "half_open":
            self._state = "open"
            self._opened_at = now
            return
        self._failures += 1
        if self._failures >= self.threshold:
            self._state = "open"
            self._opened_at = now
'''},
    tests=r'''
from breaker import CircuitBreaker

b = CircuitBreaker(3, 10)
assert b.state(0) == "closed" and b.allow(0) is True
b.record_failure(0)
b.record_failure(1)
assert b.state(1) == "closed" and b.allow(1) is True
b.record_failure(2)
assert b.state(2) == "open" and b.allow(2) is False
assert b.allow(11.9) is False
assert b.state(11.9) == "open"
assert b.state(12) == "half_open" and b.allow(12) is True
b.record_success()
assert b.state(12) == "closed"
b.record_failure(13)
b.record_failure(14)
assert b.state(14) == "closed"

b = CircuitBreaker(2, 5)
b.record_failure(0)
b.record_success()
b.record_failure(1)
assert b.state(1) == "closed"
b.record_failure(2)
assert b.state(2) == "open"
assert b.state(7) == "half_open"
b.record_failure(8)
assert b.state(8) == "open"
assert b.state(12.9) == "open"
assert b.state(13) == "half_open"
b.record_success()
b.record_failure(20)
assert b.state(20) == "closed"

b = CircuitBreaker(1, 1)
b.record_failure(0)
assert b.state(0.5) == "open"
assert b.state(1) == "half_open"
assert b.allow(1) is True
assert b.allow(1) is True

for args in ((0, 1), (1, 0)):
    try:
        CircuitBreaker(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("boundary: threshold off-by-one", "self._failures >= self.threshold", "self._failures > self.threshold"),
        ("boundary: cooldown boundary", "now - self._opened_at >= self.cooldown", "now - self._opened_at > self.cooldown"),
        ("logic: success does not reset failures", "        self._failures = 0\n        self._state = \"closed\"", "        self._state = \"closed\""),
        ("logic: half-open failure keeps old open time", "            self._state = \"open\"\n            self._opened_at = now\n            return", "            self._state = \"open\"\n            return"),
        ("logic: half-open failure closes", "            self._state = \"open\"\n            self._opened_at = now\n            return", "            self._state = \"closed\"\n            return"),
        ("logic: open allows calls", 'return self.state(now) != "open"', "return True"),
        ("logic: success does not close half-open", '        self._failures = 0\n        self._state = "closed"', "        self._failures = 0"),
        ("boundary: threshold 1 rejected", "if threshold < 1 or cooldown <= 0:", "if threshold < 2 or cooldown <= 0:"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_order_fsm", diff="medium",
    spec="Write tests for the `Order` state machine in order.py.",
    files={"order.py": r'''
class InvalidTransition(Exception):
    pass


class Order:
    """Order lifecycle. States: 'new', 'paid', 'shipped', 'delivered', 'cancelled'.
    pay(): new -> paid. ship(): paid -> shipped. deliver(): shipped -> delivered.
    cancel(): allowed from 'new' and 'paid' only -> cancelled (a paid order is refunded: refunded becomes True).
    Any other transition raises InvalidTransition and leaves the state unchanged. `history` lists every state
    entered, starting with 'new'."""

    def __init__(self):
        self.state = "new"
        self.refunded = False
        self.history = ["new"]

    def _go(self, allowed, target):
        if self.state not in allowed:
            raise InvalidTransition(f"{self.state} -> {target}")
        self.state = target
        self.history.append(target)

    def pay(self):
        self._go(("new",), "paid")

    def ship(self):
        self._go(("paid",), "shipped")

    def deliver(self):
        self._go(("shipped",), "delivered")

    def cancel(self):
        was_paid = self.state == "paid"
        self._go(("new", "paid"), "cancelled")
        self.refunded = was_paid
'''},
    tests=r'''
from order import Order, InvalidTransition


def raises(fn):
    try:
        fn()
    except InvalidTransition:
        return True
    return False


o = Order()
assert o.state == "new" and o.history == ["new"] and o.refunded is False
assert raises(o.ship) and raises(o.deliver)
assert o.state == "new" and o.history == ["new"]
o.pay()
assert o.state == "paid"
assert raises(o.pay) and raises(o.deliver)
o.ship()
assert o.state == "shipped"
assert raises(o.cancel) and raises(o.pay) and raises(o.ship)
assert o.state == "shipped" and o.refunded is False
o.deliver()
assert o.state == "delivered"
assert raises(o.cancel) and raises(o.deliver) and raises(o.pay) and raises(o.ship)
assert o.history == ["new", "paid", "shipped", "delivered"]

o = Order()
o.cancel()
assert o.state == "cancelled" and o.refunded is False
assert raises(o.pay) and raises(o.cancel) and raises(o.ship) and raises(o.deliver)
assert o.history == ["new", "cancelled"]

o = Order()
o.pay()
o.cancel()
assert o.state == "cancelled" and o.refunded is True
assert o.history == ["new", "paid", "cancelled"]
assert issubclass(InvalidTransition, Exception)
''',
    muts=[
        ("logic: cancel from shipped allowed", '("new", "paid"), "cancelled"', '("new", "paid", "shipped"), "cancelled"'),
        ("logic: cancel from paid forbidden", '("new", "paid"), "cancelled"', '("new",), "cancelled"'),
        ("logic: refund flag missing", "self.refunded = was_paid", "self.refunded = False"),
        ("logic: refund on every cancel", "self.refunded = was_paid", "self.refunded = True"),
        ("logic: ship from new allowed", '(("paid",), "shipped")', '(("new", "paid"), "shipped")'),
        ("logic: history not recorded", "        self.history.append(target)\n", ""),
        ("logic: state changed before check", "        if self.state not in allowed:\n            raise InvalidTransition(f\"{self.state} -> {target}\")\n        self.state = target", "        self.state = target\n        if self.state not in allowed:\n            raise InvalidTransition(f\"{self.state} -> {target}\")"),
        ("logic: deliver from paid allowed", '(("shipped",), "delivered")', '(("paid", "shipped"), "delivered")'),
    ][:8],
    weak=8,
))

TASKS.append(dict(
    id="qa_ttl_cache", diff="medium",
    spec="Write tests for the `TTLCache` class in ttl.py. Time is passed in explicitly.",
    files={"ttl.py": r'''
class TTLCache:
    """Key-value cache whose entries expire. set(key, value, now, ttl=None) stores a value that is valid for
    `ttl` seconds (default_ttl when None); an entry is expired when now >= set_time + ttl (so it is still valid
    one instant before). ttl <= 0 -> ValueError. get(key, now, default=None) returns the value or default if
    missing/expired (expired entries are removed). size(now) counts only live entries. ttl=0 is NOT allowed."""

    def __init__(self, default_ttl):
        if default_ttl <= 0:
            raise ValueError("ttl must be positive")
        self.default_ttl = default_ttl
        self._d = {}

    def set(self, key, value, now, ttl=None):
        ttl = self.default_ttl if ttl is None else ttl
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        self._d[key] = (value, now + ttl)

    def get(self, key, now, default=None):
        item = self._d.get(key)
        if item is None:
            return default
        value, expires = item
        if now >= expires:
            del self._d[key]
            return default
        return value

    def size(self, now):
        return sum(1 for _, exp in self._d.values() if now < exp)
'''},
    tests=r'''
from ttl import TTLCache

c = TTLCache(10)
assert c.get("a", 0) is None
assert c.get("a", 0, "dflt") == "dflt"
c.set("a", 1, now=0)
assert c.get("a", 0) == 1
assert c.get("a", 9.99) == 1
assert c.get("a", 10) is None
assert c.get("a", 10, "gone") == "gone"
assert c.get("a", 5) is None
c.set("a", 1, 0)
c.set("b", 2, 0, ttl=3)
assert c.size(0) == 2
assert c.size(2.9) == 2
assert c.size(3) == 1
assert c.size(10) == 0
c.set("a", 5, 20)
c.set("a", 6, 25, ttl=1)
assert c.get("a", 25.5) == 6
assert c.get("a", 26) is None
c.set("z", 0, 0)
assert c.get("z", 1) == 0
c.set("n", None, 0)
assert c.get("n", 1, "missing") is None
c.set("f", "", 0)
assert c.get("f", 1, "missing") == ""
for ttl in (0, -1):
    try:
        c.set("x", 1, 0, ttl=ttl)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    try:
        TTLCache(ttl)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
c2 = TTLCache(1)
c2.set("k", "v", 100)
assert c2.get("k", 100.9) == "v"
assert c2.get("k", 101) is None
''',
    muts=[
        ("boundary: expiry instant", "if now >= expires:", "if now > expires:"),
        ("boundary: size at expiry", "if now < exp)", "if now <= exp)"),
        ("logic: ttl ignored", "ttl = self.default_ttl if ttl is None else ttl", "ttl = self.default_ttl"),
        ("logic: default ttl ignores explicit 0 handling", "self.default_ttl if ttl is None else ttl", "ttl or self.default_ttl"),
        ("wrong-default: default value", "def get(self, key, now, default=None):", "def get(self, key, now, default=0):"),
        ("missing-edge-case: size counts expired", "sum(1 for _, exp in self._d.values() if now < exp)", "len(self._d)"),
        ("boundary: ttl 0 accepted on set", "        if ttl <= 0:\n            raise ValueError(\"ttl must be positive\")\n        self._d", "        if ttl < 0:\n            raise ValueError(\"ttl must be positive\")\n        self._d"),
        ("logic: falsy value treated as missing", "        if item is None:\n            return default\n        value, expires = item", "        if item is None or not item[0]:\n            return default\n        value, expires = item"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_retry_backoff", diff="medium",
    spec="Write tests for `backoff_delays(...)` and `retry(...)` in retry.py (no real sleeping: the sleep function is injected).",
    files={"retry.py": r'''
def backoff_delays(attempts, base=1.0, factor=2.0, cap=None):
    """List of delays between attempts: base * factor**i for i in range(attempts - 1), each limited to cap if
    cap is not None. attempts < 1 -> ValueError. One attempt means no delays: []."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    out = []
    for i in range(attempts - 1):
        d = base * factor ** i
        if cap is not None:
            d = min(d, cap)
        out.append(d)
    return out


def retry(fn, attempts, sleep, retry_on=(Exception,), **backoff):
    """Call fn() up to `attempts` times. If it raises an exception in retry_on, sleep for the next backoff delay and
    try again; other exceptions propagate immediately. After the last failed attempt re-raise the last exception
    without sleeping. Returns fn's result on success."""
    delays = backoff_delays(attempts, **backoff)
    for i in range(attempts):
        try:
            return fn()
        except retry_on:
            if i == attempts - 1:
                raise
            sleep(delays[i])
'''},
    tests=r'''
from retry import backoff_delays, retry

assert backoff_delays(1) == []
assert backoff_delays(2) == [1.0]
assert backoff_delays(4) == [1.0, 2.0, 4.0]
assert backoff_delays(4, base=0.5) == [0.5, 1.0, 2.0]
assert backoff_delays(4, factor=3) == [1.0, 3.0, 9.0]
assert backoff_delays(5, cap=3) == [1.0, 2.0, 3, 3]
assert backoff_delays(3, cap=100) == [1.0, 2.0]
assert backoff_delays(3, base=2, factor=1) == [2, 2]
try:
    backoff_delays(0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")


class Flaky:
    def __init__(self, fails, exc=ValueError):
        self.fails, self.calls, self.exc = fails, 0, exc

    def __call__(self):
        self.calls += 1
        if self.calls <= self.fails:
            raise self.exc("boom %d" % self.calls)
        return "ok"


slept = []
f = Flaky(2)
assert retry(f, 5, slept.append) == "ok"
assert f.calls == 3 and slept == [1.0, 2.0]

slept = []
f = Flaky(0)
assert retry(f, 3, slept.append) == "ok" and f.calls == 1 and slept == []

slept = []
f = Flaky(10)
try:
    retry(f, 3, slept.append)
except ValueError as e:
    assert str(e) == "boom 3"
else:
    raise AssertionError("expected ValueError")
assert f.calls == 3 and slept == [1.0, 2.0]

slept = []
f = Flaky(1, KeyError)
try:
    retry(f, 3, slept.append, retry_on=(ValueError,))
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
assert f.calls == 1 and slept == []

slept = []
f = Flaky(1)
assert retry(f, 2, slept.append, base=0.25) == "ok" and slept == [0.25]
f = Flaky(5)
try:
    retry(f, 1, lambda s: None)
except ValueError:
    pass
assert f.calls == 1
''',
    muts=[
        ("off-by-one: delay count", "for i in range(attempts - 1):", "for i in range(attempts):"),
        ("logic: delays linear", "d = base * factor ** i", "d = base * factor * (i + 1)"),
        ("logic: cap ignored", "d = min(d, cap)", "pass"),
        ("off-by-one: exponent start", "base * factor ** i", "base * factor ** (i + 1)"),
        ("logic: sleeps after last attempt", "            if i == attempts - 1:\n                raise\n", "            if i == attempts:\n                raise\n"),
        ("off-by-one: one attempt too few", "for i in range(attempts):\n        try:", "for i in range(attempts - 1):\n        try:"),
        ("logic: retries all exceptions", "except retry_on:", "except Exception:"),
        ("boundary: attempts 1 rejected", "if attempts < 1:", "if attempts < 2:"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_turnstile", diff="easy",
    spec="Write tests for the `Turnstile` class in turnstile.py.",
    files={"turnstile.py": r'''
class Turnstile:
    """Coin-operated turnstile. Starts locked. coin(): unlocks (if already unlocked the extra coin is counted
    as 'wasted'). push(): if unlocked -> lets one person pass (passed += 1) and locks again; if locked -> nothing
    happens and returns False. push() returns True when a person passed. Attributes: locked, passed, wasted."""

    def __init__(self):
        self.locked = True
        self.passed = 0
        self.wasted = 0

    def coin(self):
        if not self.locked:
            self.wasted += 1
        self.locked = False

    def push(self):
        if self.locked:
            return False
        self.passed += 1
        self.locked = True
        return True
'''},
    tests=r'''
from turnstile import Turnstile

t = Turnstile()
assert t.locked is True and t.passed == 0 and t.wasted == 0
assert t.push() is False
assert t.locked is True and t.passed == 0
t.coin()
assert t.locked is False and t.wasted == 0
assert t.push() is True
assert t.locked is True and t.passed == 1
assert t.push() is False and t.passed == 1
t.coin()
t.coin()
assert t.wasted == 1 and t.locked is False
t.coin()
assert t.wasted == 2
assert t.push() is True and t.passed == 2
assert t.push() is False
for _ in range(3):
    t.coin()
    assert t.push() is True
assert t.passed == 5 and t.wasted == 2
''',
    muts=[
        ("logic: stays unlocked after push", "        self.passed += 1\n        self.locked = True", "        self.passed += 1"),
        ("logic: push while locked passes", "        if self.locked:\n            return False\n", ""),
        ("logic: wasted coin not counted", "        if not self.locked:\n            self.wasted += 1\n", ""),
        ("logic: wasted counted always", "        if not self.locked:\n            self.wasted += 1\n", "        self.wasted += 1\n"),
        ("logic: passed not counted", "        self.passed += 1\n", ""),
        ("logic: starts unlocked", "self.locked = True\n        self.passed = 0", "self.locked = False\n        self.passed = 0"),
        ("logic: coin does not unlock", "            self.wasted += 1\n        self.locked = False", "            self.wasted += 1"),
    ],
    weak=6,
))

TASKS.append(dict(
    id="qa_traffic_light", diff="easy",
    spec="Write tests for `TrafficLight` in light.py. Durations: green 30 s, yellow 5 s, red 20 s, cycling green -> yellow -> red -> green.",
    files={"light.py": r'''
class TrafficLight:
    """Cycles green(30s) -> yellow(5s) -> red(20s) -> green ... starting at green at time 0.
    color_at(t) gives the color at t seconds since start (t >= 0, else ValueError); a color's duration is
    [start, end) so t=30 is already yellow. time_to_change(t) is the seconds until the next color change.
    cycles_completed(t) is the number of full 55 s cycles finished by t."""
    PLAN = (("green", 30), ("yellow", 5), ("red", 20))
    CYCLE = 55

    def color_at(self, t):
        if t < 0:
            raise ValueError("negative time")
        t = t % self.CYCLE
        for color, dur in self.PLAN:
            if t < dur:
                return color
            t -= dur

    def time_to_change(self, t):
        if t < 0:
            raise ValueError("negative time")
        t = t % self.CYCLE
        for _, dur in self.PLAN:
            if t < dur:
                return dur - t
            t -= dur

    def cycles_completed(self, t):
        if t < 0:
            raise ValueError("negative time")
        return int(t // self.CYCLE)
'''},
    tests=r'''
from light import TrafficLight

L = TrafficLight()
assert L.color_at(0) == "green"
assert L.color_at(29.9) == "green"
assert L.color_at(30) == "yellow"
assert L.color_at(34.9) == "yellow"
assert L.color_at(35) == "red"
assert L.color_at(54.9) == "red"
assert L.color_at(55) == "green"
assert L.color_at(55 * 10 + 31) == "yellow"
assert L.color_at(110) == "green"
assert L.time_to_change(0) == 30
assert L.time_to_change(10) == 20
assert L.time_to_change(30) == 5
assert L.time_to_change(34) == 1
assert L.time_to_change(35) == 20
assert L.time_to_change(54) == 1
assert L.time_to_change(55) == 30
assert L.time_to_change(65) == 20
assert L.cycles_completed(0) == 0
assert L.cycles_completed(54.9) == 0
assert L.cycles_completed(55) == 1
assert L.cycles_completed(110) == 2
assert L.cycles_completed(200) == 3
for fn in (L.color_at, L.time_to_change, L.cycles_completed):
    try:
        fn(-1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("boundary: green lasts through 30", "            if t < dur:\n                return color", "            if t <= dur:\n                return color"),
        ("logic: cycle length", "CYCLE = 55", "CYCLE = 50"),
        ("logic: yellow duration", '("yellow", 5)', '("yellow", 6)'),
        ("boundary: time_to_change at boundary", "            if t < dur:\n                return dur - t", "            if t <= dur:\n                return dur - t"),
        ("rounding: cycles rounded", "int(t // self.CYCLE)", "round(t / self.CYCLE)"),
        ("missing-edge-case: negative time", '        if t < 0:\n            raise ValueError("negative time")\n        t = t % self.CYCLE\n        for color', '        t = t % self.CYCLE\n        for color'),
        ("logic: red first", '(("green", 30), ("yellow", 5), ("red", 20))', '(("red", 20), ("yellow", 5), ("green", 30))'),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_job_queue", diff="hard",
    spec="Write tests for the `JobQueue` class in jobs.py.",
    files={"jobs.py": r'''
class JobQueue:
    """Job queue with retries. submit(job_id, max_attempts=3) adds a pending job (duplicate id -> ValueError;
    max_attempts < 1 -> ValueError). next_job() returns the id of the oldest pending job and marks it 'running'
    (None if nothing is pending). complete(job_id) marks a running job 'done'. fail(job_id): if attempts used
    (counting this one) < max_attempts the job goes back to the END of the pending queue, otherwise it becomes
    'dead'. complete/fail on a job that is not running -> ValueError; unknown id -> KeyError.
    status(job_id) -> 'pending' | 'running' | 'done' | 'dead' (KeyError if unknown); attempts(job_id) -> int."""

    def __init__(self):
        self._jobs = {}
        self._pending = []

    def submit(self, job_id, max_attempts=3):
        if job_id in self._jobs:
            raise ValueError("duplicate")
        if max_attempts < 1:
            raise ValueError("max_attempts")
        self._jobs[job_id] = {"status": "pending", "attempts": 0, "max": max_attempts}
        self._pending.append(job_id)

    def next_job(self):
        if not self._pending:
            return None
        jid = self._pending.pop(0)
        job = self._jobs[jid]
        job["status"] = "running"
        job["attempts"] += 1
        return jid

    def _running(self, job_id):
        job = self._jobs[job_id]
        if job["status"] != "running":
            raise ValueError("not running")
        return job

    def complete(self, job_id):
        self._running(job_id)["status"] = "done"

    def fail(self, job_id):
        job = self._running(job_id)
        if job["attempts"] < job["max"]:
            job["status"] = "pending"
            self._pending.append(job_id)
        else:
            job["status"] = "dead"

    def status(self, job_id):
        return self._jobs[job_id]["status"]

    def attempts(self, job_id):
        return self._jobs[job_id]["attempts"]
'''},
    tests=r'''
from jobs import JobQueue

q = JobQueue()
assert q.next_job() is None
q.submit("a")
q.submit("b", max_attempts=1)
assert q.status("a") == "pending" and q.attempts("a") == 0
assert q.next_job() == "a"
assert q.status("a") == "running" and q.attempts("a") == 1
assert q.next_job() == "b"
q.fail("b")
assert q.status("b") == "dead"
assert q.next_job() is None
q.fail("a")
assert q.status("a") == "pending"
assert q.next_job() == "a" and q.attempts("a") == 2
q.complete("a")
assert q.status("a") == "done"
assert q.next_job() is None

q = JobQueue()
q.submit("x", 2)
q.submit("y", 2)
assert q.next_job() == "x"
q.fail("x")
assert q.next_job() == "y"
assert q.next_job() == "x"
q.fail("x")
assert q.status("x") == "dead" and q.attempts("x") == 2
q.complete("y")

q = JobQueue()
q.submit("a", 3)
assert q.next_job() == "a"
for i in range(2):
    q.fail("a")
    assert q.status("a") == "pending"
    assert q.next_job() == "a"
q.fail("a")
assert q.status("a") == "dead" and q.attempts("a") == 3

q = JobQueue()
q.submit("p")
for fn in (q.complete, q.fail):
    try:
        fn("p")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    try:
        fn("nope")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
q.next_job()
q.complete("p")
try:
    q.fail("p")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
try:
    q.submit("p")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
try:
    q.submit("z", 0)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
try:
    q.status("zzz")
except KeyError:
    pass
else:
    raise AssertionError("expected KeyError")
''',
    muts=[
        ("boundary: attempts limit", 'job["attempts"] < job["max"]', 'job["attempts"] <= job["max"]'),
        ("ordering: retry goes to the front", "            self._pending.append(job_id)\n        else:", "            self._pending.insert(0, job_id)\n        else:"),
        ("logic: attempts not counted", '        job["attempts"] += 1\n', ""),
        ("missing-edge-case: complete on non-running", 'if job["status"] != "running":\n            raise ValueError("not running")', "if False:\n            pass"),
        ("missing-edge-case: duplicate submit", 'if job_id in self._jobs:\n            raise ValueError("duplicate")', "if False:\n            pass"),
        ("ordering: newest job first", "jid = self._pending.pop(0)", "jid = self._pending.pop()"),
        ("boundary: max_attempts 1 rejected", "if max_attempts < 1:", "if max_attempts < 2:"),
        ("logic: failed job never requeued", '            job["status"] = "pending"\n            self._pending.append(job_id)', '            job["status"] = "pending"'),
    ],
    weak=12,
))

TASKS.append(dict(
    id="qa_debounce", diff="medium",
    spec="Write tests for the `Debouncer` class in debounce.py (time passed in explicitly).",
    files={"debounce.py": r'''
class Debouncer:
    """Collapses bursts of calls. trigger(now, value) records a pending value (the latest trigger wins) and
    restarts the quiet period. poll(now) returns the pending value once at least `quiet` seconds have passed since
    the LAST trigger (then clears it), otherwise returns the sentinel NOTHING. With `max_wait` set, a pending value
    is also released when max_wait seconds have passed since the FIRST trigger of the current burst.
    quiet <= 0 -> ValueError."""

    NOTHING = object()

    def __init__(self, quiet, max_wait=None):
        if quiet <= 0:
            raise ValueError("quiet must be positive")
        self.quiet = quiet
        self.max_wait = max_wait
        self._value = self.NOTHING
        self._first = None
        self._last = None

    def trigger(self, now, value):
        if self._value is self.NOTHING:
            self._first = now
        self._value = value
        self._last = now

    def poll(self, now):
        if self._value is self.NOTHING:
            return self.NOTHING
        due = now - self._last >= self.quiet
        if self.max_wait is not None and now - self._first >= self.max_wait:
            due = True
        if not due:
            return self.NOTHING
        v, self._value = self._value, self.NOTHING
        return v
'''},
    tests=r'''
from debounce import Debouncer

N = Debouncer.NOTHING
d = Debouncer(5)
assert d.poll(0) is N
d.trigger(0, "a")
assert d.poll(4.9) is N
assert d.poll(5) == "a"
assert d.poll(6) is N
d.trigger(10, "x")
d.trigger(13, "y")
assert d.poll(17) is N
assert d.poll(18) == "y"
d.trigger(20, None)
assert d.poll(25) is None
assert d.poll(26) is N

d = Debouncer(5, max_wait=12)
d.trigger(0, 1)
d.trigger(4, 2)
d.trigger(8, 3)
assert d.poll(11.9) is N
d.trigger(11.9, 4)
assert d.poll(12) == 4
assert d.poll(13) is N
d.trigger(20, 5)
d.trigger(24, 6)
assert d.poll(24.5) is N
assert d.poll(29) == 6
d.trigger(40, "q")
assert d.poll(44.99) is N

d = Debouncer(2, max_wait=3)
d.trigger(0, "a")
d.trigger(1, "b")
d.trigger(2.5, "c")
assert d.poll(2.9) is N
assert d.poll(3) == "c"
d.trigger(10, "z")
assert d.poll(11) is N
assert d.poll(12) == "z"
for q in (0, -1):
    try:
        Debouncer(q)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("boundary: quiet boundary", "now - self._last >= self.quiet", "now - self._last > self.quiet"),
        ("logic: first trigger time reset every trigger", "        if self._value is self.NOTHING:\n            self._first = now\n", "        self._first = now\n"),
        ("logic: first value wins", "        self._value = value\n        self._last = now", "        if self._value is self.NOTHING:\n            self._value = value\n        self._last = now"),
        ("boundary: max_wait boundary", "now - self._first >= self.max_wait", "now - self._first > self.max_wait"),
        ("logic: value not cleared", "v, self._value = self._value, self.NOTHING", "v = self._value"),
        ("logic: quiet measured from first", "now - self._last >= self.quiet", "now - self._first >= self.quiet"),
        ("logic: max_wait ignored", "        if self.max_wait is not None and now - self._first >= self.max_wait:\n            due = True\n", ""),
        ("boundary: quiet 0 accepted", "if quiet <= 0:", "if quiet < 0:"),
    ],
    weak=9,
))
