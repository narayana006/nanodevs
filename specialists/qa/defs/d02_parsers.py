TASKS = []

TASKS.append(dict(
    id="qa_csv_line", diff="hard",
    spec="Write tests for `parse_csv_line(line)` in csvline.py.",
    files={"csvline.py": r'''
def parse_csv_line(line):
    """Split one CSV line into fields. Fields are separated by commas. A field may be wrapped in double quotes,
    in which case it may contain commas and a doubled quote ("") stands for one literal quote.
    Unquoted fields are returned as is (no stripping). An empty line gives [""]. An unterminated quote -> ValueError."""
    fields = []
    cur = []
    i = 0
    in_q = False
    while i < len(line):
        c = line[i]
        if in_q:
            if c == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    cur.append('"')
                    i += 1
                else:
                    in_q = False
            else:
                cur.append(c)
        elif c == '"':
            in_q = True
        elif c == ",":
            fields.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    if in_q:
        raise ValueError("unterminated quote")
    fields.append("".join(cur))
    return fields
'''},
    tests=r'''
from csvline import parse_csv_line

assert parse_csv_line("a,b,c") == ["a", "b", "c"]
assert parse_csv_line("") == [""]
assert parse_csv_line("a,,c") == ["a", "", "c"]
assert parse_csv_line(",") == ["", ""]
assert parse_csv_line("a,") == ["a", ""]
assert parse_csv_line(' a , b ') == [" a ", " b "]
assert parse_csv_line('"a,b",c') == ["a,b", "c"]
assert parse_csv_line('"say ""hi""",x') == ['say "hi"', "x"]
assert parse_csv_line('""') == [""]
assert parse_csv_line('"",x') == ["", "x"]
assert parse_csv_line('x,"y"') == ["x", "y"]
assert parse_csv_line('"a""",b') == ['a"', "b"]
for bad in ('"abc', 'a,"b', '"a""'):
    try:
        parse_csv_line(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)
''',
    muts=[
        ("missing-edge-case: doubled quote", "if i + 1 < len(line) and line[i + 1] == '\"':", "if False:"),
        ("off-by-one: doubled quote skip", "cur.append('\"')\n                    i += 1", "cur.append('\"')"),
        ("missing-edge-case: unterminated quote", 'if in_q:\n        raise ValueError("unterminated quote")', "if in_q:\n        pass"),
        ("missing-edge-case: trailing field dropped", '    fields.append("".join(cur))\n    return fields', "    if cur:\n        fields.append(\"\".join(cur))\n    return fields"),
        ("logic: fields stripped", 'fields.append("".join(cur))\n            cur = []', 'fields.append("".join(cur).strip())\n            cur = []'),
        ("logic: comma in quotes splits", "        if in_q:\n            if c", "        if in_q and c != ',':\n            if c"),
        ("exception-type", 'raise ValueError("unterminated quote")', 'raise RuntimeError("unterminated quote")'),
    ],
    weak=6,
    regress=[dict(mut=3, report="parse_csv_line('\"abc') silently returns ['abc'] instead of raising ValueError for the unterminated quote.", test="from csvline import parse_csv_line\ntry:\n    parse_csv_line('\"abc')\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError('no error')\n")],
))

