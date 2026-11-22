"""Stdlib-only structure checkers for HTML and CSS tasks (runs in python:3.12-slim, no network)."""
import re
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
_fails = []
_n = [0]


def ok(cond, msg):
    _n[0] += 1
    if not cond:
        _fails.append(msg)


def finish():
    for m in _fails:
        print("FAIL", m)
    print(f"{_n[0] - len(_fails)}/{_n[0]} passed")
    sys.exit(1 if _fails or _n[0] == 0 else 0)


class El:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.children, self.parts = tag, attrs, parent, [], []
    def get(self, k, d=None):
        return self.attrs.get(k, d)
    def has(self, k):
        return k in self.attrs
    def text(self):
        out = []
        for p in self.parts:
            out.append(p if isinstance(p, str) else p.text())
        return re.sub(r"\s+", " ", "".join(out)).strip()
    def walk(self):
        for c in self.children:
            yield c
            yield from c.walk()
    def find_all(self, tag=None, **attrs):
        res = []
        for e in self.walk():
            if tag and e.tag != tag:
                continue
            if all((e.attrs.get(k.replace("_", "-")) == v) if v is not True else (k.replace("_", "-") in e.attrs) for k, v in attrs.items()):
                res.append(e)
        return res
    def first(self, tag=None, **attrs):
        r = self.find_all(tag, **attrs)
        return r[0] if r else None
    def ancestors(self):
        p = self.parent
        while p:
            yield p
            p = p.parent
    def classes(self):
        return (self.attrs.get("class") or "").split()


class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = El("#root", {})
        self.cur = self.root
        self.doctype = None
    def handle_decl(self, decl):
        self.doctype = decl
    def handle_starttag(self, tag, attrs):
        e = El(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur)
        self.cur.children.append(e)
        self.cur.parts.append(e)
        if tag not in VOID:
            self.cur = e
    def handle_startendtag(self, tag, attrs):
        e = El(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur)
        self.cur.children.append(e)
        self.cur.parts.append(e)
    def handle_endtag(self, tag):
        c = self.cur
        while c is not self.root and c.tag != tag:
            c = c.parent
        if c is not self.root:
            self.cur = c.parent
    def handle_data(self, data):
        if self.cur.tag not in ("script", "style"):
            self.cur.parts.append(data)


class Doc:
    def __init__(self, src):
        p = _P()
        p.feed(src)
        p.close()
        self.root, self.doctype, self.src = p.root, p.doctype, src
    def all(self, tag=None, **attrs):
        return self.root.find_all(tag, **attrs)
    def first(self, tag=None, **attrs):
        return self.root.first(tag, **attrs)
    def by_id(self, i):
        return self.root.first(id=i)
    def ids(self):
        return [e.attrs["id"] for e in self.root.walk() if "id" in e.attrs]
    def label_text(self, el):
        """Accessible-name text for a form control from <label for>, wrapping <label>, aria-label or aria-labelledby."""
        i = el.get("id")
        if i:
            for l in self.all("label"):
                if l.get("for") == i:
                    return l.text()
        for a in el.ancestors():
            if a.tag == "label":
                return a.text()
        if el.get("aria-label"):
            return el.get("aria-label")
        if el.get("aria-labelledby"):
            return " ".join((self.by_id(x).text() if self.by_id(x) else "") for x in el.get("aria-labelledby").split()).strip()
        return ""
    def name_of(self, el):
        """Rough accessible name for buttons/links: aria-label, text, img alt, title."""
        if el.get("aria-label"):
            return el.get("aria-label").strip()
        t = el.text()
        if t:
            return t
        for im in el.find_all("img"):
            if im.get("alt"):
                return im.get("alt").strip()
        return (el.get("title") or "").strip()
    def headings(self):
        return [(int(e.tag[1]), e.text()) for e in self.root.walk() if re.fullmatch(r"h[1-6]", e.tag)]


# ---------------------------------------------------------------- CSS
def _norm_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def norm_media(m):
    m = _norm_ws(m.lower())
    m = re.sub(r"\s*:\s*", ":", m)
    m = re.sub(r"\(\s+", "(", m)
    m = re.sub(r"\s+\)", ")", m)
    return m


def norm_val(v):
    v = _norm_ws(v.lower())
    v = re.sub(r"\s*,\s*", ",", v)
    return v


def _split_top(s, sep):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


class Rule:
    def __init__(self, ctx, sels, decls, order):
        self.ctx, self.sels, self.decls, self.order = ctx, sels, decls, order


