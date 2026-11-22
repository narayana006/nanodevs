"""Small safe YAML subset parser (stdlib only; PyYAML is not available in the sandbox image).

Supported: block mappings/sequences, plain/quoted scalars, flow [] and {} (single or multi line),
block scalars (| > with -/+), comments, multi-document (---), anchors (&a), aliases (*a), merge keys (<<).
Not supported: tags (!!x), complex keys (? ), plain multi-line scalars. Raises YamlError.
"""
import copy
import re


class YamlError(Exception):
    pass


def _strip_comment(s):
    out, q, i = [], None, 0
    while i < len(s):
        c = s[i]
        if q:
            out.append(c)
            if q == '"' and c == "\\" and i + 1 < len(s):
                out.append(s[i + 1]); i += 1
            elif c == q:
                if q == "'" and i + 1 < len(s) and s[i + 1] == "'":
                    out.append("'"); i += 1
                else:
                    q = None
        elif c in "\"'" and (not out or out[-1] in " \t[{,:-" or not "".join(out).strip()):
            q = c; out.append(c)
        elif c == "#" and (i == 0 or s[i - 1] in " \t"):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).rstrip()


def _split_key(text):
    """Return (key, rest) if text is `key: rest` / `key:`; else None."""
    q, depth, i = None, 0, 0
    while i < len(text):
        c = text[i]
        if q:
            if q == '"' and c == "\\":
                i += 1
            elif c == q:
                q = None
        elif c in "\"'" and (i == 0 or text[i - 1] in " ["):
            q = c
        elif c == ":" and (i + 1 == len(text) or text[i + 1] in " \t"):
            key = text[:i].strip()
            if key and key[0] in "[{":
                return None
            return key, text[i + 1:].strip()
        i += 1
    return None


def _scalar(tok):
    t = tok.strip()
    if t == "":
        return None
    if t[0] == '"':
        if len(t) < 2 or t[-1] != '"':
            raise YamlError("bad double-quoted scalar: " + t)
        body, out, i = t[1:-1], [], 0
        while i < len(body):
            c = body[i]
            if c == "\\" and i + 1 < len(body):
                n = body[i + 1]
                out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/", "0": "\0", "r": "\r"}.get(n, "\\" + n))
                i += 2
            else:
                out.append(c); i += 1
        return "".join(out)
    if t[0] == "'":
        if len(t) < 2 or t[-1] != "'":
            raise YamlError("bad single-quoted scalar: " + t)
        return t[1:-1].replace("''", "'")
    if t in ("~", "null", "Null", "NULL"):
        return None
    if t in ("true", "True", "TRUE"):
        return True
    if t in ("false", "False", "FALSE"):
        return False
    if re.fullmatch(r"[-+]?\d+", t) and not (len(t) > 1 and t.lstrip("+-").startswith("0")):
        return int(t)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+)([eE][-+]?\d+)?", t):
        return float(t)
    return t


class _Flow:
    def __init__(self, s, anchors):
        self.s, self.i, self.anchors = s, 0, anchors

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \t\n":
            self.i += 1

    def value(self):
        self.ws()
        if self.i >= len(self.s):
            raise YamlError("unexpected end of flow")
        c = self.s[self.i]
        if c == "[":
            self.i += 1
            out = []
            while True:
                self.ws()
                if self.i >= len(self.s):
                    raise YamlError("unterminated [")
                if self.s[self.i] == "]":
                    self.i += 1; return out
                out.append(self.value())
                self.ws()
                if self.i < len(self.s) and self.s[self.i] == ",":
                    self.i += 1
        if c == "{":
            self.i += 1
            out = {}
            while True:
                self.ws()
                if self.i >= len(self.s):
                    raise YamlError("unterminated {")
                if self.s[self.i] == "}":
                    self.i += 1; return out
                k = self.plain(stop=":,}")
                self.ws()
                if self.i < len(self.s) and self.s[self.i] == ":":
                    self.i += 1
                    v = self.value() if not self._peek_end() else None
                else:
                    v = None
                out[k if isinstance(k, str) else str(k)] = v
                self.ws()
                if self.i < len(self.s) and self.s[self.i] == ",":
                    self.i += 1
        if c == "*":
            return self.plain_alias()
        return self.plain(stop=",]}")

    def _peek_end(self):
        self.ws()
        return self.i < len(self.s) and self.s[self.i] in ",}"

    def plain_alias(self):
        j = self.i + 1
        while j < len(self.s) and self.s[j] not in " ,]}\n":
            j += 1
        name = self.s[self.i + 1:j]; self.i = j
        if name not in self.anchors:
            raise YamlError("unknown alias " + name)
        return copy.deepcopy(self.anchors[name])

    def plain(self, stop):
        self.ws()
        c = self.s[self.i] if self.i < len(self.s) else ""
        if c in "\"'":
            j = self.i + 1
            while j < len(self.s):
                if c == '"' and self.s[j] == "\\":
                    j += 2; continue
                if self.s[j] == c:
                    if c == "'" and j + 1 < len(self.s) and self.s[j + 1] == "'":
                        j += 2; continue
                    break
                j += 1
            tok = self.s[self.i:j + 1]; self.i = j + 1
            return _scalar(tok)
        j = self.i
        while j < len(self.s):
            ch = self.s[j]
            if ch in stop and (ch != ":" or j + 1 >= len(self.s) or self.s[j + 1] in " \t\n,}]"):
                break
            j += 1
        tok = self.s[self.i:j]; self.i = j
        return _scalar(tok)


