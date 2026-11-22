"""Machine-checkable rules. Each rule: fn(ctx, **args) -> (ok: bool, message: str).

ctx.files = {relpath: text} (candidate files merged over the start files).
Rule types are referenced from tasks.jsonl `checks[*].type`.
"""
import json
import os
import re

import hcl
import yamlmini

# ----------------------------------------------------------------------------- loading / path engine


class Ctx:
    def __init__(self, files):
        self.files = files
        self._cache = {}

    def text(self, name):
        if name not in self.files:
            raise KeyError(f"missing file {name}")
        return self.files[name]

    def docs(self, name):
        if name in self._cache:
            return self._cache[name]
        t = self.text(name)
        ext = os.path.splitext(name)[1].lower()
        if ext in (".yaml", ".yml") or name.endswith(".gitlab-ci.yml"):
            d = yamlmini.load_all(t)
        elif ext == ".json":
            d = [json.loads(t)]
        elif ext == ".tf":
            d = [hcl.loads(t)]
        else:
            raise ValueError("cannot parse " + name)
        self._cache[name] = d
        return d


def parse_path(path):
    segs, i = [], 0
    while i < len(path):
        c = path[i]
        if c == ".":
            i += 1
        elif c == '"':
            j = path.index('"', i + 1)
            segs.append(("key", path[i + 1:j])); i = j + 1
        elif c == "[":
            j = path.index("]", i)
            inner = path[i + 1:j]
            segs.append(("all",) if inner == "*" else ("idx", int(inner))); i = j + 1
        else:
            j = i
            while j < len(path) and path[j] not in ".[":
                j += 1
            seg = path[i:j]
            segs.append(("wild",) if seg == "*" else ("key", seg)); i = j
    return segs


def get(node, path):
    """All values reachable at `path` (a ` | `-separated union). Lists are flattened when a key follows."""
    out = []
    for alt in path.split(" | "):
        cur = [node]
        for seg in parse_path(alt.strip()):
            nxt = []
            for n in cur:
                if seg[0] == "key":
                    if isinstance(n, list):
                        for it in n:
                            if isinstance(it, dict) and seg[1] in it:
                                nxt.append(it[seg[1]])
                    elif isinstance(n, dict) and seg[1] in n:
                        nxt.append(n[seg[1]])
                elif seg[0] == "wild":
                    if isinstance(n, dict):
                        nxt.extend(n.values())
                elif seg[0] == "all":
                    if isinstance(n, list):
                        nxt.extend(n)
                elif seg[0] == "idx":
                    if isinstance(n, list) and -len(n) <= seg[1] < len(n):
                        nxt.append(n[seg[1]])
            cur = nxt
        out.extend(cur)
    return out


def _num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            return None
    return None