class Css:
    """Tiny CSS parser: top-level rules plus nested @media/@supports. Values/selectors whitespace-normalised."""
    def __init__(self, src):
        self.rules, self.atrules = [], []
        self._parse(re.sub(r"/\*.*?\*/", "", src, flags=re.S), (), 0)
    def _parse(self, s, ctx, base):
        i, n = 0, len(s)
        while i < n:
            j = s.find("{", i)
            if j == -1:
                break
            semi = s.find(";", i)
            if semi != -1 and semi < j and s[i:semi].strip().startswith("@"):
                i = semi + 1
                continue
            pre = s[i:j].strip()
            d, k = 1, j + 1
            while k < n and d:
                d += (s[k] == "{") - (s[k] == "}")
                k += 1
            body = s[j + 1:k - 1]
            if re.match(r"@(media|supports|layer)", pre):
                self._parse(body, ctx + (norm_media(pre) if pre.startswith("@media") else _norm_ws(pre.lower()),), base)
            elif pre.startswith("@"):
                self.atrules.append((_norm_ws(pre.lower()), body))
            else:
                decls = {}
                for d_ in _split_top(body, ";"):
                    if ":" in d_:
                        p, v = d_.split(":", 1)
                        decls[p.strip().lower()] = norm_val(v)
                sels = [re.sub(r"\s*([>+~])\s*", r"\1", _norm_ws(x)) for x in pre.split(",") if x.strip()]
                self.rules.append(Rule(ctx, sels, decls, len(self.rules)))
            i = k
    def medias(self):
        return sorted({c for r in self.rules for c in r.ctx if c.startswith("@media")} | set())
    def get(self, sel, prop, media=None):
        """Last declared value of prop for a rule whose selector list contains `sel`, in exactly this media context.
        media=None -> top level; media='(max-width:768px)' -> inside that @media; media='*' -> anywhere."""
        sel = re.sub(r"\s*([>+~])\s*", r"\1", _norm_ws(sel))
        want = None if media in (None, "*") else "@media " + norm_media(media)
        val = None
        for r in self.rules:
            if sel not in r.sels or prop not in r.decls:
                continue
            if media == "*" or (want is None and not r.ctx) or (want is not None and r.ctx == (want,)):
                val = r.decls[prop]
        return val
    def order(self, sel, prop, media=None):
        """Source order index of the winning (last) declaration of prop for sel in that media context, or -1."""
        sel = re.sub(r"\s*([>+~])\s*", r"\1", _norm_ws(sel))
        want = None if media in (None, "*") else "@media " + norm_media(media)
        o = -1
        for r in self.rules:
            if sel in r.sels and prop in r.decls and (media == "*" or (want is None and not r.ctx) or (want is not None and r.ctx == (want,))):
                o = r.order
        return o
    def media_rules(self, pattern):
        """Rules inside any @media whose condition matches regex `pattern`."""
        return [r for r in self.rules if any(re.search(pattern, c) for c in r.ctx)]
    def has_atrule(self, prefix):
        return any(a[0].startswith(prefix) for a in self.atrules)
    def vars(self):
        out = {}
        for r in self.rules:
            for p, v in r.decls.items():
                if p.startswith("--"):
                    out[p] = v
        return out


def hex_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(h1, h2):
    a, b = luminance(hex_rgb(h1)), luminance(hex_rgb(h2))
    a, b = max(a, b), min(a, b)
    return (a + 0.05) / (b + 0.05)


def specificity(sel):
    """(ids, classes+attrs+pseudo-classes, elements+pseudo-elements) for a single compound/complex selector."""
    sel = re.sub(r"\[[^\]]*\]", " [a] ", sel)
    sel = re.sub(r":(not|is|where|has)\(([^)]*)\)", lambda m: (" " + m.group(2) + " ") if m.group(1) != "where" else " ", sel)
    ids = len(re.findall(r"#[\w-]+", sel))
    pe = len(re.findall(r"::[\w-]+", sel))
    sel2 = re.sub(r"::[\w-]+", " ", sel)
    cls = len(re.findall(r"\.[\w-]+", sel2)) + len(re.findall(r"(?<!:):[\w-]+", sel2)) + sel.count("[a]")
    tokens = re.split(r"[\s>+~]+", re.sub(r"[#.:][\w-]+|\[a\]", " ", sel2))
    el = len([t for t in tokens if t and t != "*" and re.fullmatch(r"[a-zA-Z][\w-]*", t)]) + pe
    return (ids, cls, el)
