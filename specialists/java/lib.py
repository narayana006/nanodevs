"""Helpers for declaring Java tasks compactly. Used only by build.py; consumers read tasks.jsonl."""
import re

PRELUDE = r'''
import java.util.*;
public class HiddenTest {
    static int fails = 0;
    static void fail(String m) { fails++; System.out.println("FAIL: " + m); }
    static void ok(boolean c, String m) { if (!c) fail(m); }
    static void eq(Object exp, Object act, String m) {
        boolean same;
        if (exp instanceof int[] && act instanceof int[]) same = java.util.Arrays.equals((int[]) exp, (int[]) act);
        else if (exp instanceof long[] && act instanceof long[]) same = java.util.Arrays.equals((long[]) exp, (long[]) act);
        else if (exp instanceof Object[] && act instanceof Object[]) same = java.util.Arrays.deepEquals((Object[]) exp, (Object[]) act);
        else if (isIntegral(exp) && isIntegral(act)) same = ((Number) exp).longValue() == ((Number) act).longValue();
        else if (exp instanceof Number && act instanceof Number) same = Math.abs(((Number) exp).doubleValue() - ((Number) act).doubleValue()) <= 1e-9;
        else same = java.util.Objects.equals(exp, act);
        if (!same) fail(m + ": expected <" + show(exp) + "> but was <" + show(act) + ">");
    }
    static boolean isIntegral(Object o) { return o instanceof Integer || o instanceof Long || o instanceof Short || o instanceof Byte; }
    static String show(Object o) {
        if (o instanceof int[]) return java.util.Arrays.toString((int[]) o);
        if (o instanceof long[]) return java.util.Arrays.toString((long[]) o);
        return o instanceof Object[] ? java.util.Arrays.deepToString((Object[]) o) : String.valueOf(o);
    }
    static void thrown(Class<? extends Throwable> c, Runnable r, String m) {
        try { r.run(); } catch (Throwable t) { if (c.isInstance(t)) return; fail(m + ": expected " + c.getSimpleName() + " but got " + t); return; }
        fail(m + ": expected " + c.getSimpleName() + " but nothing was thrown");
    }
    public static void main(String[] args) {
        try { run(); } catch (Throwable t) { t.printStackTrace(System.out); fail("uncaught " + t); }
        if (fails > 0) { System.out.println(fails + " failure(s)"); System.exit(1); }
        System.out.println("PASS");
    }
'''

def _hidden(body, helpers=""):
    return PRELUDE + (helpers + "\n" if helpers else "") + "    static void run() throws Exception {\n" + body.strip("\n") + "\n    }\n}\n"

def _patch(files, patches):
    out = dict(files)
    for f, old, new in patches:
        assert old in out[f], (f, old)
        out[f] = out[f].replace(old, new, 1)
    return out

def _clean(files):
    return {k: v.strip("\n") + "\n" for k, v in files.items()}

def fix(id, diff, symptom, ref, bug, body, fname, helpers="", extra=None, tags=()):
    """ref: dict file->source (correct). bug: list of (file, old, new) applied to ref to make the buggy start."""
    ref = _clean({**(extra or {}), **ref}) if extra else _clean(ref)
    start = _patch(ref, bug)
    changed = {f: ref[f] for f in ref if ref[f] != start[f]}
    return dict(id=id, kind="fix", difficulty=diff, files=start, instruction=symptom, visible="",
                hidden_tests={"HiddenTest.java": _hidden(body, helpers)}, reference=changed, entry="HiddenTest", tags=list(tags))

def impl(id, diff, spec, stub, ref, body, visible="", helpers="", tags=()):
    """stub/ref: dict file->source. stub compiles and throws UnsupportedOperationException."""
    stub, ref = _clean(stub), _clean(ref)
    return dict(id=id, kind="implement", difficulty=diff, files=stub, instruction=spec, visible=visible.strip("\n"),
                hidden_tests={"HiddenTest.java": _hidden(body, helpers)}, reference=ref, entry="HiddenTest", tags=list(tags))

def ext(id, diff, files, instruction, patches, body, new_files=None, visible="", helpers="", tags=()):
    """files: working starting code. patches: [(file, old, new)] turning it into the reference. new_files: added files."""
    files = _clean(files)
    ref = _patch(files, patches)
    changed = {f: ref[f] for f in ref if ref[f] != files[f]}
    changed.update(_clean(new_files or {}))
    return dict(id=id, kind="extend", difficulty=diff, files=files, instruction=instruction, visible=visible.strip("\n"),
                hidden_tests={"HiddenTest.java": _hidden(body, helpers)}, reference=changed, entry="HiddenTest", tags=list(tags))
