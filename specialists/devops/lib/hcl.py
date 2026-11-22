"""Tiny HCL2 (Terraform-style) parser, stdlib only. Produces plain dict/list/str/int/bool structures.

Top-level blocks with labels nest by label: resource "aws_x" "n" {..} -> doc["resource"]["aws_x"]["n"] = body.
Nested unlabeled blocks become a list under their name (body["ingress"] = [ {...}, {...} ]).
Non-literal expressions (var.x, merge(...), a ? b : c) are returned as Expr (a str subclass holding the raw text).
"""
import re


class HclError(Exception):
    pass


class Expr(str):
    pass


TOK = re.compile(r"""
 (?P<ws>[ \t\r]+)
|(?P<nl>\n)
|(?P<comment>\#[^\n]*|//[^\n]*|/\*.*?\*/)
|(?P<heredoc><<-?[A-Za-z_][A-Za-z0-9_]*\n)
|(?P<num>-?\d+(\.\d+)?)
|(?P<id>[A-Za-z_][A-Za-z0-9_\-]*)
|(?P<str>")
|(?P<op>=>|==|!=|<=|>=|&&|\|\||\.\.\.|[{}\[\]()=,:.?+\-*/%<>!])
""", re.X | re.S)


def tokenize(src):
    toks, i = [], 0
    while i < len(src):
        m = TOK.match(src, i)
        if not m:
            raise HclError(f"unexpected character {src[i]!r} at {i}")
        k = m.lastgroup
        if k in ("ws", "comment"):
            i = m.end(); continue
        if k == "nl":
            toks.append(("nl", "\n", i, m.end())); i = m.end(); continue
        if k == "heredoc":
            tag = m.group("heredoc").strip().lstrip("<-")
            end = re.search(r"^[ \t]*" + re.escape(tag) + r"[ \t]*$", src[m.end():], re.M)
            if not end:
                raise HclError("unterminated heredoc")
            body = src[m.end():m.end() + end.start()]
            i = m.end() + end.end()
            toks.append(("str", body, m.start(), i)); continue
        if k == "str":
            j, depth, buf = m.end(), 0, []
            while j < len(src):
                c = src[j]
                if c == "\\" and depth == 0:
                    buf.append(src[j:j + 2]); j += 2; continue
                if src[j:j + 2] == "${" or src[j:j + 2] == "%{":
                    depth += 1; buf.append(src[j:j + 2]); j += 2; continue
                if c == "}" and depth > 0:
                    depth -= 1
                elif c == '"' and depth == 0:
                    break
                elif c == "\n" and depth == 0:
                    raise HclError("newline in string")
                buf.append(c); j += 1
            else:
                raise HclError("unterminated string")
            raw = "".join(buf)
            raw = raw.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
            toks.append(("str", raw, m.start(), j + 1)); i = j + 1; continue
        toks.append((k, m.group(k), m.start(), m.end())); i = m.end()
    toks.append(("eof", "", len(src), len(src)))
    return toks


class P:
    def __init__(self, src):
        self.src, self.t, self.i = src, tokenize(src), 0

    def skip_nl(self):
        while self.t[self.i][0] == "nl":
            self.i += 1

    def body(self, closing):
        out = {}
        while True:
            self.skip_nl()
            k, v, _, _ = self.t[self.i]
            if k == "eof":
                if closing:
                    raise HclError("unexpected end of file, missing }")
                return out
            if k == "op" and v == "}":
                if not closing:
                    raise HclError("unexpected }")
                self.i += 1
                return out
            if k not in ("id", "str"):
                raise HclError(f"unexpected token {v!r}")
            self.i += 1
            nk, nv, _, _ = self.t[self.i]
            if nk == "op" and nv == "=":
                self.i += 1
                out[v] = self.value()
                if self.t[self.i][0] not in ("nl", "eof") and not (self.t[self.i][0] == "op" and self.t[self.i][1] == "}"):
                    raise HclError(f"unexpected {self.t[self.i][1]!r} after attribute {v}")
                continue
            labels = []
            while self.t[self.i][0] in ("id", "str"):
                labels.append(self.t[self.i][1]); self.i += 1
            if not (self.t[self.i][0] == "op" and self.t[self.i][1] == "{"):
                raise HclError(f"expected '{{' after block {v} {labels}")
            self.i += 1
            b = self.body(True)
            if closing is False or closing is None:
                cur = out
                cur = out.setdefault(v, {}) if labels else None
                if labels:
                    for lab in labels[:-1]:
                        cur = cur.setdefault(lab, {})
                    cur[labels[-1]] = b
                else:
                    if v in out and isinstance(out[v], dict) and not isinstance(out[v], list):
                        for kk, vv in b.items():
                            out[v].setdefault(kk, vv)
                    else:
                        out[v] = b
            elif labels:
                cur = out.setdefault(v, {})
                for lab in labels[:-1]:
                    cur = cur.setdefault(lab, {})
                cur[labels[-1]] = b
            else:
                out.setdefault(v, []).append(b)

    def _is_for(self, i):
        while self.t[i][0] == "nl":
            i += 1
        return self.t[i][0] == "id" and self.t[i][1] == "for" and self.t[i + 1][0] == "id"

    def value(self):
        start = self.i
        k, v, s, e = self.t[self.i]
        val = None
        simple = False
        if k == "str":
            self.i += 1; val = v; simple = True
        elif k == "num":
            self.i += 1; val = float(v) if "." in v else int(v); simple = True
        elif k == "id" and v in ("true", "false", "null"):
            self.i += 1; val = {"true": True, "false": False, "null": None}[v]; simple = True
        elif k == "op" and v == "[" and not self._is_for(start + 1):
            self.i += 1; val = []
            while True:
                while self.t[self.i][0] == "nl":
                    self.i += 1
                if self.t[self.i][:2] == ("op", "]"):
                    self.i += 1; break
                val.append(self.value())
                while self.t[self.i][0] == "nl":
                    self.i += 1
                if self.t[self.i][:2] == ("op", ","):
                    self.i += 1
            simple = True
        elif k == "op" and v == "{" and not self._is_for(start + 1):
            self.i += 1; val = {}
            while True:
                while self.t[self.i][0] in ("nl",) or self.t[self.i][:2] == ("op", ","):
                    self.i += 1
                if self.t[self.i][:2] == ("op", "}"):
                    self.i += 1; break
                kk, kv, _, _ = self.t[self.i]
                self.i += 1
                if self.t[self.i][:2] in (("op", "="), ("op", ":")):
                    self.i += 1
                else:
                    raise HclError("expected = in object")
                val[kv] = self.value()
            simple = True
        if simple:
            nk, nv = self.t[self.i][:2]
            if nk in ("nl", "eof") or (nk == "op" and nv in (",", "]", "}", ")")):
                return val
        # generic expression: consume to depth-0 boundary
        self.i = start
        depth = 0
        while True:
            k, v, s, e = self.t[self.i]
            if k == "eof":
                break
            if depth == 0 and (k == "nl" or (k == "op" and v in (",", "]", "}", ")"))):
                break
            if k == "op" and v in "([{":
                depth += 1
            elif k == "op" and v in ")]}":
                depth -= 1
            self.i += 1
        end = self.t[self.i - 1][3]
        return Expr(self.src[self.t[start][2]:end])


def loads(src):
    return P(src).body(False)
