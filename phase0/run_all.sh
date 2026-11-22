#!/bin/bash
# Runs the bug-fix tasks on each model in turn (one server at a time, Metal GPU for speed;
# pass rates do not depend on CPU vs GPU). Usage: run_all.sh
cd "$(dirname "$0")"
declare -a NAMES=("devstral-small-2-24b" "gemma-4-26b-a4b")
declare -a FILES=("$(cd "$(dirname "$0")/.." && pwd)/models/mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf" \
                  "$HOME/.lmstudio/models/lmstudio-community/gemma-4-26B-A4B-it-GGUF/gemma-4-26B-A4B-it-Q4_K_M.gguf")
PORT=8081
for i in 0 1; do
  echo "=== ${NAMES[$i]}: starting server"
  llama-server -m "${FILES[$i]}" -ngl 99 -c 8192 --host 127.0.0.1 --port $PORT > "results_server_${NAMES[$i]}.log" 2>&1 &
  SPID=$!
  for s in $(seq 1 180); do
    curl -s "http://127.0.0.1:$PORT/health" | grep -q '"ok"' && break
    kill -0 $SPID 2>/dev/null || { echo "server died, see results_server_${NAMES[$i]}.log"; break; }
    sleep 1
  done
  python3 run_model.py "${NAMES[$i]}" $PORT 5
  kill $SPID; wait $SPID 2>/dev/null
  echo "=== ${NAMES[$i]}: done"
done
