"""Assemble tasks.jsonl from the task modules. Usage: python3 build.py"""
import importlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tb
MODULES = ["js_a", "js_b", "js_c", "js_d", "js_e", "js_f", "js_g", "html_a", "html_b", "css_a", "css_b"]
for m in MODULES:
    if os.path.exists(os.path.join(HERE, m + ".py")):
        importlib.import_module(m)
ids = [t["id"] for t in tb.TASKS]
assert len(ids) == len(set(ids)), "duplicate ids"
with open(os.path.join(HERE, "tasks.jsonl"), "w") as f:
    for t in tb.TASKS:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")
print("wrote", len(tb.TASKS), "tasks")
