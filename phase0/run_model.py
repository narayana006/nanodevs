"""Run the 20 bug-fix tasks against one running llama-server. Usage: run_model.py NAME PORT [K]"""
import os
import sys

from tasks import TASKS
from harness import run_eval, HERE

name, port = sys.argv[1], sys.argv[2]
k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
run_eval(name, f"http://127.0.0.1:{port}", TASKS, k, os.path.join(HERE, "results", f"{name}.json"))