TASKS.append(dict(
    id="qa_query_string", diff="medium",
    spec="Write tests for `parse_qs(qs)` and `build_qs(params)` in qs.py.",
    files={"qs.py": r'''
from urllib.parse import quote, unquote_plus


def parse_qs(qs):
    """Parse 'a=1&b=2&a=3' into {'a': ['1', '3'], 'b': ['2']}. A leading '?' is ignored. '+' and %XX are decoded.
    A pair without '=' has the value ''. Empty pairs (e.g. from '&&') are skipped. Empty input -> {}."""
    if qs.startswith("?"):
        qs = qs[1:]
    out = {}
    for part in qs.split("&"):
        if not part:
            continue
        k, _, v = part.partition("=")
        out.setdefault(unquote_plus(k), []).append(unquote_plus(v))
    return out


def build_qs(params):
    """Inverse of parse_qs for a dict of lists; keys sorted, values kept in order, spaces become %20."""
    pairs = []
    for k in sorted(params):
        for v in params[k]:
            pairs.append(quote(k, safe="") + "=" + quote(str(v), safe=""))
    return "&".join(pairs)
'''},
    tests=r'''
from qs import parse_qs, build_qs

assert parse_qs("a=1&b=2") == {"a": ["1"], "b": ["2"]}
assert parse_qs("a=1&a=3") == {"a": ["1", "3"]}
assert parse_qs("?a=1") == {"a": ["1"]}
assert parse_qs("") == {}
assert parse_qs("?") == {}
assert parse_qs("a") == {"a": [""]}
assert parse_qs("a=") == {"a": [""]}
assert parse_qs("a=1&&b=2&") == {"a": ["1"], "b": ["2"]}
assert parse_qs("a=hello+world") == {"a": ["hello world"]}
assert parse_qs("a=%41%2B") == {"a": ["A+"]}
assert parse_qs("q=a=b") == {"q": ["a=b"]}
assert parse_qs("x%20y=1") == {"x y": ["1"]}
assert parse_qs("a=2&a=1") == {"a": ["2", "1"]}

assert build_qs({"b": ["2"], "a": ["1"]}) == "a=1&b=2"
assert build_qs({"a": ["1", "3"]}) == "a=1&a=3"
assert build_qs({}) == ""
assert build_qs({"a": ["x y"]}) == "a=x%20y"
assert build_qs({"a": ["1&2"]}) == "a=1%262"
assert build_qs({"k k": [5]}) == "k%20k=5"
assert build_qs({"a": ["b", "a"]}) == "a=b&a=a"
''',
    muts=[
        ("missing-edge-case: leading ?", 'if qs.startswith("?"):\n        qs = qs[1:]\n', ""),
        ("missing-edge-case: empty pairs", "if not part:\n            continue\n", ""),
        ("logic: plus not decoded", "unquote_plus(v)", "unquote(v)"),
        ("logic: only last value kept", "out.setdefault(unquote_plus(k), []).append(unquote_plus(v))", "out[unquote_plus(k)] = [unquote_plus(v)]"),
        ("logic: partition on last =", 'part.partition("=")', 'part.rpartition("=")'),
        ("ordering: keys not sorted", "for k in sorted(params):", "for k in params:"),
        ("logic: ampersand unescaped", 'quote(str(v), safe="")', 'quote(str(v), safe="&")'),
        ("ordering: values sorted", "for v in params[k]:", "for v in sorted(params[k]):"),
    ],
    weak=6,
))