_Q = {"Ki": 2**10, "Mi": 2**20, "Gi": 2**30, "Ti": 2**40, "K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12, "m": 1e-3, "k": 1e3}


def qty(x):
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    if not isinstance(x, str):
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([A-Za-z]{0,2})", x.strip())
    if not m:
        return None
    suf = m.group(2)
    if suf and suf not in _Q:
        return None
    return float(m.group(1)) * (_Q[suf] if suf else 1)


def _op(op, v, want):
    if op == "eq":
        if v == want and type(v) == type(want):
            return True
        scalar = lambda x: isinstance(x, (str, int, float)) and not isinstance(x, bool)
        return v == want or (scalar(v) and scalar(want) and str(v) == str(want))
    if op == "ne":
        return not _op("eq", v, want)
    if op == "in":
        return any(_op("eq", v, w) for w in want)
    if op == "not_in":
        return not _op("in", v, want)
    if op in ("regex", "not_regex"):
        sv = " ".join(map(str, v)) if isinstance(v, list) else str(v) if isinstance(v, (str, int, float)) and not isinstance(v, bool) else None
        hit = sv is not None and re.search(want, sv) is not None
        return hit if op == "regex" else not hit
    if op in ("gte", "lte", "gt", "lt"):
        a, b = _num(v), _num(want)
        if a is None or b is None:
            return False
        return {"gte": a >= b, "lte": a <= b, "gt": a > b, "lt": a < b}[op]
    if op in ("qty_lte", "qty_gte"):
        a, b = qty(v), qty(want)
        if a is None or b is None:
            return False
        return a <= b if op == "qty_lte" else a >= b
    if op == "truthy":
        return bool(v) and v not in ("false", "False", "no")
    if op == "falsy":
        return not v or v in ("false", "False", "no")
    if op == "contains":
        if isinstance(v, (list, tuple)):
            return any(_op("eq", i, want) for i in v)
        if isinstance(v, dict):
            return want in v
        return isinstance(v, str) and str(want) in v
    if op == "not_contains":
        return not _op("contains", v, want)
    if op == "len_gte":
        return hasattr(v, "__len__") and len(v) >= want
    if op == "len_lte":
        return hasattr(v, "__len__") and len(v) <= want
    if op == "type":
        return {"str": isinstance(v, str), "int": isinstance(v, int) and not isinstance(v, bool), "bool": isinstance(v, bool),
                "list": isinstance(v, list), "dict": isinstance(v, dict)}[want]
    raise ValueError("unknown op " + op)


def _select(docs, select):
    if not select:
        return [d for d in docs if d is not None]
    out = []
    for d in docs:
        if not isinstance(d, dict):
            continue
        ok = True
        for k, want in select.items():
            vals = get(d, k)
            wants = want if isinstance(want, list) else [want]
            if not any(v in wants for v in vals):
                ok = False
        if ok:
            out.append(d)
    return out


def r_q(ctx, file, path, op, value=None, select=None, mode="all", allow_empty=False, min_docs=1, each=None):
    """Query a YAML/JSON/HCL file. For each selected document (and, if `each` is given, for each element found at the
    `each` path inside it), apply `op` to the values found at `path`.
    mode all: >=1 value and all satisfy; any: some value satisfies; none: no value satisfies.
    ops: eq ne in not_in regex not_regex gte lte gt lt qty_lte qty_gte truthy falsy contains not_contains
         len_gte len_lte type exists missing"""
    docs = _select(ctx.docs(file), select)
    if len(docs) < min_docs:
        return False, f"no document matching {select} in {file}"
    for d in docs:
        label = str((select or {}).get("kind", "")) + "/" + str((get(d, "metadata.name") or [""])[0]) if isinstance(d, dict) else ""
        nodes = [d]
        if each:
            nodes = get(d, each)
            if not nodes and not allow_empty:
                return False, f"{file} {label}: nothing at {each}"
        for node in nodes:
            vals = get(node, path)
            if op == "exists":
                ok = len(vals) > 0 and any(v is not None for v in vals)
            elif op == "missing":
                ok = len([v for v in vals if v is not None]) == 0
            elif mode == "all":
                ok = (len(vals) > 0 or allow_empty) and all(_op(op, v, value) for v in vals)
            elif mode == "any":
                ok = any(_op(op, v, value) for v in vals)
            elif mode == "none":
                ok = not any(_op(op, v, value) for v in vals)
            else:
                raise ValueError("bad mode")
            if not ok:
                who = (node.get("name") if isinstance(node, dict) and isinstance(node.get("name"), str) else "")
                return False, f"{file} {label} {who}: {path} {op} {value!r} failed (values: {str(vals)[:120]})"
    return True, "ok"


def _leaves(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _leaves(k)
            yield from _leaves(v)
    elif isinstance(x, list):
        for v in x:
            yield from _leaves(v)
    elif isinstance(x, str):
        yield x


def r_q_scan(ctx, file, regex, expect="absent", select=None):
    """Scan every string key/value in the parsed document(s) for a regex."""
    hits = [s for d in _select(ctx.docs(file), select) for s in _leaves(d) if re.search(regex, s)]
    if expect == "absent":
        return (not hits), (f"found {hits[:2]!r} matching {regex}" if hits else "ok")
    return (bool(hits)), ("ok" if hits else f"nothing matches {regex}")


def r_docs(ctx, file, select=None, min=1, max=None):
    n = len(_select(ctx.docs(file), select))
    if n < min or (max is not None and n > max):
        return False, f"{n} documents match {select}, want {min}..{max}"
    return True, "ok"


def r_valid(ctx, file):
    ctx.docs(file)
    return True, "ok"


# ----------------------------------------------------------------------------- generic text rules


def r_file_exists(ctx, file):
    return (file in ctx.files and ctx.files[file].strip() != ""), ("ok" if file in ctx.files else f"{file} missing")


def r_contains(ctx, file, regex, flags="m", count_min=1):
    f = sum(getattr(re, c.upper()) for c in flags) if flags else 0
    n = len(re.findall(regex, ctx.text(file), f))
    return n >= count_min, ("ok" if n >= count_min else f"{file}: pattern {regex!r} not found")


def r_not_contains(ctx, file, regex, flags="m"):
    f = sum(getattr(re, c.upper()) for c in flags) if flags else 0
    m = re.search(regex, ctx.text(file), f)
    return m is None, ("ok" if not m else f"{file}: forbidden pattern {regex!r} found: {m.group(0)[:80]!r}")


def r_lineset(ctx, file, has, absent=()):
    """Non-comment lines of file (stripped, leading ./ and / removed) must include each entry (list = alternatives)."""
    lines = {l.strip().lstrip("/") for l in ctx.text(file).splitlines() if l.strip() and not l.strip().startswith("#")}
    lines |= {l.rstrip("/") for l in lines}
    for h in has:
        alts = h if isinstance(h, list) else [h]
        if not any(a.lstrip("/").rstrip("/") in lines or a in lines for a in alts):
            return False, f"{file}: missing entry {alts[0]!r}"
    for a in absent:
        if a in lines:
            return False, f"{file}: must not contain {a!r}"
    return True, "ok"


def r_ordered(ctx, file, regexes, flags="m"):
    """Regexes must match in order (each match starts at/after the end of the previous)."""
    t = ctx.text(file)
    pos = 0
    f = sum(getattr(re, c.upper()) for c in flags) if flags else 0
    for rx in regexes:
        m = re.compile(rx, f).search(t, pos)
        if not m:
            return False, f"{file}: {rx!r} not found after position {pos}"
        pos = m.end()
    return True, "ok"


# ----------------------------------------------------------------------------- Dockerfile


def df_parse(text):
    """-> list of stages; each stage dict(image, alias, instrs=[(CMD, args, line)]); plus global ARGs."""
    raw = text.split("\n")
    instrs, buf, startline = [], "", 0
    for n, l in enumerate(raw):
        s = l.strip()
        if not buf and (s == "" or s.startswith("#")):
            continue
        if buf and s.startswith("#"):
            continue
        if not buf:
            startline = n + 1
        if s.endswith("\\"):
            buf += s[:-1] + " "
            continue
        buf += s
        m = re.match(r"(\w+)\s*(.*)$", buf, re.S)
        if m:
            instrs.append((m.group(1).upper(), m.group(2).strip(), startline))
        buf = ""
    stages, gargs, cur = [], {}, None
    for cmd, args, ln in instrs:
        if cmd == "FROM":
            toks = [t for t in args.split() if not t.startswith("--")]
            alias = toks[2] if len(toks) >= 3 and toks[1].lower() == "as" else None
            cur = dict(image=toks[0] if toks else "", alias=alias, instrs=[], line=ln)
            stages.append(cur)
        elif cur is None:
            if cmd == "ARG":
                k, _, v = args.partition("=")
                gargs[k.strip()] = v.strip().strip("\"'")
        else:
            cur["instrs"].append((cmd, args, ln))
    return stages, gargs


def _resolve(img, gargs):
    return re.sub(r"\$\{?(\w+)\}?", lambda m: gargs.get(m.group(1), m.group(0)), img)


def r_df_base_pinned(ctx, file="Dockerfile", allow_latest=False):
    stages, gargs = df_parse(ctx.text(file))
    if not stages:
        return False, "no FROM"
    aliases = set()
    for st in stages:
        img = _resolve(st["image"], gargs)
        if img != "scratch" and img not in aliases:
            if "@sha256:" in img:
                pass
            elif "$" in img:
                return False, f"unresolvable variable in FROM {img}"
            else:
                last = img.rsplit("/", 1)[-1]
                if ":" not in last:
                    return False, f"FROM {img} has no tag (implicit :latest)"
                if last.split(":", 1)[1] == "latest" and not allow_latest:
                    return False, f"FROM {img} uses :latest"
        if st["alias"]:
            aliases.add(st["alias"])
    return True, "ok"


def r_df_from_regex(ctx, regex, file="Dockerfile", stage="final"):
    stages, gargs = df_parse(ctx.text(file))
    sel = {"final": stages[-1:], "first": stages[:1], "all": stages}[stage]
    for st in sel:
        if not re.search(regex, _resolve(st["image"], gargs)):
            return False, f"FROM {st['image']} does not match {regex}"
    return bool(sel), "ok"


def r_df_user_nonroot(ctx, file="Dockerfile"):
    stages, _ = df_parse(ctx.text(file))
    users = [a for c, a, _ in stages[-1]["instrs"] if c == "USER"]
    if not users:
        return False, "final stage has no USER (runs as root)"
    u = users[-1].split(":")[0].strip().strip("\"'")
    if u in ("root", "0", ""):
        return False, f"final USER is {u}"
    return True, "ok"


def r_df_user_before_cmd(ctx, file="Dockerfile"):
    stages, _ = df_parse(ctx.text(file))
    ins = stages[-1]["instrs"]
    iu = [i for i, (c, _, _) in enumerate(ins) if c == "USER"]
    ic = [i for i, (c, _, _) in enumerate(ins) if c in ("CMD", "ENTRYPOINT")]
    return (bool(iu) and bool(ic) and max(iu) < min(ic)), "USER must come before CMD/ENTRYPOINT"


def r_df_no_add_url(ctx, file="Dockerfile"):
    stages, _ = df_parse(ctx.text(file))
    for st in stages:
        for c, a, ln in st["instrs"]:
            if c == "ADD" and re.search(r"https?://|ftp://", a):
                return False, f"line {ln}: ADD with URL"
    return True, "ok"


def r_df_no_add(ctx, file="Dockerfile"):
    stages, _ = df_parse(ctx.text(file))
    for st in stages:
        for c, a, ln in st["instrs"]:
            if c == "ADD":
                return False, f"line {ln}: ADD used (prefer COPY)"
    return True, "ok"


def r_df_healthcheck(ctx, file="Dockerfile"):
    stages, _ = df_parse(ctx.text(file))
    for c, a, _ in stages[-1]["instrs"]:
        if c == "HEALTHCHECK" and not a.upper().startswith("NONE"):
            return True, "ok"
    return False, "final stage has no HEALTHCHECK"


def r_df_instr(ctx, instr, regex=".", file="Dockerfile", scope="final", expect="present", min=1):
    stages, _ = df_parse(ctx.text(file))
    sel = stages[-1:] if scope == "final" else stages
    hits = [(c, a) for st in sel for c, a, _ in st["instrs"] if c == instr.upper() and re.search(regex, a)]
    if expect == "present":
        return len(hits) >= min, ("ok" if len(hits) >= min else f"no {instr} matching {regex!r}")
    return not hits, ("ok" if not hits else f"forbidden {instr}: {hits[0][1][:80]}")


def r_df_instr_order(ctx, steps, file="Dockerfile", scope="final"):
    """steps: list of [INSTR, regex]; first match index of each must be strictly increasing."""
    stages, _ = df_parse(ctx.text(file))
    ins = [(c, a) for c, a, _ in stages[-1]["instrs"]] if scope == "final" else [(c, a) for st in stages for c, a, _ in st["instrs"]]
    last = -1
    for instr, rx in steps:
        idx = next((i for i, (c, a) in enumerate(ins) if i > last and c == instr and re.search(rx, a)), None)
        if idx is None:
            return False, f"expected {instr} matching {rx!r} after position {last}"
        last = idx
    return True, "ok"


def r_df_multistage(ctx, min_stages=2, file="Dockerfile"):
    stages, _ = df_parse(ctx.text(file))
    if len(stages) < min_stages:
        return False, f"{len(stages)} stage(s)"
    if not any(c == "COPY" and "--from" in a for c, a, _ in stages[-1]["instrs"]):
        return False, "final stage does not COPY --from a builder"
    return True, "ok"


def r_df_apt_hygiene(ctx, file="Dockerfile"):
    stages, _ = df_parse(ctx.text(file))
    for st in stages:
        for c, a, ln in st["instrs"]:
            if c != "RUN":
                continue
            if "apt-get install" in a:
                if "apt-get update" not in a:
                    return False, f"line {ln}: apt-get install without update in same RUN"
                if "--no-install-recommends" not in a:
                    return False, f"line {ln}: missing --no-install-recommends"
                if not re.search(r"rm\s+-rf\s+/var/lib/apt/lists", a):
                    return False, f"line {ln}: apt lists not cleaned in same layer"
                if not re.search(r"(-y|--yes|-qq)", a):
                    return False, f"line {ln}: apt-get install without -y"
            elif re.search(r"apt-get update\s*$|apt-get update\s*(&&\s*)?$", a):
                return False, f"line {ln}: apt-get update alone in its own RUN"
    return True, "ok"


def r_df_no_secrets(ctx, file="Dockerfile"):
    stages, gargs = df_parse(ctx.text(file))
    for st in stages:
        for c, a, ln in st["instrs"]:
            if c in ("ENV", "ARG") and re.search(r"(PASS(WORD)?|SECRET|TOKEN|API_?KEY|PRIVATE_?KEY|CREDENTIAL)\w*\s*[= ]\s*[^$\s]", a, re.I):
                return False, f"line {ln}: secret-looking literal in {c}"
    for k, v in gargs.items():
        if re.search(r"(PASS|SECRET|TOKEN|KEY)", k, re.I) and v:
            return False, f"global ARG {k} has default secret"
    return True, "ok"


def r_df_exec_form(ctx, file="Dockerfile"):
    stages, _ = df_parse(ctx.text(file))
    found = False
    for c, a, ln in stages[-1]["instrs"]:
        if c in ("CMD", "ENTRYPOINT"):
            found = True
            if not a.lstrip().startswith("["):
                return False, f"line {ln}: {c} in shell form"
            json.loads(a)
    return found, "ok" if found else "no CMD/ENTRYPOINT"


def r_df_no_curl_pipe(ctx, file="Dockerfile"):
    t = ctx.text(file)
    m = re.search(r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(sh|bash)\b", t.replace("\\\n", " "))
    return m is None, ("ok" if not m else "curl | sh pattern")


def r_df_copy_dot_last(ctx, manifests, install_regex, file="Dockerfile"):
    """Cache-friendly ordering: COPY manifests -> RUN install -> COPY source (. .), in the final-or-any stage that installs."""
    stages, _ = df_parse(ctx.text(file))
    for st in stages:
        ins = st["instrs"]
        for i, (c, a, _) in enumerate(ins):
            if c == "RUN" and re.search(install_regex, a):
                before = [x for x in ins[:i] if x[0] == "COPY" and any(m in x[1] for m in manifests)]
                after = [x for x in ins[i + 1:] if x[0] == "COPY" and re.search(r"(^|\s)\.(/)?\s+\S+", x[1])]
                dot_before = [x for x in ins[:i] if x[0] == "COPY" and re.search(r"(^|\s|--\S+\s)\.(/)?\s+\S+", x[1]) and "--from" not in x[1]]
                if before and not dot_before and after:
                    return True, "ok"
                return False, "dependency manifest must be copied before install, and the source copied after it"
    return False, "install step not found"


# ----------------------------------------------------------------------------- Kubernetes


def r_k8s_selectors(ctx, file):
    """Workload selector.matchLabels must be a subset of its pod template labels; Services must select some template."""
    docs = [d for d in ctx.docs(file) if isinstance(d, dict)]
    tpls = []
    for d in docs:
        if d.get("kind") in ("Deployment", "StatefulSet", "DaemonSet", "ReplicaSet"):
            sel = (get(d, "spec.selector.matchLabels") or [None])[0]
            lab = (get(d, "spec.template.metadata.labels") or [None])[0]
            if not isinstance(sel, dict) or not sel:
                return False, f"{d.get('kind')} has no spec.selector.matchLabels"
            if not isinstance(lab, dict) or any(lab.get(k) != v for k, v in sel.items()):
                return False, f"{d['kind']}/{(get(d, 'metadata.name') or ['?'])[0]}: selector {sel} does not match template labels {lab}"
            tpls.append(lab)
    for d in docs:
        if d.get("kind") == "Service":
            sel = (get(d, "spec.selector") or [None])[0]
            if not isinstance(sel, dict) or not sel:
                return False, "Service without selector"
            if not any(all(l.get(k) == v for k, v in sel.items()) for l in tpls):
                return False, f"Service {(get(d, 'metadata.name') or ['?'])[0]} selector {sel} matches no pod template"
    return True, "ok"


def r_k8s_ports_match(ctx, file):
    """Every Service targetPort that is a name must exist as a containerPort name; numeric must be a containerPort."""
    docs = [d for d in ctx.docs(file) if isinstance(d, dict)]
    cports = set()
    for d in docs:
        for p in get(d, "spec.template.spec.containers[*].ports[*]"):
            if isinstance(p, dict):
                cports.add(p.get("name")); cports.add(p.get("containerPort"))
    for d in docs:
        if d.get("kind") == "Service":
            for p in get(d, "spec.ports[*]"):
                tp = p.get("targetPort", p.get("port"))
                if tp not in cports:
                    return False, f"Service targetPort {tp!r} is not a containerPort/name ({sorted(map(str, cports))})"
    return True, "ok"


def r_k8s_probe_ports(ctx, file):
    """Probe ports must refer to a declared container port (name or number)."""
    for d in ctx.docs(file):
        if not isinstance(d, dict):
            continue
        for c in get(d, "spec.template.spec.containers[*]"):
            declared = {p.get("name") for p in c.get("ports", []) or []} | {p.get("containerPort") for p in c.get("ports", []) or []}
            for pn in ("livenessProbe", "readinessProbe", "startupProbe"):
                for port in get(c, f"{pn}.httpGet.port | {pn}.tcpSocket.port"):
                    if port not in declared:
                        return False, f"{pn} port {port!r} not declared in container ports"
    return True, "ok"


def r_k8s_refs_exist(ctx, file):
    """envFrom/volumes/configMapKeyRef refs inside the same file must resolve (ConfigMap/Secret/PVC/ServiceAccount defined here)."""
    docs = [d for d in ctx.docs(file) if isinstance(d, dict)]
    have = {(d.get("kind"), (get(d, "metadata.name") or [None])[0]) for d in docs}
    for d in docs:
        for n in get(d, "spec.template.spec.volumes[*].configMap.name"):
            if ("ConfigMap", n) not in have:
                return False, f"volume references missing ConfigMap {n}"
        for n in get(d, "spec.template.spec.volumes[*].persistentVolumeClaim.claimName"):
            if ("PersistentVolumeClaim", n) not in have:
                return False, f"volume references missing PVC {n}"
        for n in get(d, "spec.template.spec.containers[*].envFrom[*].configMapRef.name"):
            if ("ConfigMap", n) not in have:
                return False, f"envFrom references missing ConfigMap {n}"
        for n in get(d, "spec.template.spec.volumes[*].configMap.name"):
            pass
        vols = set(get(d, "spec.template.spec.volumes[*].name"))
        for m in get(d, "spec.template.spec.containers[*].volumeMounts[*].name"):
            if m not in vols:
                return False, f"volumeMount {m} has no matching volume"
    return True, "ok"


# ----------------------------------------------------------------------------- CI (GitHub Actions)


def r_ci_uses_pinned(ctx, file, sha=False, allow_first_party_tag=True):
    """Every `uses:` must carry an explicit ref; never a branch (main/master/latest). sha=True: third party must be a 40-hex SHA."""
    for d in ctx.docs(file):
        for u in get(d, "jobs.*.steps[*].uses"):
            if u.startswith("./") or u.startswith("docker://"):
                continue
            if "@" not in u:
                return False, f"uses {u} has no ref"
            ref = u.split("@", 1)[1]
            if ref in ("main", "master", "latest", "HEAD"):
                return False, f"uses {u} tracks a moving branch"
            first = u.startswith(("actions/", "github/"))
            if sha and not (re.fullmatch(r"[0-9a-f]{40}", ref) or (first and allow_first_party_tag and re.fullmatch(r"v\d+(\.\d+){0,2}", ref))):
                return False, f"uses {u} must be pinned to a full commit SHA"
    return True, "ok"


def r_ci_no_untrusted_expr_in_run(ctx, file):
    bad = r"\$\{\{\s*(github\.event\.(issue|pull_request|comment|review|head_commit|pages|commits)[^}]*(title|body|name|label|ref|message|email|login)|github\.head_ref)[^}]*\}\}"
    for d in ctx.docs(file):
        for r in get(d, "jobs.*.steps[*].run"):
            if re.search(bad, r):
                return False, "attacker-controlled expression interpolated into run:"
    return True, "ok"


def r_ci_job_perms(ctx, file, allowed_writes=()):
    """Top-level `permissions` exists OR every job has permissions; no `write-all`; writes only for allowed scopes."""
    for d in ctx.docs(file):
        top = d.get("permissions") if isinstance(d, dict) else None
        jobs = d.get("jobs", {}) or {}
        if top is None and not all(isinstance(j, dict) and "permissions" in j for j in jobs.values()):
            return False, "no least-privilege permissions block (default token is broad)"
        for p in [top] + [j.get("permissions") for j in jobs.values() if isinstance(j, dict)]:
            if p in ("write-all",):
                return False, "permissions: write-all"
            if isinstance(p, dict):
                for scope, lvl in p.items():
                    if lvl == "write" and scope not in allowed_writes:
                        return False, f"permission {scope}: write not allowed here"
    return True, "ok"


def r_ci_needs_acyclic(ctx, file):
    for d in ctx.docs(file):
        jobs = d.get("jobs", {})
        for name, j in jobs.items():
            needs = j.get("needs", []) or []
            needs = [needs] if isinstance(needs, str) else needs
            for n in needs:
                if n not in jobs:
                    return False, f"job {name} needs unknown job {n}"
        # cycle detect
        state = {}

        def visit(n):
            if state.get(n) == 1:
                raise ValueError("cycle")
            if state.get(n) == 2:
                return
            state[n] = 1
            nd = jobs[n].get("needs", []) or []
            for m in ([nd] if isinstance(nd, str) else nd):
                visit(m)
            state[n] = 2
        try:
            for n in jobs:
                visit(n)
        except ValueError:
            return False, "needs cycle"
    return True, "ok"


# ----------------------------------------------------------------------------- Makefile


def mk_parse(text):
    """-> dict(vars, rules[{targets, prereqs, recipe[]}], phony set, default_goal, errors[])"""
    lines = text.split("\n")
    joined, buf = [], ""
    for l in lines:
        if l.endswith("\\") and not l.startswith("#"):
            buf += l[:-1] + " "
            continue
        joined.append(buf + l); buf = ""
    variables, rules, phony, errors, cur = {}, [], set(), [], None
    default = None
    for l in joined:
        if l.startswith("\t"):
            if cur is None:
                errors.append("recipe line before any rule")
            else:
                cur["recipe"].append(l[1:])
            continue
        s = l.strip()
        if s == "" or s.startswith("#"):
            continue
        s = re.sub(r"\s+#.*$", "", s)
        m = re.match(r"^([A-Za-z_.][\w.\-]*)\s*(:=|\?=|\+=|=|::=)\s*(.*)$", s)
        if m:
            k, o, v = m.groups()
            if k == ".DEFAULT_GOAL":
                default = v.strip()
                continue
            if o == "?=" and k in variables:
                pass
            elif o == "+=":
                variables[k] = (variables.get(k, "") + " " + v).strip()
            else:
                variables[k] = v
            cur = None
            continue
        m = re.match(r"^([^:=\s][^:=]*?)\s*::?\s*([^=]*?)(?:\s*;\s*(.*))?$", s)
        if m and not s.startswith(("ifeq", "ifneq", "ifdef", "ifndef", "else", "endif", "include", "-include", "export", ".DEFAULT_GOAL")):
            targets = m.group(1).split()
            prereqs = [p for p in m.group(2).split() if p != "|"]
            if targets == [".PHONY"]:
                phony |= set(prereqs)
                cur = None
                continue
            cur = dict(targets=targets, prereqs=prereqs, recipe=[])
            if m.group(3):
                cur["recipe"].append(m.group(3))
            rules.append(cur)
            if default is None and not targets[0].startswith(".") and "%" not in targets[0]:
                default = targets[0]
            continue
        m = re.match(r"^\.DEFAULT_GOAL\s*:?=\s*(\S+)", s)
        if m:
            default = m.group(1)
            continue
        cur = None
    return dict(vars=variables, rules=rules, phony=phony, default=default, errors=errors)


def _expand(s, variables, tgt="", pre=None, depth=0):
    pre = pre or []

    def rep(m):
        n = m.group(1) or m.group(2)
        if depth < 8 and n in variables:
            return _expand(variables[n], variables, tgt, pre, depth + 1)
        return ""
    s = re.sub(r"\$\(([A-Za-z_][\w]*)\)|\$\{([A-Za-z_][\w]*)\}", rep, s)
    s = s.replace("$@", tgt).replace("$<", pre[0] if pre else "").replace("$^", " ".join(pre)).replace("$$", "$")
    return s


def mk_plan(mk, target, overrides=None):
    variables = {"MAKE": "make", "CURDIR": "."}
    variables.update(mk["vars"])
    variables.update(overrides or {})
    rules = {t: r for r in mk["rules"] for t in r["targets"]}
    order, seen = [], set()

    def visit(t):
        if t in seen:
            return
        seen.add(t)
        r = rules.get(t)
        if not r:
            return
        for p in r["prereqs"]:
            visit(p)
        for line in r["recipe"]:
            cmd = _expand(line, variables, t, r["prereqs"]).strip()
            cmd = cmd.lstrip("@-+ ").strip()
            if cmd:
                order.append(cmd)
    visit(target)
    return order


def r_mk_parse_ok(ctx, file="Makefile"):
    mk = mk_parse(ctx.text(file))
    if mk["errors"]:
        return False, "; ".join(mk["errors"])
    if re.search(r"^ +\S", ctx.text(file), re.M) and re.search(r"^ {2,}[^\s#].*", ctx.text(file), re.M):
        # space-indented lines directly under a rule are a classic bug
        for l in ctx.text(file).split("\n"):
            if re.match(r"^ {2,}\S", l) and not l.lstrip().startswith(("#", "ifeq", "ifneq", "else", "endif", "$(")) and "=" not in l.split()[0]:
                return False, f"line indented with spaces instead of a tab: {l.strip()[:50]!r}"
    return True, "ok"


def r_mk_phony(ctx, targets, file="Makefile"):
    mk = mk_parse(ctx.text(file))
    missing = [t for t in targets if t not in mk["phony"]]
    return not missing, ("ok" if not missing else f".PHONY missing {missing}")


def r_mk_target(ctx, target, file="Makefile"):
    mk = mk_parse(ctx.text(file))
    ok = any(target in r["targets"] for r in mk["rules"])
    return ok, "ok" if ok else f"target {target} not defined"


def r_mk_default(ctx, target, file="Makefile"):
    mk = mk_parse(ctx.text(file))
    return mk["default"] == target, f"default goal is {mk['default']!r}, want {target!r}"


def r_mk_var(ctx, name, file="Makefile", regex=None):
    mk = mk_parse(ctx.text(file))
    if name not in mk["vars"]:
        return False, f"variable {name} not defined"
    if regex and not re.search(regex, mk["vars"][name]):
        return False, f"variable {name}={mk['vars'][name]!r} does not match {regex}"
    return True, "ok"


def r_mk_plan(ctx, target, steps, file="Makefile", overrides=None, forbid=()):
    """Dry-run planner: expand `target` (prereqs first). `steps` regexes must appear in order in the command list."""
    mk = mk_parse(ctx.text(file))
    cmds = mk_plan(mk, target, overrides)
    pos = -1
    for rx in steps:
        idx = next((i for i, c in enumerate(cmds) if i > pos and re.search(rx, c)), None)
        if idx is None:
            return False, f"make {target}: no command matching {rx!r} after #{pos}; plan={cmds[:8]}"
        pos = idx
    for rx in forbid:
        if any(re.search(rx, c) for c in cmds):
            return False, f"make {target}: forbidden command {rx!r} in plan"
    return True, "ok"


# ----------------------------------------------------------------------------- registry

RULES = {
    "q": r_q, "q_scan": r_q_scan, "docs": r_docs, "valid": r_valid,
    "file_exists": r_file_exists, "contains": r_contains, "not_contains": r_not_contains, "lineset": r_lineset, "ordered": r_ordered,
    "df_base_pinned": r_df_base_pinned, "df_from_regex": r_df_from_regex, "df_user_nonroot": r_df_user_nonroot,
    "df_user_before_cmd": r_df_user_before_cmd, "df_no_add_url": r_df_no_add_url, "df_no_add": r_df_no_add,
    "df_healthcheck": r_df_healthcheck, "df_instr": r_df_instr, "df_instr_order": r_df_instr_order,
    "df_multistage": r_df_multistage, "df_apt_hygiene": r_df_apt_hygiene, "df_no_secrets": r_df_no_secrets,
    "df_exec_form": r_df_exec_form, "df_no_curl_pipe": r_df_no_curl_pipe, "df_copy_dot_last": r_df_copy_dot_last,
    "k8s_selectors": r_k8s_selectors, "k8s_ports_match": r_k8s_ports_match, "k8s_probe_ports": r_k8s_probe_ports,
    "k8s_refs_exist": r_k8s_refs_exist,
    "ci_uses_pinned": r_ci_uses_pinned, "ci_no_untrusted_expr": r_ci_no_untrusted_expr_in_run,
    "ci_job_perms": r_ci_job_perms, "ci_needs_acyclic": r_ci_needs_acyclic,
    "mk_parse_ok": r_mk_parse_ok, "mk_phony": r_mk_phony, "mk_target": r_mk_target, "mk_default": r_mk_default,
    "mk_var": r_mk_var, "mk_plan": r_mk_plan,
}