def _flow_parse(text, anchors):
    f = _Flow(text, anchors)
    v = f.value()
    f.ws()
    if f.i != len(f.s):
        raise YamlError("trailing text after flow collection: " + f.s[f.i:])
    return v


class _Parser:
    def __init__(self, text):
        self.raw = text.split("\n")
        self.lines = []  # (indent, text, rawindex)
        self.anchors = {}
        for n, r in enumerate(self.raw):
            if "\t" in r[:len(r) - len(r.lstrip())]:
                if r.strip() and not r.strip().startswith("#"):
                    raise YamlError(f"line {n+1}: tab used for indentation")
            s = _strip_comment(r)
            if s.strip() == "":
                self.lines.append(None)
                continue
            self.lines.append((len(s) - len(s.lstrip(" ")), s.strip(), n))
        self.pos = 0

    def peek(self):
        while self.pos < len(self.lines) and self.lines[self.pos] is None:
            self.pos += 1
        return self.lines[self.pos] if self.pos < len(self.lines) else None

    def parse(self):
        ln = self.peek()
        if ln is None:
            return None
        v = self.block(ln[0])
        if self.peek() is not None:
            raise YamlError(f"line {self.peek()[2]+1}: unexpected content (bad indentation?)")
        return v

    def block(self, indent):
        ln = self.peek()
        if ln is None or ln[0] < indent:
            return None
        if ln[1] == "-" or ln[1].startswith("- "):
            return self.seq(ln[0])
        return self.mapping(ln[0])

    def seq(self, indent):
        out = []
        while True:
            ln = self.peek()
            if ln is None or ln[0] != indent or not (ln[1] == "-" or ln[1].startswith("- ")):
                if ln is not None and ln[0] > indent:
                    raise YamlError(f"line {ln[2]+1}: bad indentation in sequence")
                return out
            rest = ln[1][1:]
            lead = len(rest) - len(rest.lstrip(" "))
            rest = rest.lstrip(" ")
            if rest == "":
                self.pos += 1
                nxt = self.peek()
                out.append(self.block(nxt[0]) if nxt and nxt[0] > indent else None)
                continue
            anchor = None
            m = re.match(r"&(\S+)\s*(.*)$", rest)
            if m and not _split_key(rest[0:0] + rest):
                anchor, rest = m.group(1), m.group(2)
            if rest == "" and anchor:
                self.pos += 1
                nxt = self.peek()
                v = self.block(nxt[0]) if nxt and nxt[0] > indent else None
                self.anchors[anchor] = v
                out.append(v)
                continue
            if _split_key(rest) and not rest.startswith(("\"", "'")) or (_split_key(rest) and rest[0] in "\"'" and self._quoted_key(rest)):
                self.lines[self.pos] = (indent + 1 + lead, rest, ln[2])
                v = self.mapping(indent + 1 + lead)
            elif rest == "-" or rest.startswith("- "):
                self.lines[self.pos] = (indent + 1 + lead, rest, ln[2])
                v = self.seq(indent + 1 + lead)
            else:
                self.pos += 1
                v = self.inline(rest, indent, ln[2])
            if anchor:
                self.anchors[anchor] = v
            out.append(v)

    def _quoted_key(self, rest):
        return _split_key(rest) is not None

    def inline(self, rest, indent, rawidx, key_indent=None):
        """Parse the value text on the same line (scalar, flow, alias, block scalar)."""
        rest = rest.strip()
        if rest.startswith("*") and re.fullmatch(r"\*\S+", rest):
            name = rest[1:]
            if name not in self.anchors:
                raise YamlError(f"line {rawidx+1}: unknown alias {name}")
            return copy.deepcopy(self.anchors[name])
        if rest[0] in "|>":
            if not re.fullmatch(r"[|>][-+0-9]*", rest):
                raise YamlError(f"line {rawidx+1}: bad block scalar header")
            return self.block_scalar(rest, indent if key_indent is None else key_indent, rawidx)
        if rest[0] in "[{":
            text = rest
            while not self._balanced(text):
                self.pos_raw_advance = True
                nxt = self.peek()
                if nxt is None:
                    raise YamlError(f"line {rawidx+1}: unterminated flow collection")
                text += " " + nxt[1]
                self.pos += 1
            return _flow_parse(text, self.anchors)
        if rest[0] in "!":
            raise YamlError(f"line {rawidx+1}: tags are not supported")
        if rest[0] == "&":
            m = re.match(r"&(\S+)\s*(.*)$", rest)
            v = self.inline(m.group(2), indent, rawidx) if m.group(2) else None
            self.anchors[m.group(1)] = v
            return v
        if rest[0] in "\"'":
            q = rest[0]
            if len(rest) < 2 or rest[-1] != q:
                raise YamlError(f"line {rawidx+1}: unterminated quoted scalar")
        return _scalar(rest)

    @staticmethod
    def _balanced(t):
        d, q = 0, None
        for i, c in enumerate(t):
            if q:
                if c == q:
                    q = None
            elif c in "\"'":
                q = c
            elif c in "[{":
                d += 1
            elif c in "]}":
                d -= 1
        return d <= 0

    def block_scalar(self, header, parent_indent, rawidx):
        style = header[0]
        chomp = "-" if "-" in header else "+" if "+" in header else ""
        i = rawidx + 1
        body = []
        block_indent = None
        while i < len(self.raw):
            r = self.raw[i]
            if r.strip() == "":
                body.append("")
                i += 1
                continue
            ind = len(r) - len(r.lstrip(" "))
            if ind <= parent_indent:
                break
            if block_indent is None:
                block_indent = ind
            if ind < block_indent:
                break
            body.append(r[block_indent:])
            i += 1
        # advance parser past consumed lines
        while self.pos < len(self.lines) and (self.lines[self.pos] is None or self.lines[self.pos][2] < i):
            self.pos += 1
        trailing = 0
        while body and body[-1] == "":
            body.pop(); trailing += 1
        if style == "|":
            text = "\n".join(body)
        else:
            parts, cur = [], []
            for b in body:
                if b == "":
                    parts.append(" ".join(cur)); cur = []
                    parts.append("\n")
                else:
                    cur.append(b)
            parts.append(" ".join(cur))
            text = "".join(parts)
        if not body:
            return ""
        if chomp == "-":
            return text
        if chomp == "+":
            return text + "\n" * (1 + trailing)
        return text + "\n"

    def mapping(self, indent):
        out = {}
        while True:
            ln = self.peek()
            if ln is None or ln[0] < indent:
                return out
            if ln[0] > indent:
                raise YamlError(f"line {ln[2]+1}: bad indentation")
            if ln[1] == "-" or ln[1].startswith("- "):
                return out
            kv = _split_key(ln[1])
            if kv is None:
                raise YamlError(f"line {ln[2]+1}: expected 'key: value', got {ln[1]!r}")
            key, rest = kv
            key = _scalar(key) if key[:1] in "\"'" else key
            key = key if isinstance(key, str) else str(key)
            self.pos += 1
            anchor = None
            if rest.startswith("&"):
                m = re.match(r"&(\S+)\s*(.*)$", rest)
                anchor, rest = m.group(1), m.group(2)
            if rest == "":
                nxt = self.peek()
                if nxt and (nxt[0] > indent or (nxt[0] == indent and (nxt[1] == "-" or nxt[1].startswith("- ")))):
                    v = self.block(nxt[0])
                else:
                    v = None
            else:
                v = self.inline(rest, indent, ln[2], key_indent=indent)
            if anchor:
                self.anchors[anchor] = v
            if key == "<<":
                for m_ in (v if isinstance(v, list) else [v]):
                    if isinstance(m_, dict):
                        for mk, mv in m_.items():
                            out.setdefault(mk, mv)
                continue
            if key in out:
                raise YamlError(f"line {ln[2]+1}: duplicate key {key!r}")
            out[key] = v


def load_all(text):
    docs, cur = [], []
    for line in text.split("\n"):
        if re.match(r"^---(\s|$)", line):
            if "".join(cur).strip():
                docs.append("\n".join(cur))
            cur = []
            rest = line[3:].strip()
            if rest and not rest.startswith("#"):
                cur.append(rest)
        elif re.match(r"^\.\.\.\s*$", line):
            continue
        else:
            cur.append(line)
    if "".join(cur).strip() or not docs:
        docs.append("\n".join(cur))
    out = []
    for d in docs:
        if d.strip() == "" or all(l.strip() == "" or l.strip().startswith("#") for l in d.split("\n")):
            continue
        out.append(_Parser(d).parse())
    return out


def load(text):
    docs = load_all(text)
    if len(docs) > 1:
        raise YamlError("multiple documents")
    return docs[0] if docs else None