TASKS.append(dict(
    id="qa_semver", diff="medium",
    spec="Write tests for `parse_version(s)` and `compare(a, b)` in semver.py.",
    files={"semver.py": r'''
def parse_version(s):
    """'1.2.3' or '1.2.3-beta.1' -> (1, 2, 3, ('beta', 1)); no prerelease -> empty tuple.
    A leading 'v' is allowed. Must have exactly three numeric parts, else ValueError."""
    if s.startswith("v"):
        s = s[1:]
    core, _, pre = s.partition("-")
    parts = core.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError("bad version: %r" % s)
    pre_t = tuple(int(x) if x.isdigit() else x for x in pre.split(".")) if pre else ()
    return int(parts[0]), int(parts[1]), int(parts[2]), pre_t


def compare(a, b):
    """-1, 0 or 1. Numeric parts compare numerically; a version with a prerelease is LOWER than the same
    version without; prerelease identifiers compare pairwise (numbers < strings, numbers numerically)."""
    x, y = parse_version(a), parse_version(b)
    if x[:3] != y[:3]:
        return -1 if x[:3] < y[:3] else 1
    px, py = x[3], y[3]
    if px == py:
        return 0
    if not px:
        return 1
    if not py:
        return -1
    for i, j in zip(px, py):
        if i == j:
            continue
        if isinstance(i, int) != isinstance(j, int):
            return -1 if isinstance(i, int) else 1
        return -1 if i < j else 1
    return -1 if len(px) < len(py) else 1
'''},
    tests=r'''
from semver import parse_version, compare

assert parse_version("1.2.3") == (1, 2, 3, ())
assert parse_version("v1.2.3") == (1, 2, 3, ())
assert parse_version("1.2.3-beta.1") == (1, 2, 3, ("beta", 1))
assert parse_version("0.0.10-rc") == (0, 0, 10, ("rc",))
for bad in ("1.2", "1.2.3.4", "a.b.c", "1.2.x", ""):
    try:
        parse_version(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)

assert compare("1.2.3", "1.2.3") == 0
assert compare("1.2.3", "1.2.4") == -1
assert compare("1.3.0", "1.2.9") == 1
assert compare("2.0.0", "1.9.9") == 1
assert compare("1.10.0", "1.9.0") == 1
assert compare("1.0.0-alpha", "1.0.0") == -1
assert compare("1.0.0", "1.0.0-alpha") == 1
assert compare("1.0.0-alpha", "1.0.0-beta") == -1
assert compare("1.0.0-beta.2", "1.0.0-beta.11") == -1
assert compare("1.0.0-alpha.1", "1.0.0-alpha") == 1
assert compare("1.0.0-alpha", "1.0.0-alpha.1") == -1
assert compare("1.0.0-1", "1.0.0-alpha") == -1
assert compare("1.0.0-alpha", "1.0.0-1") == 1
assert compare("v1.0.0", "1.0.0") == 0
assert compare("1.0.0-rc.1", "1.0.0-rc.1") == 0
''',
    muts=[
        ("logic: numeric parts compared as strings", "return int(parts[0]), int(parts[1]), int(parts[2]), pre_t", "return parts[0].zfill(1), int(parts[1]), int(parts[2]), pre_t"),
        ("logic: prerelease higher than release", "    if not px:\n        return 1\n    if not py:\n        return -1\n", "    if not px:\n        return -1\n    if not py:\n        return 1\n"),
        ("missing-edge-case: v prefix", 'if s.startswith("v"):\n        s = s[1:]\n', ""),
        ("missing-edge-case: extra part accepted", "len(parts) != 3", "len(parts) < 3"),
        ("logic: numeric identifier compared as string", "int(x) if x.isdigit() else x", "x"),
        ("comparison: shorter prerelease higher", "return -1 if len(px) < len(py) else 1", "return 1 if len(px) < len(py) else -1"),
        ("logic: numbers rank above strings", "return -1 if isinstance(i, int) else 1", "return 1 if isinstance(i, int) else -1"),
        ("exception-type", 'raise ValueError("bad version: %r" % s)', 'raise TypeError("bad version: %r" % s)'),
    ],
    weak=7,
))

TASKS.append(dict(
    id="qa_ini_parser", diff="hard",
    spec="Write tests for `parse_ini(text)` in ini.py.",
    files={"ini.py": r'''
def parse_ini(text):
    """Parse INI text into {section: {key: value}}.
    - '[name]' starts a section; keys before any section go into the section ''.
    - 'key = value' (whitespace around key and value is stripped); a line without '=' -> ValueError.
    - lines starting with '#' or ';' (after stripping) and blank lines are ignored.
    - a repeated key in the same section: the last value wins.
    - a section header must end with ']' else ValueError; the same section may appear again (keys merge)."""
    result = {}
    cur = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line[0] == "[":
            if not line.endswith("]"):
                raise ValueError("bad section: %r" % line)
            cur = line[1:-1].strip()
            result.setdefault(cur, {})
            continue
        if "=" not in line:
            raise ValueError("missing '=': %r" % line)
        k, _, v = line.partition("=")
        result.setdefault(cur, {})[k.strip()] = v.strip()
    return result
'''},
    tests=r'''
from ini import parse_ini

assert parse_ini("") == {}
assert parse_ini("[a]\nx=1\ny = 2") == {"a": {"x": "1", "y": "2"}}
assert parse_ini("top=1\n[s]\nk=v") == {"": {"top": "1"}, "s": {"k": "v"}}
assert parse_ini("# c\n; c2\n\n[s]\n  # indented\nk=v") == {"s": {"k": "v"}}
assert parse_ini("[s]\nk=1\nk=2") == {"s": {"k": "2"}}
assert parse_ini("[s]\nk=1\n[t]\nk=2\n[s]\nj=3") == {"s": {"k": "1", "j": "3"}, "t": {"k": "2"}}
assert parse_ini("[empty]") == {"empty": {}}
assert parse_ini("[ spaced ]\n k = v w ") == {"spaced": {"k": "v w"}}
assert parse_ini("[s]\nurl=a=b") == {"s": {"url": "a=b"}}
assert parse_ini("[s]\nk=") == {"s": {"k": ""}}
assert parse_ini("[s]\r\nk=v\r\n") == {"s": {"k": "v"}}
for bad in ("[s", "[s]\njunk", "justtext"):
    try:
        parse_ini(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)
''',
    muts=[
        ("missing-edge-case: ; comments", 'line[0] in "#;"', 'line[0] == "#"'),
        ("missing-edge-case: # comments", 'line[0] in "#;"', 'line[0] == ";"'),
        ("logic: first duplicate wins", "[k.strip()] = v.strip()", ".setdefault(k.strip(), v.strip())"),
        ("logic: section re-open resets", "result.setdefault(cur, {})\n            continue", "result[cur] = {}\n            continue"),
        ("logic: values not stripped", "= v.strip()", "= v"),
        ("logic: split on last =", 'line.partition("=")', 'line.rpartition("=")'),
        ("missing-edge-case: bad section accepted", 'if not line.endswith("]"):\n                raise ValueError("bad section: %r" % line)', "if False:\n                pass"),
        ("missing-edge-case: empty section dropped", "cur = line[1:-1].strip()\n            result.setdefault(cur, {})", "cur = line[1:-1].strip()"),
        ("exception-type", """raise ValueError("missing '=': %r" % line)""", """raise KeyError("missing '=': %r" % line)"""),
    ][:8],
    weak=5,
))

