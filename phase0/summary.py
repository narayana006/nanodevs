import glob
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
runs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(here, "results", "*.json")))]
print(f"{'model':<24}{'tasks':>6}{'pass@1':>8}{'pass@5':>8}{'sec/cand':>10}{'tok/cand':>10}")
for r in runs:
    res = r["results"]
    n = len(res)
    p1 = sum(1 for x in res if x["solved_at"] == 1)
    pk = sum(1 for x in res if x["solved_at"])
    cands = [c for x in res for c in x["candidates"]]
    print(f"{r['model']:<24}{n:>6}{p1:>6}/{n:<2}{pk:>5}/{n:<2}{sum(c['gen_seconds'] for c in cands)/len(cands):>10.1f}"
          f"{sum(c['tokens'] for c in cands)/len(cands):>10.0f}")
print()
ids = [x["id"] for x in runs[0]["results"]] if runs else []
print(f"{'task':<20}" + "".join(f"{r['model'][:22]:<24}" for r in runs))
for i, tid in enumerate(ids):
    row = f"{tid:<20}"
    for r in runs:
        s = r["results"][i]["solved_at"] if i < len(r["results"]) else "-"
        row += f"{('solved@' + str(s)) if isinstance(s, int) else ('FAILED' if s is None else s):<24}"
    print(row)
