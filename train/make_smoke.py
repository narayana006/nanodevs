import json, os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase0"))
from harness2 import make_prompt, show
from tasks_fix import TASKS_FIX
from tasks_write import TASKS_WRITE
from tasks_feature import TASKS_FEATURE
rows = []
for t in TASKS_FIX + TASKS_WRITE + TASKS_FEATURE:
    ref = t.get("reference")
    if not ref: continue
    rows.append({"messages": [{"role": "user", "content": make_prompt(t, "")},
                              {"role": "assistant", "content": show(ref)}]})
random.Random(0).shuffle(rows)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smoke")
n = len(rows); k = max(2, n // 8)
for name, part in (("train", rows[k:]), ("valid", rows[:k])):
    with open(f"{out}/{name}.jsonl", "w") as f:
        for r in part: f.write(json.dumps(r) + "\n")
print(n, "examples;", n - k, "train,", k, "valid")