TASKS.append(dict(
    id="qa_luhn", diff="easy",
    spec="Write tests for `luhn_valid(number)` and `luhn_check_digit(partial)` in luhn.py.",
    files={"luhn.py": r'''
def luhn_valid(number):
    """True if the digit string passes the Luhn checksum. Spaces and dashes are ignored.
    Any other non-digit character, or fewer than 2 digits, -> False."""
    s = number.replace(" ", "").replace("-", "")
    if len(s) < 2 or not s.isdigit():
        return False
    total = 0
    for i, ch in enumerate(reversed(s)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def luhn_check_digit(partial):
    """Return the digit (0-9) to append to the digit string `partial` to make it Luhn-valid."""
    for d in range(10):
        if luhn_valid(partial + str(d)):
            return d
    raise ValueError("bad input")
'''},
    tests=r'''
from luhn import luhn_valid, luhn_check_digit

assert luhn_valid("4539 1488 0343 6467") is True
assert luhn_valid("4539148803436467") is True
assert luhn_valid("4539-1488-0343-6467") is True
assert luhn_valid("4539148803436468") is False
assert luhn_valid("79927398713") is True
assert luhn_valid("79927398710") is False
assert luhn_valid("0000") is True
assert luhn_valid("18") is True
assert luhn_valid("") is False
assert luhn_valid("0") is False
assert luhn_valid("5") is False
assert luhn_valid("7992739871x") is False
assert luhn_valid("59") is True
assert luhn_valid("92") is False
assert luhn_check_digit("7992739871") == 3
assert luhn_check_digit("453914880343646") == 7
assert luhn_check_digit("1") == 8
assert luhn_check_digit("0") == 0
''',
    muts=[
        ("off-by-one: doubling parity", "if i % 2 == 1:", "if i % 2 == 0:"),
        ("logic: no subtract 9", "            if d > 9:\n                d -= 9\n", ""),
        ("boundary: doubled 10", "if d > 9:", "if d > 10:"),
        ("boundary: single digit accepted", "len(s) < 2", "len(s) < 1"),
        ("missing-edge-case: dashes kept", '.replace("-", "")', ""),
        ("logic: processes digits left to right", "enumerate(reversed(s))", "enumerate(s)"),
        ("logic: empty digits", "not s.isdigit()", "False"),
    ],
    weak=7,
))

