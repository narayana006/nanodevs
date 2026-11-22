"""Templates 1: off-by-one, inverted conditions, missing checks."""
TEMPLATES = {}


def T(name, difficulty, title, base, good, tests, defects, params):
    TEMPLATES[name] = (dict(difficulty=difficulty, title=title, base=base, good=good, tests=tests, defects=defects), params)


# ---------------------------------------------------------------- moving average (suspicious-but-correct loop bounds)
T("moving_avg", "medium", "Compute @F@ with a running sum instead of re-summing every window",
  base={"@M@.py": '''
def @F@(xs, k):
    if k <= 0:
        raise ValueError("k must be positive")
    return [sum(xs[i:i + k]) / k for i in range(len(xs) - k + 1)]
'''},
  good={"@M@.py": '''
def @F@(xs, k):
    if k <= 0:
        raise ValueError("k must be positive")
    if k > len(xs):
        return []
    total = sum(xs[:k])
    out = [total / k]
    for i in range(k, len(xs)):
        total += xs[i] - xs[i - k]
        out.append(total / k)
    return out
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_basic():
    assert m.@F@([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]

def test_full_window():
    assert m.@F@([2, 4, 6], 3) == [4.0]

def test_last_window_included():
    assert m.@F@([1, 1, 1, 1, 9], 2)[-1] == 5.0

def test_k_larger_than_input():
    assert m.@F@([1, 2], 5) == []

def test_bad_k():
    try:
        m.@F@([1, 2], 0)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
''',
  defects=[
      dict(file="@M@.py", old="    for i in range(k, len(xs)):", new="    for i in range(k, len(xs) - 1):", category="off_by_one",
           test="test_last_window_included", why="The loop stops one element early (len(xs) - 1), so the final window average is never appended."),
      dict(file="@M@.py", old="    if k > len(xs):\n        return []\n    total = sum(xs[:k])\n", new="    total = sum(xs[:k])\n", category="missing_check",
           test="test_k_larger_than_input", why="The k > len(xs) guard was dropped, so a window larger than the input returns a bogus single average instead of []."),
  ],
  params=[dict(M="smoothing", F="moving_avg", _use=[0]), dict(M="rolling", F="rolling_mean", _use=[0, 1], _diff="medium")])

# ---------------------------------------------------------------- pagination
T("paginate", "easy", "Expose pagination metadata via @F@_meta and reuse it in @F@",
  base={"@M@.py": '''
def @F@(items, page, size=10):
    """1-based page of items."""
    return items[(page - 1) * size: page * size]
'''},
  good={"@M@.py": '''
def @F@_meta(items, page, size=10):
    if page < 1 or size < 1:
        raise ValueError("page and size must be >= 1")
    start = (page - 1) * size
    return {"items": items[start:start + size], "page": page, "has_next": start + size < len(items)}


def @F@(items, page, size=10):
    """1-based page of items."""
    return @F@_meta(items, page, size)["items"]
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_page_two():
    assert m.@F@(list(range(1, 11)), 2, 3) == [4, 5, 6]

def test_first_page():
    assert m.@F@(list(range(1, 11)), 1, 4) == [1, 2, 3, 4]

def test_last_partial():
    assert m.@F@(list(range(1, 11)), 4, 3) == [10]

def test_has_next_exact_end():
    needs(m, "@F@_meta")
    assert m.@F@_meta(list(range(6)), 2, 3)["has_next"] is False

def test_has_next_true():
    needs(m, "@F@_meta")
    assert m.@F@_meta(list(range(7)), 2, 3)["has_next"] is True
''',
  defects=[
      dict(file="@M@.py", old="    start = (page - 1) * size\n", new="    start = page * size\n", category="off_by_one",
           test="test_page_two", why="start should be (page - 1) * size for 1-based pages; page * size skips the first page entirely."),
      dict(file="@M@.py", old="start + size < len(items)}", new="start + size <= len(items)}", category="off_by_one",
           test="test_has_next_exact_end", why="has_next uses <=, so the last full page reports a next page that does not exist."),
  ],
  params=[dict(M="paging", F="paginate", _use=[0]), dict(M="listing", F="get_page", _use=[1])])

# ---------------------------------------------------------------- chunks with overlap
T("chunks", "medium", "Add an overlap option to @F@",
  base={"@M@.py": '''
def @F@(xs, n):
    if n < 1:
        raise ValueError("n must be >= 1")
    return [xs[i:i + n] for i in range(0, len(xs), n)]
'''},
  good={"@M@.py": '''
def @F@(xs, n, overlap=0):
    if n < 1:
        raise ValueError("n must be >= 1")
    if not 0 <= overlap < n:
        raise ValueError("overlap must be in [0, n)")
    step = n - overlap
    out = []
    for i in range(0, len(xs), step):
        out.append(xs[i:i + n])
        if i + n >= len(xs):
            break
    return out
'''},
  tests='''
import @M@ as m
from _rt import needs_param

def test_plain():
    assert m.@F@([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

def test_exact_multiple():
    assert m.@F@([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

def test_overlap():
    needs_param(m.@F@, "overlap")
    assert m.@F@([1, 2, 3, 4, 5], 3, overlap=1) == [[1, 2, 3], [3, 4, 5]]

def test_overlap_tail():
    needs_param(m.@F@, "overlap")
    assert m.@F@([1, 2, 3, 4, 5, 6], 3, overlap=1) == [[1, 2, 3], [3, 4, 5], [5, 6]]

def test_empty():
    assert m.@F@([], 3) == []

def test_overlap_validation():
    needs_param(m.@F@, "overlap")
    try:
        m.@F@([1, 2, 3], 2, overlap=2)
    except ValueError as e:
        assert "overlap" in str(e)
        return
    raise AssertionError
''',
  defects=[
      dict(file="@M@.py", old="        if i + n >= len(xs):", new="        if i + n > len(xs):", category="off_by_one",
           test="test_overlap", why="The early-exit test should be >=; with > an already-complete final chunk is followed by an extra duplicate/trailing chunk."),
      dict(file="@M@.py", old="    if not 0 <= overlap < n:", new="    if not 0 <= overlap <= n:", category="off_by_one", test="test_overlap_validation",
           why="overlap == n gives step 0 (infinite loop / ZeroDivision-like failure); the upper bound must be exclusive."),
  ],
  params=[dict(M="batching", F="chunk", _use=[0]), dict(M="windows", F="split_windows", _use=[1], _diff="easy")])

# ---------------------------------------------------------------- lower-bound binary search
T("lower_bound", "medium", "Replace linear scan in @F@ with binary search",
  base={"@M@.py": '''
def @F@(a, target):
    """Index of the first element >= target (len(a) if none). `a` is sorted."""
    for i, v in enumerate(a):
        if v >= target:
            return i
    return len(a)
'''},
  good={"@M@.py": '''
def @F@(a, target):
    """Index of the first element >= target (len(a) if none). `a` is sorted."""
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo
'''},
  tests='''
import @M@ as m

def test_found():
    assert m.@F@([1, 3, 5, 7], 5) == 2

def test_between():
    assert m.@F@([1, 3, 5, 7], 4) == 2

def test_beyond_end():
    assert m.@F@([1, 3, 5, 7], 9) == 4

def test_before_start():
    assert m.@F@([1, 3, 5, 7], 0) == 0

def test_duplicates_first():
    assert m.@F@([1, 2, 2, 2, 3], 2) == 1

def test_empty():
    assert m.@F@([], 1) == 0
''',
  defects=[
      dict(file="@M@.py", old="    lo, hi = 0, len(a)\n", new="    lo, hi = 0, len(a) - 1\n", category="off_by_one", test="test_beyond_end",
           why="hi must start at len(a) (exclusive upper bound); len(a) - 1 can never return len(a) for targets beyond the end."),
      dict(file="@M@.py", old="        if a[mid] < target:", new="        if a[mid] <= target:", category="inverted_condition", test="test_duplicates_first",
           why="Using <= moves past equal elements, so the returned index is the first element > target, not the first >= target."),
  ],
  params=[dict(M="search", F="lower_bound", _use=[0]), dict(M="sortedlist", F="first_at_least", _use=[0, 1], _diff="hard")])

# ---------------------------------------------------------------- truncate
T("truncate", "easy", "@F@: guarantee the result (with ellipsis) never exceeds the limit",
  base={"@M@.py": '''
def @F@(text, limit):
    if len(text) > limit:
        return text[:limit]
    return text
'''},
  good={"@M@.py": '''
def @F@(text, limit, ellipsis="..."):
    if len(text) <= limit:
        return text
    if limit <= len(ellipsis):
        return ellipsis[:limit]
    return text[:limit - len(ellipsis)] + ellipsis
'''},
  tests='''
import @M@ as m
from _rt import needs_param

def test_short_unchanged():
    assert m.@F@("hello", 10) == "hello"

def test_exact_length_unchanged():
    assert m.@F@("hello", 5) == "hello"

def test_truncated_fits():
    needs_param(m.@F@, "ellipsis")
    out = m.@F@("hello world", 8)
    assert out == "hello..." and len(out) == 8

def test_tiny_limit():
    needs_param(m.@F@, "ellipsis")
    assert m.@F@("hello world", 2) == ".."
''',
  defects=[
      dict(file="@M@.py", old="    if len(text) <= limit:", new="    if len(text) < limit:", category="off_by_one", test="test_exact_length_unchanged",
           why="Text exactly at the limit is now truncated with an ellipsis although it already fits (< should be <=)."),
      dict(file="@M@.py", old="    return text[:limit - len(ellipsis)] + ellipsis", new="    return text[:limit] + ellipsis", category="off_by_one",
           test="test_truncated_fits", why="Keeping `limit` characters and then appending the ellipsis makes the result longer than the limit."),
  ],
  params=[dict(M="textutil", F="truncate", _use=[0]), dict(M="shorten", F="clip_text", _use=[1])])

# ---------------------------------------------------------------- inclusive day range
T("day_range", "easy", "Add @F@ helper and use it in @G@",
  base={"@M@.py": '''
def @G@(start, end):
    """Number of days in [start, end] (day numbers, inclusive)."""
    return end - start + 1
'''},
  good={"@M@.py": '''
def @F@(start, end):
    """All day numbers in [start, end], inclusive. Empty when end < start."""
    return list(range(start, end + 1))


def @G@(start, end):
    """Number of days in [start, end] (day numbers, inclusive)."""
    return len(@F@(start, end))
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_count():
    assert m.@G@(3, 5) == 3

def test_count_single_day():
    assert m.@G@(4, 4) == 1

def test_range_inclusive():
    needs(m, "@F@")
    assert m.@F@(3, 5) == [3, 4, 5]

def test_range_empty():
    needs(m, "@F@")
    assert m.@F@(5, 3) == []
''',
  defects=[
      dict(file="@M@.py", old="    return list(range(start, end + 1))", new="    return list(range(start, end))", category="off_by_one", test="test_count",
           why="range(start, end) excludes the end day; the contract (and @G@) is inclusive, so every count is now one too small."),
  ],
  params=[dict(M="calendar_util", F="days_in", G="count_days"), dict(M="booking_dates", F="nights", G="night_count")])

# ---------------------------------------------------------------- discount rules
T("discount", "easy", "Support bulk discount on top of the member discount",
  base={"@M@.py": '''
def @F@(price, qty, member):
    total = price * qty
    if member:
        total = total * 0.9
    return round(total, 2)
'''},
  good={"@M@.py": '''
BULK_QTY = @BULK@


def @F@(price, qty, member):
    total = price * qty
    rate = 0.0
    if member:
        rate += 0.10
    if qty >= BULK_QTY:
        rate += 0.05
    return round(total * (1 - rate), 2)
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_member():
    assert m.@F@(10, 2, True) == 18.0

def test_non_member_pays_full():
    assert m.@F@(10, 2, False) == 20.0

def test_bulk_boundary():
    needs(m, "BULK_QTY")
    assert m.@F@(10, @BULK@, False) == round(10 * @BULK@ * 0.95, 2)

def test_below_bulk():
    assert m.@F@(10, @BULK@ - 1, False) == 10 * (@BULK@ - 1)

def test_member_and_bulk():
    needs(m, "BULK_QTY")
    assert m.@F@(10, @BULK@, True) == round(10 * @BULK@ * 0.85, 2)
''',
  defects=[
      dict(file="@M@.py", old="    if member:\n        rate += 0.10", new="    if not member:\n        rate += 0.10", category="inverted_condition", test="test_non_member_pays_full",
           line_offset=0, why="The member discount condition is inverted: non-members get the discount and members do not."),
      dict(file="@M@.py", old="    if qty >= BULK_QTY:", new="    if qty > BULK_QTY:", category="off_by_one", test="test_bulk_boundary",
           why="The bulk discount should apply at qty == BULK_QTY (>=), the boundary quantity is excluded by >."),
  ],
  params=[dict(M="pricing", F="final_price", BULK=10, _use=[0]), dict(M="checkout", F="order_total", BULK=25, _use=[1])])

# ---------------------------------------------------------------- permission check
T("can_edit", "medium", "Allow editors to edit unlocked documents",
  base={"@M@.py": '''
class Doc:
    def __init__(self, owner, locked=False):
        self.owner = owner
        self.locked = locked


def can_edit(user, doc):
    return user == doc.owner
'''},
  good={"@M@.py": '''
class Doc:
    def __init__(self, owner, editors=(), locked=False):
        self.owner = owner
        self.editors = set(editors)
        self.locked = locked


def can_edit(user, doc):
    if user == doc.owner:
        return True
    return user in doc.editors and not doc.locked
'''},
  tests='''
import @M@ as m
from _rt import needs_param

def test_owner():
    assert m.can_edit("ann", m.Doc("ann")) is True

def test_stranger():
    assert not m.can_edit("bob", m.Doc("ann"))

def test_editor_unlocked():
    needs_param(m.Doc, "editors")
    assert m.can_edit("bob", m.Doc("ann", editors=["bob"]))

def test_editor_locked():
    needs_param(m.Doc, "editors")
    assert not m.can_edit("bob", m.Doc("ann", editors=["bob"], locked=True))

def test_owner_locked_still_edits():
    assert m.can_edit("ann", m.Doc("ann", locked=True))
''',
  defects=[
      dict(file="@M@.py", old="user in doc.editors and not doc.locked", new="user in doc.editors and doc.locked", category="inverted_condition", test="test_editor_unlocked",
           why="The lock test is inverted: editors can only edit locked documents and are blocked on unlocked ones."),
      dict(file="@M@.py", old="    if user == doc.owner:\n        return True", new="    if user != doc.owner:\n        return True", category="inverted_condition", test="test_stranger",
           why="`!=` lets every non-owner edit and rejects the owner."),
  ],
  params=[dict(M="perms", _use=[0]), dict(M="acl", _use=[1], _diff="easy")])

# ---------------------------------------------------------------- retry decision
T("should_retry", "medium", "Centralise HTTP retry policy in @F@",
  base={"@M@.py": '''
def @F@(status):
    return status >= 500
'''},
  good={"@M@.py": '''
MAX_ATTEMPTS = @MAXA@


def @F@(status, attempt=1):
    """Retry server errors and 429, never other client errors, at most MAX_ATTEMPTS attempts in total."""
    if attempt >= MAX_ATTEMPTS:
        return False
    if status == 429:
        return True
    return status >= 500
'''},
  tests='''
import @M@ as m
from _rt import needs

def test_5xx_retried():
    assert m.@F@(503) is True

def test_4xx_not_retried():
    assert m.@F@(404) is False

def test_ok_not_retried():
    assert m.@F@(200) is False

def test_429_retried():
    needs(m, "MAX_ATTEMPTS")
    assert m.@F@(429, 1) is True

def test_attempt_cap():
    needs(m, "MAX_ATTEMPTS")
    assert m.@F@(429, @MAXA@) is False
    assert m.@F@(429, @MAXA@ + 1) is False
''',
  defects=[
      dict(file="@M@.py", old="    return status >= 500\n", new="    return status < 500\n", category="inverted_condition", test="test_5xx_retried",
           line_offset=0, why="The final comparison is inverted: client errors and successes are retried while server errors are not."),
      dict(file="@M@.py", old="    if attempt >= MAX_ATTEMPTS:", new="    if attempt > MAX_ATTEMPTS:", category="off_by_one", test="test_attempt_cap",
           why="With > the policy allows MAX_ATTEMPTS + 1 attempts; it should stop when attempt >= MAX_ATTEMPTS."),
  ],
  params=[dict(M="retry_policy", F="should_retry", MAXA=3, _use=[1]), dict(M="http_retry", F="retryable", MAXA=5, _use=[0, 1], _diff="hard")])
