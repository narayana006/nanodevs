#!/usr/bin/env bash
# Measure the base model in a CPU-only container at a fixed memory limit.
# Usage: bench_container.sh MEM THREADS [GGUF_PATH]   e.g. bench_container.sh 22g 4
set -euo pipefail
MEM="${1:?memory e.g. 22g}"; THR="${2:?threads}"
GGUF="${3:-$HOME/.lmstudio/models/lmstudio-community/gemma-4-26B-A4B-it-GGUF/gemma-4-26B-A4B-it-Q4_K_M.gguf}"
NAME="nanodevs-bench-$MEM-$THR"
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" --memory "$MEM" --memory-swap "$MEM" --cpus "$THR" -p 127.0.0.1:8190:8080 \
  -v "$GGUF":/m/model.gguf:ro ghcr.io/ggml-org/llama.cpp:server \
  -m /m/model.gguf --host 0.0.0.0 --port 8080 -c 8192 -t "$THR" -np 1 --reasoning off >/dev/null
trap 'docker rm -f "$NAME" >/dev/null 2>&1' EXIT
T0=$(date +%s)
until curl -sf http://127.0.0.1:8190/health >/dev/null; do
  [ "$(docker inspect -f '{{.State.Running}}' "$NAME")" = true ] || { echo "container exited:"; docker logs "$NAME" 2>&1 | tail -5; docker inspect -f 'OOMKilled={{.State.OOMKilled}}' "$NAME"; exit 1; }
  sleep 3
done
echo "load_seconds=$(( $(date +%s) - T0 ))"
PROMPT="Write a python function that reverses a linked list, with a short docstring."
curl -s http://127.0.0.1:8190/v1/chat/completions -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys;print(json.dumps({'messages':[{'role':'user','content':sys.argv[1]}],'max_tokens':128,'temperature':0}))" "$PROMPT")" \
 | python3 -c "import json,sys;d=json.load(sys.stdin);t=d['timings'];print('pp_tok_s',round(t['prompt_per_second'],1),'tg_tok_s',round(t['predicted_per_second'],1))"
docker stats --no-stream --format 'mem_used={{.MemUsage}} cpu={{.CPUPerc}}' "$NAME"
