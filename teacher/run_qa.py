"""Run a model over the qa task set (mutation-graded test writing) with the specialist's own prompts and grader.
Usage: run_qa.py NAME PORT [K] [WORKERS] [LIMIT]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bench
sys.path.insert(0, os.path.join(_bench.ROOT, "specialists", "qa"))
import prompts

tasks = [json.loads(l) for l in open(os.path.join(_bench.ROOT, "specialists", "qa", "tasks.jsonl")) if l.strip()]

def grade(t, text):
    if prompts.extract_tests(text) is None:
        return False, "NO test_solution.py block", False
    ok, detail = prompts.grade_answer(t, text)
    return ok, detail, True

_bench.main("qa", tasks, prompts.render_prompt, grade)
