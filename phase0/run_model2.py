"""Run the round 2 tasks against one running llama-server. Usage: run_model2.py NAME PORT [K]"""
import os
import sys

from harness2 import run_eval2
from harness import HERE
from tasks_fix import TASKS_FIX
from tasks_write import TASKS_WRITE
from tasks_feature import TASKS_FEATURE
from tasks_tests import TASKS_TESTS

name, port = sys.argv[1], sys.argv[2]
k = int(sys.argv[3]) if len(sys.argv) > 3 else 3
os.makedirs(os.path.join(HERE, "results2"), exist_ok=True)
tasks = TASKS_FIX + TASKS_WRITE + TASKS_FEATURE + TASKS_TESTS
run_eval2(name, f"http://127.0.0.1:{port}", tasks, k, os.path.join(HERE, "results2", f"{name}.json"))