TASKS.append(dict(
    id="qa_ipv4", diff="medium",
    spec="Write tests for `is_ipv4(s)` and `ip_to_int(s)` in ipv4.py.",
    files={"ipv4.py": r'''
def is_ipv4(s):
    """True for dotted-quad IPv4 addresses: exactly four decimal parts 0-255, digits only, no leading zeros
    (except '0' itself), no whitespace or signs."""
    parts = s.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        if not p or not p.isascii() or not p.isdigit():
            return False
        if len(p) > 1 and p[0] == "0":
            return False
        if int(p) > 255:
            return False
    return True


def ip_to_int(s):
    """'1.2.3.4' -> 16909060 (big-endian). Invalid address -> ValueError."""
    if not is_ipv4(s):
        raise ValueError("invalid ip")
    n = 0
    for p in s.split("."):
        n = n * 256 + int(p)
    return n
'''},
    tests=r'''
from ipv4 import is_ipv4, ip_to_int

for ok in ("0.0.0.0", "255.255.255.255", "1.2.3.4", "192.168.1.1", "10.0.0.255", "1.10.100.0"):
    assert is_ipv4(ok) is True, ok
for bad in ("", "1.2.3", "1.2.3.4.5", "256.1.1.1", "1.1.1.256", "01.2.3.4", "1.2.3.04", "1..3.4", "a.b.c.d",
            "1.2.3.-4", " 1.2.3.4", "1.2.3.4 ", "+1.2.3.4", "1,2,3,4", "1.2.3.", "٣.1.1.1"):
    assert is_ipv4(bad) is False, bad
assert ip_to_int("0.0.0.0") == 0
assert ip_to_int("1.2.3.4") == 16909060
assert ip_to_int("255.255.255.255") == 4294967295
assert ip_to_int("0.0.1.0") == 256
assert ip_to_int("10.0.0.1") == 167772161
try:
    ip_to_int("1.2.3")
except ValueError:
    pass
else:
    raise AssertionError("expected ValueError")
''',
    muts=[
        ("boundary: 255 rejected", "int(p) > 255", "int(p) >= 255"),
        ("boundary: 256 accepted", "int(p) > 255", "int(p) > 256"),
        ("missing-edge-case: leading zeros", 'if len(p) > 1 and p[0] == "0":\n            return False\n', ""),
        ("missing-edge-case: zero rejected as leading zero", 'len(p) > 1 and p[0] == "0"', 'p[0] == "0"'),
        ("missing-edge-case: extra parts", "len(parts) != 4", "len(parts) < 4"),
        ("missing-edge-case: unicode digits", "not p.isascii() or ", ""),
        ("logic: byte order", "n = n * 256 + int(p)", "n = n + int(p) * 256"),
        ("logic: accumulation base", "n = n * 256 + int(p)", "n = n * 255 + int(p)"),
    ],
    weak=4,
))

TASKS.append(dict(
    id="qa_brackets", diff="medium",
    spec="Write tests for `is_balanced(s)` and `first_mismatch(s)` in brackets.py.",
    files={"brackets.py": r'''
PAIRS = {")": "(", "]": "[", "}": "{"}


def is_balanced(s):
    """True when every (, [, { is closed by the matching bracket in the right order. Other characters are ignored."""
    return first_mismatch(s) == -1


def first_mismatch(s):
    """Index of the first character that makes the string unbalanced, or -1 when balanced.
    A closer with no opener or the wrong opener is reported at its own index;
    unclosed openers left at the end are reported at the index of the OLDEST (outermost) unclosed opener."""
    stack = []
    for i, c in enumerate(s):
        if c in "([{":
            stack.append((c, i))
        elif c in PAIRS:
            if not stack or stack[-1][0] != PAIRS[c]:
                return i
            stack.pop()
    return stack[0][1] if stack else -1
'''},
    tests=r'''
from brackets import is_balanced, first_mismatch

assert is_balanced("") is True
assert is_balanced("()") is True
assert is_balanced("([]{})") is True
assert is_balanced("a(b)c[d]{e}") is True
assert is_balanced("(") is False
assert is_balanced(")") is False
assert is_balanced("(]") is False
assert is_balanced("([)]") is False
assert is_balanced("((") is False
assert is_balanced("())") is False
assert is_balanced("{[()]}") is True
assert is_balanced("}{") is False
assert first_mismatch("()") == -1
assert first_mismatch("") == -1
assert first_mismatch(")") == 0
assert first_mismatch("ab)") == 2
assert first_mismatch("(]") == 1
assert first_mismatch("([)]") == 2
assert first_mismatch("((") == 0
assert first_mismatch("a(b(c") == 1
assert first_mismatch("())(") == 2
assert first_mismatch("{[}") == 2
''',
    muts=[
        ("missing-edge-case: closer without opener", "if not stack or stack[-1][0] != PAIRS[c]:", "if stack and stack[-1][0] != PAIRS[c]:"),
        ("logic: wrong opener accepted", "stack[-1][0] != PAIRS[c]", "False"),
        ("ordering: newest unclosed reported", "return stack[0][1] if stack else -1", "return stack[-1][1] if stack else -1"),
        ("logic: braces ignored", 'c in "([{"', 'c in "(["'),
        ("off-by-one: index reported", "                return i\n", "                return i + 1\n"),
        ("logic: is_balanced inverted", "== -1", "!= -1"),
        ("missing-edge-case: leftover openers", "return stack[0][1] if stack else -1", "return -1"),
    ],
    weak=8,
))

