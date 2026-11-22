"""Tiny test runtime used by hidden tests (copied into the grading sandbox next to them)."""
import sys
import traceback


class Skip(Exception):
    pass


def needs(mod, *names):
    """Tests of NEW api are guarded so that they pass (skip) on the base, where the api does not exist yet."""
    if not all(hasattr(mod, n) for n in names):
        raise Skip()


def run_all(modname):
    mod = __import__(modname)
    for name in sorted(n for n in dir(mod) if n.startswith("test_")):
        fn = getattr(mod, name)
        try:
            fn()
            print("PASS", name)
        except Skip:
            print("PASS", name)
        except BaseException as e:  # noqa: BLE001
            msg = "".join(traceback.format_exception_only(type(e), e)).strip().replace("\n", " ")[:160]
            print("FAIL", name, msg)


def needs_param(fn, *names):
    """Skip (= pass on base) unless callable/class `fn` accepts all the named parameters."""
    import inspect
    try:
        ps = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        raise Skip()
    if not all(n in ps for n in names):
        raise Skip()
