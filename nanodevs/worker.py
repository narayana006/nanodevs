"""Isolated checker entry point; imports no project code or reference solution."""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys


def main():
    resource.setrlimit(resource.RLIMIT_FSIZE, (131072, 131072))
    request = json.loads(Path(sys.argv[1]).read_text())
    failures = []
    try:
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            spec = importlib.util.spec_from_file_location("candidate_module", request["candidate"])
            module = importlib.util.module_from_spec(spec)
            sys.modules["candidate_module"] = module
            spec.loader.exec_module(module)
            function = getattr(module, request["function"])
            for index, case in enumerate(request["cases"]):
                try:
                    actual = function(*case["args"], **case.get("kwargs", {}))
                    if actual != case["expected"]:
                        failures.append({"case": index, "reason": "value_mismatch", "actual": repr(actual)[:200], "expected": repr(case["expected"])[:200]})
                except Exception as error:
                    failures.append({"case": index, "reason": type(error).__name__, "detail": str(error)[:200]})
        output = {"status": "failed" if failures else "passed", "cases": len(request["cases"]), "failures": failures}
    except Exception as error:
        output = {"status": "failed", "cases": len(request["cases"]), "failures": [{"reason": type(error).__name__, "detail": str(error)[:200]}]}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