TASKS.append(dict(
    id="qa_hex_color", diff="easy",
    spec="Write tests for `parse_hex_color(s)` and `to_hex(rgb)` in color.py.",
    files={"color.py": r'''
def parse_hex_color(s):
    """'#ff8800' or '#f80' (case-insensitive, '#' required) -> (255, 136, 0). Anything else -> ValueError."""
    if not s.startswith("#"):
        raise ValueError("missing #")
    h = s[1:]
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError("bad length")
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError("bad digits")


def to_hex(rgb):
    """(255, 136, 0) -> '#ff8800' (lower case, zero padded). Components outside 0..255 -> ValueError."""
    if len(rgb) != 3 or any(not 0 <= c <= 255 for c in rgb):
        raise ValueError("bad rgb")
    return "#" + "".join("%02x" % c for c in rgb)
'''},
    tests=r'''
from color import parse_hex_color, to_hex

assert parse_hex_color("#ff8800") == (255, 136, 0)
assert parse_hex_color("#FF8800") == (255, 136, 0)
assert parse_hex_color("#f80") == (255, 136, 0)
assert parse_hex_color("#000") == (0, 0, 0)
assert parse_hex_color("#0a0B0c") == (10, 11, 12)
assert parse_hex_color("#123") == (17, 34, 51)
for bad in ("ff8800", "#ff88", "#ff88000", "#gg0000", "#", "", "#12345", "#ffff"):
    try:
        parse_hex_color(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)
assert to_hex((255, 136, 0)) == "#ff8800"
assert to_hex((0, 0, 0)) == "#000000"
assert to_hex((1, 2, 3)) == "#010203"
assert to_hex((255, 255, 255)) == "#ffffff"
assert to_hex((10, 11, 12)) == "#0a0b0c"
for bad in ((256, 0, 0), (-1, 0, 0), (0, 0, 300), (1, 2)):
    try:
        to_hex(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % (bad,))
''',
    muts=[
        ("missing-edge-case: short form", "    if len(h) == 3:\n        h = \"\".join(c * 2 for c in h)\n", ""),
        ("logic: short form expansion", "c * 2 for c in h", "c + \"0\" for c in h"),
        ("missing-edge-case: # not required", 'if not s.startswith("#"):\n        raise ValueError("missing #")\n    h = s[1:]', 'h = s.lstrip("#")'),
        ("boundary: 255 rejected", "not 0 <= c <= 255", "not 0 <= c < 255"),
        ("boundary: 0 rejected", "not 0 <= c <= 255", "not 0 < c <= 255"),
        ("logic: no zero padding", '"%02x" % c', '"%x" % c'),
        ("logic: upper case output", '"%02x" % c', '"%02X" % c'),
        ("exception-type", 'raise ValueError("bad digits")', 'raise TypeError("bad digits")'),
    ],
    weak=5,
))

