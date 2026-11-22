"""Task-builder helpers. Every task module imports `add*` from here and appends to TASKS."""
TASKS = []
JS_PRE = "const {test, finish, clock, makeDom, key, assert} = require('./tlib.js');\n"
PY_PRE = "from checklib import *\n"


def _add(id, kind, lang, diff, topic, instruction, start, ref, checks, visible):
    assert diff in ("easy", "medium", "hard") and kind in ("write", "fix", "extend", "a11y", "css")
    assert all(k in start for k in ref) or kind in ("write", "a11y", "css"), id
    TASKS.append(dict(id=id, kind=kind, lang=lang, difficulty=diff, topic=topic, files=start, instruction=instruction.strip(),
                      visible=visible.strip(), checks=checks, reference={"files": ref}, output_files=sorted(ref)))


def js(id, kind, diff, topic, instruction, start, ref, test, visible=""):
    checks = dict(runner="node", entry="test_hidden.js", files={"test_hidden.js": JS_PRE + test.strip() + "\nfinish();\n"})
    _add(id, kind, "js", diff, topic, instruction, start, ref, checks, visible)


def py(id, kind, lang, diff, topic, instruction, start, ref, test, visible=""):
    checks = dict(runner="python", entry="check_hidden.py", files={"check_hidden.py": PY_PRE + test.strip() + "\nfinish()\n"})
    _add(id, kind, lang, diff, topic, instruction, start, ref, checks, visible)


def stub(*names):
    return "module.exports = {\n" + ",\n".join(f"  {n}() {{ throw new Error('not implemented'); }}" for n in names) + "\n};\n"


def jsfix(id, diff, topic, symptom, fname, ref_src, bugs, test, visible=""):
    """Fix-the-bug task. start = reference with each (old, new) replacement applied, so the bug is a real minimal diff."""
    start = ref_src
    for old, new in bugs:
        assert old in start, (id, old)
        start = start.replace(old, new, 1)
    assert start != ref_src
    instr = f"The code in {fname} has a bug (or a few): the hidden tests fail. {symptom} Fix it and return the corrected {fname}; keep the same exports and behaviour otherwise."
    js(id, "fix", diff, topic, instr, {fname: start}, {fname: ref_src}, test, visible)


def jsext(id, diff, topic, instruction, fname, base_src, ref_src, test, visible=""):
    """Extend-an-existing-snippet task: start = working base code (passes old behaviour, fails new tests)."""
    js(id, "extend", diff, topic, instruction, {fname: base_src}, {fname: ref_src}, test, visible)
