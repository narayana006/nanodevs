#!/usr/bin/env bash
# Start the CPU-only model server, wait until it is ready, then run a few real tasks
# through the locked-down test sandbox. Needs: Docker, Python 3.9+. First run downloads ~16 GB.
set -euo pipefail
cd "$(dirname "$0")/.."
N="${1:-5}"
docker compose up -d server
echo "Waiting for the model to load (first start downloads the model)..."
until curl -sf http://127.0.0.1:8080/health >/dev/null; do sleep 5; done
python3 teacher/run_python.py quickstart 8080 1 1 "$N"
echo "Done. Results: teacher/python_quickstart.json"
echo "Stop with: docker compose down"