TASKS.append(dict(
    id="qa_kv_tokenizer", diff="hard",
    spec="Write tests for `tokenize(line)` in tokens.py.",
    files={"tokens.py": r'''
def tokenize(line):
    """Split a command line into tokens, shell-like:
    - tokens are separated by runs of spaces/tabs;
    - single quotes keep everything literally; double quotes keep spaces and allow \\" and \\\\ escapes;
    - outside quotes a backslash escapes the next character;
    - quotes next to other text join into one token ('a"b c"d' -> 'ab cd'); an empty quoted string is an empty token;
    - an unterminated quote or a trailing backslash -> ValueError."""
    tokens = []
    cur = []
    has = False
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c in " \t":
            if has:
                tokens.append("".join(cur))
                cur, has = [], False
        elif c == "\\":
            if i + 1 >= n:
                raise ValueError("trailing backslash")
            i += 1
            cur.append(line[i])
            has = True
        elif c == "'":
            j = line.find("'", i + 1)
            if j < 0:
                raise ValueError("unterminated quote")
            cur.append(line[i + 1:j])
            has = True
            i = j
        elif c == '"':
            i += 1
            while True:
                if i >= n:
                    raise ValueError("unterminated quote")
                if line[i] == '"':
                    break
                if line[i] == "\\" and i + 1 < n and line[i + 1] in '"\\':
                    i += 1
                cur.append(line[i])
                i += 1
            has = True
        else:
            cur.append(c)
            has = True
        i += 1
    if has:
        tokens.append("".join(cur))
    return tokens
'''},
    tests=r'''
from tokens import tokenize

assert tokenize("") == []
assert tokenize("   ") == []
assert tokenize("a b c") == ["a", "b", "c"]
assert tokenize("  a \t b  ") == ["a", "b"]
assert tokenize("echo 'hello world'") == ["echo", "hello world"]
assert tokenize('echo "hello world"') == ["echo", "hello world"]
assert tokenize("a\\ b") == ["a b"]
assert tokenize('a"b c"d') == ["ab cd"]
assert tokenize("''") == [""]
assert tokenize('x "" y') == ["x", "", "y"]
assert tokenize("'a\\b'") == ["a\\b"]
assert tokenize('"a\\"b"') == ['a"b']
assert tokenize('"a\\\\b"') == ["a\\b"]
assert tokenize('"a\\nb"') == ["a\\nb"]
assert tokenize("'it''s'") == ["its"]
assert tokenize('"a" \'b\'') == ["a", "b"]
assert tokenize("a\\\\") == ["a\\"]
for bad in ("'abc", '"abc', "abc\\", '"abc\\"'):
    try:
        tokenize(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)
''',
    muts=[
        ("missing-edge-case: empty quoted token", "            has = True\n            i = j\n", "            has = bool(line[i + 1:j])\n            i = j\n"),
        ("missing-edge-case: trailing token", "    if has:\n        tokens.append", "    if False:\n        tokens.append"),
        ("missing-edge-case: unterminated single quote", 'if j < 0:\n                raise ValueError("unterminated quote")', "if j < 0:\n                j = n"),
        ("missing-edge-case: trailing backslash", 'if i + 1 >= n:\n                raise ValueError("trailing backslash")', "if i + 1 >= n:\n                break"),
        ("logic: double-quote escapes", "line[i + 1] in '\"\\\\'", "line[i + 1] in '\"'"),
        ("logic: tab not separator", 'c in " \\t"', 'c == " "'),
        ("logic: tokens not joined", "            if has:\n                tokens.append", "            if has or True:\n                tokens.append"),
        ("exception-type", 'raise ValueError("trailing backslash")', 'raise IndexError("trailing backslash")'),
    ],
    weak=9,
))

TASKS.append(dict(
    id="qa_isbn", diff="medium",
    spec="Write tests for `isbn10_valid(s)` and `isbn13_valid(s)` in isbn.py.",
    files={"isbn.py": r'''
def _clean(s):
    return s.replace("-", "").replace(" ", "")


def isbn10_valid(s):
    """ISBN-10: 10 chars, first nine digits, last digit or 'X' (=10, upper case only). Hyphens/spaces ignored.
    Valid when sum(digit_i * (10 - i)) for i = 0..9 is divisible by 11."""
    s = _clean(s)
    if len(s) != 10 or not s[:9].isdigit():
        return False
    last = s[9]
    if last == "X":
        v = 10
    elif last.isdigit():
        v = int(last)
    else:
        return False
    total = sum(int(c) * (10 - i) for i, c in enumerate(s[:9])) + v
    return total % 11 == 0


def isbn13_valid(s):
    """ISBN-13: 13 digits; sum of digits weighted 1,3,1,3,... divisible by 10. Hyphens/spaces ignored."""
    s = _clean(s)
    if len(s) != 13 or not s.isdigit():
        return False
    return sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(s)) % 10 == 0
'''},
    tests=r'''
from isbn import isbn10_valid, isbn13_valid

assert isbn10_valid("0306406152") is True
assert isbn10_valid("0-306-40615-2") is True
assert isbn10_valid("0 306 40615 2") is True
assert isbn10_valid("080442957X") is True
assert isbn10_valid("0804429570") is False
assert isbn10_valid("080442957x") is False
assert isbn10_valid("0306406153") is False
assert isbn10_valid("030640615") is False
assert isbn10_valid("03064061522") is False
assert isbn10_valid("X306406152") is False
assert isbn10_valid("") is False
assert isbn10_valid("030640615Y") is False
assert isbn10_valid("0000000000") is True
assert isbn13_valid("9780306406157") is True
assert isbn13_valid("978-0-306-40615-7") is True
assert isbn13_valid("9780306406158") is False
assert isbn13_valid("978030640615") is False
assert isbn13_valid("97803064061570") is False
assert isbn13_valid("978030640615X") is False
assert isbn13_valid("9783161484100") is True
assert isbn13_valid("0000000000000") is True
assert isbn13_valid("9780306406147") is False
''',
    muts=[
        ("off-by-one: weights", "int(c) * (10 - i)", "int(c) * (9 - i)"),
        ("missing-edge-case: X check digit", '    if last == "X":\n        v = 10\n    elif', "    if False:\n        v = 10\n    elif"),
        ("logic: lower x accepted", 'if last == "X":', 'if last in "Xx":'),
        ("logic: X value", "v = 10", "v = 11"),
        ("logic: isbn13 weights swapped", "(1 if i % 2 == 0 else 3)", "(3 if i % 2 == 0 else 1)"),
        ("logic: isbn13 modulus", "% 10 == 0", "% 11 == 0"),
        ("missing-edge-case: hyphens", '.replace("-", "")', ""),
        ("boundary: length not checked", "len(s) != 13 or", ""),
    ],
    weak=7,
))

