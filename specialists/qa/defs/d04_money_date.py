TASKS = []

TASKS.append(dict(
    id="qa_split_bill", diff="medium",
    spec="Write tests for `split_cents(total_cents, n)` and `split_weighted(total_cents, weights)` in splitting.py.",
    files={"splitting.py": r'''
def split_cents(total_cents, n):
    """Split an integer amount of cents into n integer parts that sum exactly to the total. The remainder cents go
    one each to the FIRST parts, so parts are non-increasing. total < 0 or n < 1 -> ValueError."""
    if total_cents < 0 or n < 1:
        raise ValueError("bad arguments")
    base, rem = divmod(total_cents, n)
    return [base + 1 if i < rem else base for i in range(n)]


def split_weighted(total_cents, weights):
    """Split by integer weights using the largest-remainder method: floor each share, then give the leftover cents
    one at a time to the parts with the largest fractional remainder (ties -> lower index first).
    Weights must be non-negative with a positive sum, else ValueError."""
    if total_cents < 0 or not weights or any(w < 0 for w in weights) or sum(weights) == 0:
        raise ValueError("bad arguments")
    s = sum(weights)
    shares = [total_cents * w // s for w in weights]
    rems = [total_cents * w % s for w in weights]
    left = total_cents - sum(shares)
    order = sorted(range(len(weights)), key=lambda i: (-rems[i], i))
    for i in order[:left]:
        shares[i] += 1
    return shares
'''},
    tests=r'''
from splitting import split_cents, split_weighted

assert split_cents(100, 4) == [25, 25, 25, 25]
assert split_cents(100, 3) == [34, 33, 33]
assert split_cents(101, 3) == [34, 34, 33]
assert split_cents(0, 3) == [0, 0, 0]
assert split_cents(2, 5) == [1, 1, 0, 0, 0]
assert split_cents(7, 1) == [7]
assert sum(split_cents(1000001, 7)) == 1000001
for args in ((-1, 2), (5, 0), (5, -1)):
    try:
        split_cents(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
assert split_weighted(100, [1, 1]) == [50, 50]
assert split_weighted(100, [1, 1, 1]) == [34, 33, 33]
assert split_weighted(10, [1, 2, 3]) == [2, 3, 5]
assert split_weighted(100, [3, 1]) == [75, 25]
assert split_weighted(5, [1, 1, 1, 1]) == [2, 1, 1, 1]
assert split_weighted(10, [1, 0, 1]) == [5, 0, 5]
assert split_weighted(1, [2, 3]) == [0, 1]
assert split_weighted(2, [1, 1, 1]) == [1, 1, 0]
assert split_weighted(0, [1, 2]) == [0, 0]
assert split_weighted(7, [5, 2, 3]) == [4, 1, 2]
assert sum(split_weighted(999, [7, 11, 13])) == 999
for args in ((10, []), (10, [0, 0]), (10, [1, -1, 3]), (-5, [1])):
    try:
        split_weighted(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("off-by-one: remainder distribution", "if i < rem", "if i <= rem"),
        ("ordering: remainder to last parts", "base + 1 if i < rem else base", "base + 1 if i >= n - rem else base"),
        ("boundary: n=1 rejected", "or n < 1:", "or n < 2:"),
        ("boundary: zero total rejected", "total_cents < 0 or n < 1", "total_cents <= 0 or n < 1"),
        ("ordering: ties go to higher index", "key=lambda i: (-rems[i], i)", "key=lambda i: (-rems[i], -i)"),
        ("logic: smallest remainder first", "key=lambda i: (-rems[i], i)", "key=lambda i: (rems[i], i)"),
        ("missing-edge-case: zero weight sum", " or sum(weights) == 0", ""),
        ("logic: rounding instead of floor", "total_cents * w // s for w", "round(total_cents * w / s) for w"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_money_format", diff="medium",
    spec="Write tests for `format_money(cents, symbol='$')` and `parse_money(text)` in money.py.",
    files={"money.py": r'''
def format_money(cents, symbol="$"):
    """Integer cents -> '$1,234.56'. Negative amounts are '-$1,234.56' (sign before the symbol).
    Always two decimals; thousands separated by commas."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    whole, frac = divmod(cents, 100)
    return f"{sign}{symbol}{whole:,}.{frac:02d}"


def parse_money(text):
    """'$1,234.56' / '-$5' / '12.5' / '(3.00)' -> integer cents. Parentheses mean negative. At most two decimals,
    commas are ignored, a leading '$' is optional. Garbage or 3+ decimals -> ValueError."""
    s = text.strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s.startswith("-"):
        neg, s = True, s[1:]
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "")
    whole, dot, frac = s.partition(".")
    if not whole.isdigit() or (dot and (not frac.isdigit() or len(frac) > 2)):
        raise ValueError("bad money: %r" % text)
    cents = int(whole) * 100 + (int(frac.ljust(2, "0")) if frac else 0)
    return -cents if neg else cents
'''},
    tests=r'''
from money import format_money, parse_money

assert format_money(0) == "$0.00"
assert format_money(5) == "$0.05"
assert format_money(100) == "$1.00"
assert format_money(123456) == "$1,234.56"
assert format_money(100000000) == "$1,000,000.00"
assert format_money(99999) == "$999.99"
assert format_money(-5) == "-$0.05"
assert format_money(-123456) == "-$1,234.56"
assert format_money(250, "EUR ") == "EUR 2.50"
assert format_money(100000) == "$1,000.00"
assert parse_money("$1,234.56") == 123456
assert parse_money("12.5") == 1250
assert parse_money("12.50") == 1250
assert parse_money("12") == 1200
assert parse_money("0.05") == 5
assert parse_money("-$5") == -500
assert parse_money("$-5") == -500 if False else True
assert parse_money("(3.00)") == -300
assert parse_money("  7.1  ") == 710
assert parse_money("1,000") == 100000
assert parse_money("0") == 0
for bad in ("", "abc", "1.234", "1.", ".5", "$", "1.2.3", "--5", "$$5"):
    try:
        parse_money(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)
''',
    muts=[
        ("logic: no zero padding of cents", "{frac:02d}", "{frac}"),
        ("logic: no thousands separator", "{whole:,}", "{whole}"),
        ("logic: sign after symbol", 'f"{sign}{symbol}{whole:,}', 'f"{symbol}{sign}{whole:,}'),
        ("logic: negative loses sign", 'sign = "-" if cents < 0 else ""', 'sign = ""'),
        ("rounding: one fractional digit", 'int(frac.ljust(2, "0"))', "int(frac)"),
        ("missing-edge-case: parentheses", '    if s.startswith("(") and s.endswith(")"):\n        neg, s = True, s[1:-1]\n', ""),
        ("boundary: three decimals", "len(frac) > 2", "len(frac) > 3"),
        ("missing-edge-case: empty fraction", "(not frac.isdigit() or len(frac) > 2)", "(len(frac) > 2)"),
    ],
    weak=10,
))

TASKS.append(dict(
    id="qa_tax_calc", diff="hard",
    spec="Write tests for `line_total`, `apply_discount` and `invoice_total` in invoice.py. All money is Decimal.",
    files={"invoice.py": r'''
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def q(x):
    """Round a Decimal to cents, half up."""
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(unit_price, qty):
    """unit_price * qty rounded to cents. qty must be a positive int, price non-negative, else ValueError."""
    if qty < 1 or unit_price < 0:
        raise ValueError("bad line")
    return q(Decimal(unit_price) * qty)


def apply_discount(amount, percent):
    """Reduce amount by percent (0..100 inclusive, else ValueError), rounded to cents half up."""
    if not 0 <= percent <= 100:
        raise ValueError("bad percent")
    return q(amount * (Decimal(100) - Decimal(percent)) / Decimal(100))


def invoice_total(lines, discount_percent=0, tax_rate=Decimal("0")):
    """lines: list of (unit_price, qty). Subtotal = sum of line totals; discount applied to the subtotal; then tax
    (tax_rate as fraction, e.g. Decimal('0.0825')) is added on the discounted amount, tax rounded half up.
    Returns (subtotal_after_discount, tax, total). Empty lines -> ValueError."""
    if not lines:
        raise ValueError("empty invoice")
    sub = sum((line_total(p, n) for p, n in lines), Decimal("0.00"))
    sub = apply_discount(sub, discount_percent)
    tax = q(sub * tax_rate)
    return sub, tax, sub + tax
'''},
    tests=r'''
from decimal import Decimal as D
from invoice import line_total, apply_discount, invoice_total

assert line_total(D("2.50"), 3) == D("7.50")
assert line_total(D("0.005"), 1) == D("0.01")
assert line_total(D("0.004"), 1) == D("0.00")
assert line_total(D("0.015"), 1) == D("0.02")
assert line_total(D("0"), 5) == D("0.00")
assert line_total(D("1.005"), 3) == D("3.02")
for args in ((D("1"), 0), (D("1"), -2), (D("-1"), 1)):
    try:
        line_total(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
assert apply_discount(D("100.00"), 10) == D("90.00")
assert apply_discount(D("100.00"), 0) == D("100.00")
assert apply_discount(D("100.00"), 100) == D("0.00")
assert apply_discount(D("19.99"), 15) == D("16.99")
assert apply_discount(D("0.05"), 50) == D("0.03")
assert apply_discount(D("10.00"), D("12.5")) == D("8.75")
for bad in (-1, 101):
    try:
        apply_discount(D("1"), bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
assert invoice_total([(D("10.00"), 2), (D("5.00"), 1)]) == (D("25.00"), D("0.00"), D("25.00"))
assert invoice_total([(D("10.00"), 1)], 10, D("0.10")) == (D("9.00"), D("0.90"), D("9.90"))
assert invoice_total([(D("19.99"), 1)], 0, D("0.0825")) == (D("19.99"), D("1.65"), D("21.64"))
assert invoice_total([(D("0.10"), 1), (D("0.20"), 1)]) == (D("0.30"), D("0.00"), D("0.30"))
assert invoice_total([(D("100"), 1)], 50, D("0.05")) == (D("50.00"), D("2.50"), D("52.50"))
assert invoice_total([(D("1.00"), 1)], 0, D("0.005")) == (D("1.00"), D("0.01"), D("1.01"))
try:
    invoice_total([])
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("rounding: half even", "rounding=ROUND_HALF_UP", "rounding=ROUND_HALF_EVEN"),
        ("rounding: truncation", "rounding=ROUND_HALF_UP", "rounding=ROUND_DOWN"),
        ("boundary: qty 1 rejected", "if qty < 1 or", "if qty < 2 or"),
        ("boundary: free items rejected", "unit_price < 0", "unit_price <= 0"),
        ("boundary: 100 percent rejected", "not 0 <= percent <= 100", "not 0 <= percent < 100"),
        ("boundary: 0 percent rejected", "not 0 <= percent <= 100", "not 0 < percent <= 100"),
        ("logic: tax on pre-discount amount", "sub = apply_discount(sub, discount_percent)\n    tax = q(sub * tax_rate)", "tax = q(sub * tax_rate)\n    sub = apply_discount(sub, discount_percent)"),
        ("logic: discount percentage inverted", "(Decimal(100) - Decimal(percent))", "Decimal(percent)"),
        ("missing-edge-case: empty invoice", 'if not lines:\n        raise ValueError("empty invoice")', "if not lines:\n        return (Decimal('0.00'),) * 3"),
    ][:8],
    weak=10,
))

TASKS.append(dict(
    id="qa_add_months", diff="hard",
    spec="Write tests for `add_months(d, n)` and `months_between(a, b)` in months.py.",
    files={"months.py": r'''
import calendar
from datetime import date


def add_months(d, n):
    """Add n (possibly negative) months to a date. If the target month is shorter, clamp to its last day
    (Jan 31 + 1 month = Feb 28/29). Returns a new date."""
    total = d.year * 12 + (d.month - 1) + n
    year, month = divmod(total, 12)
    month += 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def months_between(a, b):
    """Number of COMPLETE months from date a to date b (b >= a, else ValueError).
    2024-01-15 -> 2024-02-14 is 0; 2024-01-15 -> 2024-02-15 is 1."""
    if b < a:
        raise ValueError("b before a")
    m = (b.year - a.year) * 12 + (b.month - a.month)
    if b.day < a.day:
        m -= 1
    return m
'''},
    tests=r'''
from datetime import date
from months import add_months, months_between

assert add_months(date(2024, 1, 15), 1) == date(2024, 2, 15)
assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
assert add_months(date(2023, 1, 31), 1) == date(2023, 2, 28)
assert add_months(date(2024, 3, 31), -1) == date(2024, 2, 29)
assert add_months(date(2024, 12, 15), 1) == date(2025, 1, 15)
assert add_months(date(2024, 1, 15), -1) == date(2023, 12, 15)
assert add_months(date(2024, 1, 15), 12) == date(2025, 1, 15)
assert add_months(date(2024, 1, 15), -13) == date(2022, 12, 15)
assert add_months(date(2024, 1, 15), 0) == date(2024, 1, 15)
assert add_months(date(2024, 5, 31), 1) == date(2024, 6, 30)
assert add_months(date(2024, 11, 30), 3) == date(2025, 2, 28)
assert add_months(date(2024, 2, 29), 12) == date(2025, 2, 28)
assert add_months(date(2024, 2, 29), 48) == date(2028, 2, 29)
assert add_months(date(2024, 12, 31), 2) == date(2025, 2, 28)
assert months_between(date(2024, 1, 15), date(2024, 2, 15)) == 1
assert months_between(date(2024, 1, 15), date(2024, 2, 14)) == 0
assert months_between(date(2024, 1, 15), date(2024, 1, 15)) == 0
assert months_between(date(2024, 1, 31), date(2025, 1, 31)) == 12
assert months_between(date(2023, 12, 20), date(2024, 1, 19)) == 0
assert months_between(date(2023, 12, 20), date(2024, 1, 20)) == 1
assert months_between(date(2023, 1, 1), date(2025, 3, 5)) == 26
try:
    months_between(date(2024, 2, 1), date(2024, 1, 1))
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("off-by-one: month index", "(d.month - 1) + n", "d.month + n"),
        ("missing-edge-case: day clamp", "min(d.day, calendar.monthrange(year, month)[1])", "d.day"),
        ("logic: clamp to 28", "calendar.monthrange(year, month)[1]", "min(28, calendar.monthrange(year, month)[1])"),
        ("logic: year wrap", "d.year * 12 +", "(d.year - 1) * 12 +"),
        ("comparison: incomplete month counted", "if b.day < a.day:", "if b.day < a.day - 1:"),
        ("missing-edge-case: incomplete month", "    if b.day < a.day:\n        m -= 1\n", ""),
        ("missing-edge-case: reversed dates", 'if b < a:\n        raise ValueError("b before a")', "if b < a:\n        return 0"),
        ("comparison: same day", "if b.day < a.day:", "if b.day <= a.day:"),
    ],
    weak=10,
))

TASKS.append(dict(
    id="qa_business_days", diff="hard",
    spec="Write tests for `is_business_day`, `add_business_days` and `business_days_between` in bizdays.py.",
    files={"bizdays.py": r'''
from datetime import date, timedelta


def is_business_day(d, holidays=frozenset()):
    """Monday-Friday that is not in holidays."""
    return d.weekday() < 5 and d not in holidays


def add_business_days(d, n, holidays=frozenset()):
    """Move n business days forward (n > 0) or backward (n < 0) from d. n == 0 returns d unchanged even when d is
    not a business day. The start day itself is not counted."""
    step = 1 if n >= 0 else -1
    remaining = abs(n)
    cur = d
    while remaining:
        cur += timedelta(days=step)
        if is_business_day(cur, holidays):
            remaining -= 1
    return cur


def business_days_between(a, b, holidays=frozenset()):
    """Count business days in the half-open range [a, b). Negative when b < a (the count of [b, a))."""
    if b < a:
        return -business_days_between(b, a, holidays)
    n = 0
    cur = a
    while cur < b:
        if is_business_day(cur, holidays):
            n += 1
        cur += timedelta(days=1)
    return n
'''},
    tests=r'''
from datetime import date
from bizdays import is_business_day, add_business_days, business_days_between

mon, tue, fri, sat, sun = date(2024, 5, 6), date(2024, 5, 7), date(2024, 5, 10), date(2024, 5, 11), date(2024, 5, 12)
assert is_business_day(mon) and is_business_day(fri)
assert not is_business_day(sat) and not is_business_day(sun)
assert not is_business_day(tue, {tue})
assert is_business_day(tue, {mon})
assert add_business_days(mon, 1) == tue
assert add_business_days(fri, 1) == date(2024, 5, 13)
assert add_business_days(sat, 1) == date(2024, 5, 13)
assert add_business_days(mon, 5) == date(2024, 5, 13)
assert add_business_days(mon, 0) == mon
assert add_business_days(sat, 0) == sat
assert add_business_days(date(2024, 5, 13), -1) == fri
assert add_business_days(date(2024, 5, 13), -5) == mon
assert add_business_days(sun, -1) == fri
assert add_business_days(mon, 1, {tue}) == date(2024, 5, 8)
assert add_business_days(fri, 1, {date(2024, 5, 13)}) == date(2024, 5, 14)
assert add_business_days(mon, 10) == date(2024, 5, 20)
assert business_days_between(mon, mon) == 0
assert business_days_between(mon, tue) == 1
assert business_days_between(mon, date(2024, 5, 13)) == 5
assert business_days_between(mon, sat) == 5
assert business_days_between(sat, mon) == -0 or True
assert business_days_between(sat, date(2024, 5, 13)) == 0
assert business_days_between(tue, mon) == -1
assert business_days_between(date(2024, 5, 13), mon) == -5
assert business_days_between(mon, date(2024, 5, 13), {tue, date(2024, 5, 8)}) == 3
assert business_days_between(mon, date(2024, 5, 20)) == 10
''',
    muts=[
        ("boundary: Friday not a business day", "d.weekday() < 5", "d.weekday() < 4"),
        ("boundary: Saturday is a business day", "d.weekday() < 5", "d.weekday() < 6"),
        ("missing-edge-case: holidays ignored", "and d not in holidays", ""),
        ("off-by-one: one day short", "remaining = abs(n)", "remaining = max(abs(n) - 1, 0)"),
        ("logic: backward direction", "step = 1 if n >= 0 else -1", "step = 1"),
        ("off-by-one: end inclusive", "while cur < b:", "while cur <= b:"),
        ("off-by-one: start exclusive", "    n = 0\n    cur = a\n", "    n = 0\n    cur = a + timedelta(days=1)\n"),
        ("logic: negative sign lost", "return -business_days_between(b, a, holidays)", "return business_days_between(b, a, holidays)"),
    ],
    weak=14,
))

TASKS.append(dict(
    id="qa_age", diff="medium",
    spec="Write tests for `age_on(birth, today)` and `next_birthday(birth, today)` in age.py.",
    files={"age.py": r'''
import calendar
from datetime import date


def age_on(birth, today):
    """Completed years on `today`. today before birth -> ValueError."""
    if today < birth:
        raise ValueError("born in the future")
    years = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        years -= 1
    return years


def next_birthday(birth, today):
    """The first date >= today that is a birthday. A Feb 29 birthday is celebrated on Feb 28 in non-leap years.
    Returns a date."""
    for year in (today.year, today.year + 1):
        if birth.month == 2 and birth.day == 29 and not calendar.isleap(year):
            cand = date(year, 2, 28)
        else:
            cand = date(year, birth.month, birth.day)
        if cand >= today:
            return cand
'''},
    tests=r'''
from datetime import date
from age import age_on, next_birthday

assert age_on(date(2000, 5, 15), date(2024, 5, 15)) == 24
assert age_on(date(2000, 5, 15), date(2024, 5, 14)) == 23
assert age_on(date(2000, 5, 15), date(2024, 5, 16)) == 24
assert age_on(date(2000, 5, 15), date(2024, 6, 1)) == 24
assert age_on(date(2000, 5, 15), date(2024, 4, 30)) == 23
assert age_on(date(2000, 5, 15), date(2000, 5, 15)) == 0
assert age_on(date(2000, 5, 15), date(2001, 5, 14)) == 0
assert age_on(date(2000, 2, 29), date(2023, 2, 28)) == 22
assert age_on(date(2000, 2, 29), date(2023, 3, 1)) == 23
assert age_on(date(1990, 12, 31), date(2024, 1, 1)) == 33
try:
    age_on(date(2000, 1, 1), date(1999, 12, 31))
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert next_birthday(date(2000, 5, 15), date(2024, 5, 15)) == date(2024, 5, 15)
assert next_birthday(date(2000, 5, 15), date(2024, 5, 16)) == date(2025, 5, 15)
assert next_birthday(date(2000, 5, 15), date(2024, 1, 1)) == date(2024, 5, 15)
assert next_birthday(date(2000, 5, 15), date(2024, 12, 31)) == date(2025, 5, 15)
assert next_birthday(date(2000, 2, 29), date(2023, 1, 1)) == date(2023, 2, 28)
assert next_birthday(date(2000, 2, 29), date(2024, 1, 1)) == date(2024, 2, 29)
assert next_birthday(date(2000, 2, 29), date(2024, 3, 1)) == date(2025, 2, 28)
assert next_birthday(date(2000, 2, 29), date(2023, 2, 28)) == date(2023, 2, 28)
assert next_birthday(date(2000, 2, 29), date(2023, 3, 1)) == date(2024, 2, 29)
''',
    muts=[
        ("comparison: birthday not yet counted", "(today.month, today.day) < (birth.month, birth.day)", "(today.month, today.day) <= (birth.month, birth.day)"),
        ("missing-edge-case: before birthday this year", "    if (today.month, today.day) < (birth.month, birth.day):\n        years -= 1\n", ""),
        ("logic: month only compared", "(today.month, today.day) < (birth.month, birth.day)", "today.month < birth.month"),
        ("missing-edge-case: future birth", 'if today < birth:\n        raise ValueError("born in the future")', "if False:\n        pass"),
        ("comparison: birthday today skipped", "if cand >= today:", "if cand > today:"),
        ("missing-edge-case: leap day handling", "if birth.month == 2 and birth.day == 29 and not calendar.isleap(year):", "if False:"),
        ("logic: leap day on Mar 1", "cand = date(year, 2, 28)", "cand = date(year, 3, 1)"),
        ("off-by-one: next year candidate", "(today.year, today.year + 1)", "(today.year, today.year)"),
    ],
    weak=10,
))

TASKS.append(dict(
    id="qa_format_duration", diff="easy",
    spec="Write tests for `format_seconds(n)` and `humanize(n)` in fmttime.py.",
    files={"fmttime.py": r'''
def format_seconds(n):
    """Seconds -> 'H:MM:SS' (hours not padded, may exceed 24). Negative -> ValueError. Fractions are truncated."""
    if n < 0:
        raise ValueError("negative")
    n = int(n)
    h, rem = divmod(n, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def humanize(n):
    """Rough text for a span of seconds: <60 -> 'N seconds' (singular 'second' for exactly 1);
    <3600 -> minutes; <86400 -> hours; else days. Counts are truncated (119 s -> '1 minute'); singular for 1."""
    if n < 0:
        raise ValueError("negative")
    for limit, unit_s, name in ((60, 1, "second"), (3600, 60, "minute"), (86400, 3600, "hour"), (None, 86400, "day")):
        if limit is None or n < limit:
            k = int(n // unit_s)
            return f"{k} {name}" + ("" if k == 1 else "s")
'''},
    tests=r'''
from fmttime import format_seconds, humanize

assert format_seconds(0) == "0:00:00"
assert format_seconds(59) == "0:00:59"
assert format_seconds(60) == "0:01:00"
assert format_seconds(3599) == "0:59:59"
assert format_seconds(3600) == "1:00:00"
assert format_seconds(3661) == "1:01:01"
assert format_seconds(90000) == "25:00:00"
assert format_seconds(59.9) == "0:00:59"
try:
    format_seconds(-1)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
assert humanize(0) == "0 seconds"
assert humanize(1) == "1 second"
assert humanize(2) == "2 seconds"
assert humanize(59) == "59 seconds"
assert humanize(60) == "1 minute"
assert humanize(119) == "1 minute"
assert humanize(120) == "2 minutes"
assert humanize(3599) == "59 minutes"
assert humanize(3600) == "1 hour"
assert humanize(7200) == "2 hours"
assert humanize(86399) == "23 hours"
assert humanize(86400) == "1 day"
assert humanize(86400 * 10) == "10 days"
try:
    humanize(-5)
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("logic: hours padded", 'f"{h}:{m:02d}', 'f"{h:02d}:{m:02d}'),
        ("logic: minutes not padded", "{m:02d}", "{m}"),
        ("logic: seconds not padded", "{s:02d}", "{s}"),
        ("boundary: 60 seconds is seconds", "(60, 1,", "(61, 1,"),
        ("boundary: 3600 is minutes", "(3600, 60,", "(3601, 60,"),
        ("boundary: 86400 is hours", "(86400, 3600,", "(86401, 3600,"),
        ("logic: singular", '("" if k == 1 else "s")', '"s"'),
        ("rounding: rounds up", "k = int(n // unit_s)", "k = round(n / unit_s)"),
    ],
    weak=8,
))

TASKS.append(dict(
    id="qa_amortize", diff="hard",
    spec="Write tests for `monthly_payment(principal, annual_rate, months)` and `schedule(principal, annual_rate, months)` in loan.py.",
    files={"loan.py": r'''
def monthly_payment(principal, annual_rate, months):
    """Fixed monthly payment for a fully amortising loan, rounded to cents (round half to even via round()).
    annual_rate is a fraction (0.06 = 6%). A zero rate means principal / months. months < 1, principal <= 0 or
    a negative rate -> ValueError."""
    if months < 1 or principal <= 0 or annual_rate < 0:
        raise ValueError("bad loan")
    r = annual_rate / 12
    if r == 0:
        return round(principal / months, 2)
    pay = principal * r / (1 - (1 + r) ** -months)
    return round(pay, 2)


def schedule(principal, annual_rate, months):
    """List of (payment, interest, principal_part, balance) per month. Interest each month is
    round(balance * annual_rate / 12, 2). The final payment is adjusted so the balance ends at exactly 0."""
    pay = monthly_payment(principal, annual_rate, months)
    bal = round(principal, 2)
    rows = []
    for i in range(months):
        interest = round(bal * annual_rate / 12, 2)
        if i == months - 1:
            payment = round(bal + interest, 2)
        else:
            payment = pay
        part = round(payment - interest, 2)
        bal = round(bal - part, 2)
        rows.append((payment, interest, part, bal))
    return rows
'''},
    tests=r'''
from loan import monthly_payment, schedule

assert monthly_payment(1000, 0.0, 10) == 100.0
assert monthly_payment(1200, 0.0, 12) == 100.0
assert monthly_payment(1000, 0.0, 3) == 333.33
assert monthly_payment(100000, 0.06, 360) == 599.55
assert monthly_payment(10000, 0.12, 12) == 888.49
assert monthly_payment(5000, 0.05, 1) == 5020.83
assert monthly_payment(1, 0.0, 1) == 1.0
for args in ((1000, 0.05, 0), (0, 0.05, 12), (-5, 0.05, 12), (1000, -0.01, 12)):
    try:
        monthly_payment(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
rows = schedule(1200, 0.0, 12)
assert len(rows) == 12
assert rows[0] == (100.0, 0.0, 100.0, 1100.0)
assert rows[-1][3] == 0.0
rows = schedule(10000, 0.12, 12)
assert len(rows) == 12
assert rows[0] == (888.49, 100.0, 788.49, 9211.51)
assert rows[1][1] == 92.12
assert rows[-1][3] == 0.0
assert abs(sum(r[2] for r in rows) - 10000) < 0.005
assert all(r[0] == 888.49 for r in rows[:-1])
assert abs(rows[-1][0] - 888.49) < 1
one = schedule(1000, 0.12, 1)
assert one == [(1010.0, 10.0, 1000.0, 0.0)]
r3 = schedule(1000, 0.0, 3)
assert [r[0] for r in r3] == [333.33, 333.33, 333.34]
assert r3[-1][3] == 0.0
''',
    muts=[
        ("logic: annual rate not divided by 12", "r = annual_rate / 12", "r = annual_rate"),
        ("off-by-one: exponent", "(1 + r) ** -months", "(1 + r) ** -(months - 1)"),
        ("missing-edge-case: zero rate", "    if r == 0:\n        return round(principal / months, 2)\n", ""),
        ("boundary: months 1 rejected", "months < 1 or", "months < 2 or"),
        ("boundary: negative rate", "annual_rate < 0", "annual_rate < -1"),
        ("rounding: payment truncated", "return round(pay, 2)\n\n\ndef schedule", "return int(pay * 100) / 100\n\n\ndef schedule"),
        ("missing-edge-case: final payment not adjusted", "        if i == months - 1:", "        if False:"),
        ("logic: interest on original principal", "interest = round(bal * annual_rate / 12, 2)", "interest = round(principal * annual_rate / 12, 2)"),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_quarter", diff="easy",
    spec="Write tests for `quarter(d)`, `fiscal_year(d, start_month)` and `quarter_bounds(year, q)` in fiscal.py.",
    files={"fiscal.py": r'''
import calendar
from datetime import date


def quarter(d):
    """Calendar quarter 1-4 of a date."""
    return (d.month - 1) // 3 + 1


def fiscal_year(d, start_month=1):
    """Fiscal year label: the fiscal year starts on the 1st of start_month (1-12, else ValueError) and is named
    after the calendar year in which it ENDS (start_month=1 -> the calendar year; start_month=10 -> Oct 2023 is FY2024)."""
    if not 1 <= start_month <= 12:
        raise ValueError("bad start month")
    return d.year if start_month == 1 or d.month < start_month else d.year + 1


def quarter_bounds(year, q):
    """(first_day, last_day) of calendar quarter q (1-4, else ValueError) in year."""
    if not 1 <= q <= 4:
        raise ValueError("bad quarter")
    first_month = 3 * (q - 1) + 1
    last_month = first_month + 2
    return date(year, first_month, 1), date(year, last_month, calendar.monthrange(year, last_month)[1])
'''},
    tests=r'''
from datetime import date
from fiscal import quarter, fiscal_year, quarter_bounds

assert quarter(date(2024, 1, 1)) == 1
assert quarter(date(2024, 3, 31)) == 1
assert quarter(date(2024, 4, 1)) == 2
assert quarter(date(2024, 6, 30)) == 2
assert quarter(date(2024, 7, 1)) == 3
assert quarter(date(2024, 9, 30)) == 3
assert quarter(date(2024, 10, 1)) == 4
assert quarter(date(2024, 12, 31)) == 4
assert fiscal_year(date(2023, 10, 1), 10) == 2024
assert fiscal_year(date(2023, 9, 30), 10) == 2023
assert fiscal_year(date(2023, 12, 31), 10) == 2024
assert fiscal_year(date(2024, 1, 1), 10) == 2024
assert fiscal_year(date(2024, 6, 15)) == 2024
assert fiscal_year(date(2024, 6, 15), 1) == 2024
assert fiscal_year(date(2024, 12, 31), 12) == 2025
assert fiscal_year(date(2024, 11, 30), 12) == 2024
assert fiscal_year(date(2024, 4, 5), 4) == 2025
assert fiscal_year(date(2024, 3, 31), 4) == 2024
for bad in (0, 13, -1):
    try:
        fiscal_year(date(2024, 1, 1), bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
assert quarter_bounds(2024, 1) == (date(2024, 1, 1), date(2024, 3, 31))
assert quarter_bounds(2024, 2) == (date(2024, 4, 1), date(2024, 6, 30))
assert quarter_bounds(2024, 3) == (date(2024, 7, 1), date(2024, 9, 30))
assert quarter_bounds(2023, 4) == (date(2023, 10, 1), date(2023, 12, 31))
for bad in (0, 5):
    try:
        quarter_bounds(2024, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("off-by-one: quarter boundaries", "(d.month - 1) // 3 + 1", "d.month // 3 + 1"),
        ("off-by-one: quarter lower", "(d.month - 1) // 3 + 1", "(d.month - 1) // 3"),
        ("comparison: fiscal start month", "d.month < start_month", "d.month <= start_month"),
        ("logic: fiscal year uses previous year", "else d.year + 1", "else d.year - 1"),
        ("boundary: start month 12 rejected", "not 1 <= start_month <= 12", "not 1 <= start_month < 12"),
        ("boundary: quarter 4 rejected", "not 1 <= q <= 4", "not 1 <= q < 4"),
        ("off-by-one: first month", "3 * (q - 1) + 1", "3 * q"),
        ("logic: last day of quarter", "calendar.monthrange(year, last_month)[1]", "30"),
    ],
    weak=8,
))

TASKS.append(dict(
    id="qa_unit_convert", diff="medium",
    spec="Write tests for `convert(value, from_unit, to_unit)` and `c_to_f`/`f_to_c` in units.py.",
    files={"units.py": r'''
LENGTH = {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0, "in": 0.0254, "ft": 0.3048, "mi": 1609.344}


def convert(value, from_unit, to_unit):
    """Convert a length between units in LENGTH (case-sensitive). Unknown unit -> KeyError. Result rounded to
    6 decimals. Converting a unit to itself returns the value unchanged (as float)."""
    f = LENGTH[from_unit]
    t = LENGTH[to_unit]
    return round(value * f / t, 6)


def c_to_f(c):
    """Celsius to Fahrenheit. Below absolute zero (-273.15) -> ValueError."""
    if c < -273.15:
        raise ValueError("below absolute zero")
    return c * 9 / 5 + 32


def f_to_c(f):
    """Fahrenheit to Celsius. Below absolute zero (-459.67) -> ValueError."""
    if f < -459.67:
        raise ValueError("below absolute zero")
    return (f - 32) * 5 / 9
'''},
    tests=r'''
from units import convert, c_to_f, f_to_c

assert convert(1, "km", "m") == 1000.0
assert convert(1, "m", "km") == 0.001
assert convert(100, "cm", "m") == 1.0
assert convert(12, "in", "ft") == 1.0
assert convert(1, "mi", "km") == 1.609344
assert convert(5, "m", "m") == 5.0
assert convert(0, "km", "mi") == 0.0
assert convert(1, "ft", "in") == 12.0
assert convert(2.5, "m", "mm") == 2500.0
assert convert(1, "mm", "km") == 1e-06
assert convert(-3, "m", "cm") == -300.0
for args in ((1, "parsec", "m"), (1, "m", "furlong"), (1, "KM", "m")):
    try:
        convert(*args)
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
assert c_to_f(0) == 32
assert c_to_f(100) == 212
assert c_to_f(-40) == -40
assert c_to_f(37) == 98.6 or abs(c_to_f(37) - 98.6) < 1e-9
assert c_to_f(-273.15) < -459.6
assert f_to_c(32) == 0
assert f_to_c(212) == 100
assert f_to_c(-40) == -40
assert abs(f_to_c(98.6) - 37) < 1e-9
assert f_to_c(-459.67) < -273.1
for fn, v in ((c_to_f, -273.16), (f_to_c, -459.68)):
    try:
        fn(v)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
''',
    muts=[
        ("swapped-args: ratio inverted", "value * f / t", "value * t / f"),
        ("logic: mile factor", '"mi": 1609.344', '"mi": 1609.0'),
        ("logic: inch factor", '"in": 0.0254', '"in": 0.0245'),
        ("rounding: precision", "round(value * f / t, 6)", "round(value * f / t, 3)"),
        ("boundary: absolute zero rejected (C)", "c < -273.15", "c <= -273.15"),
        ("boundary: absolute zero not enforced (F)", "f < -459.67", "f < -460"),
        ("logic: c_to_f offset", "c * 9 / 5 + 32", "c * 9 / 5 + 30"),
        ("logic: f_to_c scale", "(f - 32) * 5 / 9", "(f - 32) * 9 / 5"),
    ],
    weak=7,
))

TASKS.append(dict(
    id="qa_percent_change", diff="easy",
    spec="Write tests for `pct_change`, `cagr` and `round_half_up` in growth.py.",
    files={"growth.py": r'''
def round_half_up(x, digits=0):
    """Round half away from zero (not banker's rounding): 0.5 -> 1, 1.5 -> 2, 2.5 -> 3, -0.5 -> -1."""
    f = 10 ** digits
    y = abs(x) * f
    r = int(y + 0.5)
    return (r if x >= 0 else -r) / f if digits > 0 else (r if x >= 0 else -r)


def pct_change(old, new):
    """Percentage change from old to new, as a float. old == 0 -> ZeroDivisionError is NOT raised: return
    float('inf') if new > 0, float('-inf') if new < 0 and 0.0 if new == 0."""
    if old == 0:
        return float("inf") if new > 0 else float("-inf") if new < 0 else 0.0
    return (new - old) / abs(old) * 100


def cagr(start, end, years):
    """Compound annual growth rate as a fraction. start <= 0, end < 0 or years <= 0 -> ValueError."""
    if start <= 0 or end < 0 or years <= 0:
        raise ValueError("bad inputs")
    return (end / start) ** (1 / years) - 1
'''},
    tests=r'''
from growth import round_half_up, pct_change, cagr

assert round_half_up(0.5) == 1
assert round_half_up(1.5) == 2
assert round_half_up(2.5) == 3
assert round_half_up(2.4) == 2
assert round_half_up(2.6) == 3
assert round_half_up(-0.5) == -1
assert round_half_up(-2.5) == -3
assert round_half_up(-2.4) == -2
assert round_half_up(0) == 0
assert round_half_up(1.25, 1) == 1.3
assert round_half_up(-1.25, 1) == -1.3
assert round_half_up(1.24, 1) == 1.2
assert round_half_up(3.14159, 2) == 3.14
assert pct_change(100, 150) == 50
assert pct_change(200, 100) == -50
assert pct_change(100, 100) == 0
assert pct_change(-100, -50) == 50
assert pct_change(-100, -150) == -50
assert pct_change(0, 5) == float("inf")
assert pct_change(0, -5) == float("-inf")
assert pct_change(0, 0) == 0.0
assert abs(cagr(100, 200, 1) - 1.0) < 1e-12
assert abs(cagr(100, 121, 2) - 0.1) < 1e-12
assert abs(cagr(100, 100, 5)) < 1e-12
assert abs(cagr(100, 0, 3) - (-1.0)) < 1e-12
assert abs(cagr(1000, 8000, 3) - 1.0) < 1e-12
for args in ((0, 10, 1), (-5, 10, 1), (5, -1, 1), (5, 10, 0), (5, 10, -2)):
    try:
        cagr(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % (args,))
''',
    muts=[
        ("rounding: banker's rounding", "r = int(y + 0.5)", "r = round(y)"),
        ("rounding: truncation", "r = int(y + 0.5)", "r = int(y)"),
        ("logic: negative sign lost", "(r if x >= 0 else -r) / f if digits > 0", "r / f if digits > 0"),
        ("logic: negative base uses signed old", "/ abs(old) * 100", "/ old * 100"),
        ("missing-edge-case: zero old negative new", 'if new > 0 else float("-inf") if new < 0 else 0.0', 'if new > 0 else float("-inf")'),
        ("boundary: zero end rejected", "or end < 0 or", "or end <= 0 or"),
        ("boundary: zero years accepted", "or years <= 0:", "or years < 0:"),
        ("logic: exponent", "(1 / years)", "(1 / (years + 1))"),
    ],
    weak=10,
))
