"""Collect all tasks from the tasks_*.py modules."""
import importlib

MODULES = ["tasks_fix", "tasks_write", "tasks_write2", "tasks_feature", "tasks_refactor", "tasks_extra"]


def all_tasks():
    out = []
    for m in MODULES:
        try:
            mod = importlib.import_module(m)
        except ModuleNotFoundError as e:
            if e.name == m:
                continue
            raise
        out += [v for k, v in vars(mod).items() if k.startswith("TASKS_") and isinstance(v, list)][0]
    return out