TASKS.append(dict(
    id="qa_email_check", diff="medium",
    spec="Write tests for `is_valid_email(s)` in emailcheck.py.",
    files={"emailcheck.py": r'''
import string

LOCAL_OK = set(string.ascii_letters + string.digits + "._%+-")


def is_valid_email(s):
    """Simplified email check. Exactly one '@'. Local part: 1-64 chars from letters, digits and ._%+-, must not
    start or end with '.', and must not contain '..'. Domain: at least two dot-separated labels, each 1-63 chars of
    letters, digits and '-', not starting or ending with '-'; the last label (TLD) is at least 2 letters long."""
    if s.count("@") != 1:
        return False
    local, domain = s.split("@")
    if not 1 <= len(local) <= 64:
        return False
    if any(c not in LOCAL_OK for c in local):
        return False
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    for lab in labels:
        if not 1 <= len(lab) <= 63:
            return False
        if lab.startswith("-") or lab.endswith("-"):
            return False
        if any(c not in string.ascii_letters + string.digits + "-" for c in lab):
            return False
    tld = labels[-1]
    return len(tld) >= 2 and tld.isalpha()
'''},
    tests=r'''
from emailcheck import is_valid_email

for ok in ("a@b.co", "john.doe@example.com", "user+tag@mail.example.org", "a_b%c-d@x.io", "x@sub.domain.example.com",
           "a" * 64 + "@example.com", "1@2.ab", "a@b-c.com"):
    assert is_valid_email(ok) is True, ok
for bad in ("", "a", "a@", "@b.com", "a@b", "a@@b.com", "a@b@c.com", ".a@b.com", "a.@b.com", "a..b@c.com",
            "a" * 65 + "@example.com", "a b@c.com", "a@-b.com", "a@b-.com", "a@b.c", "a@b.c1", "a@b..com",
            "a@.com", "a@b.com.", "a@b!.com", "a@" + "x" * 64 + ".com", "a,b@c.com"):
    assert is_valid_email(bad) is False, bad
assert is_valid_email("a@" + "x" * 63 + ".com") is True
assert is_valid_email("a@b.c" + "o" * 5) is True
''',
    muts=[
        ("boundary: local 64", "not 1 <= len(local) <= 64", "not 1 <= len(local) < 64"),
        ("boundary: local 65 accepted", "not 1 <= len(local) <= 64", "not 1 <= len(local) <= 65"),
        ("missing-edge-case: empty local", "not 1 <= len(local)", "not 0 <= len(local)"),
        ("missing-edge-case: double dot", ' or ".." in local', ""),
        ("missing-edge-case: leading dot", 'local.startswith(".") or ', ""),
        ("boundary: tld length", "len(tld) >= 2", "len(tld) >= 1"),
        ("missing-edge-case: tld digits", "and tld.isalpha()", ""),
        ("missing-edge-case: label hyphen", 'lab.startswith("-") or lab.endswith("-")', 'lab.startswith("-")'),
        ("boundary: label 63", "not 1 <= len(lab) <= 63", "not 1 <= len(lab) < 63"),
    ][:8],
    weak=2,
))
