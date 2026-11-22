"""Build planner SFT data from reference plans, holding out whole task families for an honest test.
Writes train/planner/{train,valid}.jsonl and train/planner/test_ids.json."""
import json, os, random, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tasks = [json.loads(l) for l in open(f"{ROOT}/specialists/planner/tasks.jsonl")]
fams = collections.Counter(t["family"] for t in tasks)
rnd = random.Random(11)
names = sorted(fams); rnd.shuffle(names)
test_f, n = set(), 0
for f in names:                       # hold out families until ~25% of tasks
    if n >= len(tasks) * 0.25: break
    test_f.add(f); n += fams[f]
test = [t for t in tasks if t["family"] in test_f]
rest = [t for t in tasks if t["family"] not in test_f]
rnd.shuffle(rest)
nv = max(8, len(rest) // 10)
os.makedirs(f"{ROOT}/train/planner", exist_ok=True)
def row(t): return {"messages": [{"role": "user", "content": t["prompt"]},
                                 {"role": "assistant", "content": json.dumps(t["reference_plan"])}]}
for name, part in (("train", rest[nv:]), ("valid", rest[:nv])):
    with open(f"{ROOT}/train/planner/{name}.jsonl", "w") as f:
        for t in part: f.write(json.dumps(row(t)) + "\n")
json.dump({"test_families": sorted(test_f), "test_ids": [t["id"] for t in test]}, open(f"{ROOT}/train/planner/test_ids.json", "w"), indent=1)
print(len(rest) - nv, "train,", nv, "valid,", len(test), "held-out test from", len(test_f), "families")
