#!/bin/sh
# Rebuild tasks.jsonl inside the locked-down container (one container).
cd "$(dirname "$0")" || exit 1
docker run --rm -i --name tc-data-build --network none --memory 256m --cpus 1 --pids-limit 64 --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 65534:65534 -v "$PWD:/b:ro" -w /b python:3.12-slim python /b/build_tasks.py > tasks.jsonl.tmp \
  && mv tasks.jsonl.tmp tasks.jsonl
