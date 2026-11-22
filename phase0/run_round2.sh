#!/bin/bash
# Round 2: 30 harder tasks on each model in turn (Metal GPU; pass rates do not depend on CPU vs GPU).
cd "$(dirname "$0")"
PORT=8083
run() {  # NAME FILE [extra server flags]
  NAME=$1; FILE=$2; shift 2
  echo "=== $NAME: starting server"
  llama-server -m "$FILE" -ngl 99 -c 12288 --host 127.0.0.1 --port $PORT "$@" > "results_server2_$NAME.log" 2>&1 &
  SPID=$!
  for s in $(seq 1 180); do
    curl -s "http://127.0.0.1:$PORT/health" | grep -q '"ok"' && break
    kill -0 $SPID 2>/dev/null || { echo "server died"; return 1; }
    sleep 1
  done
  python3 run_model2.py "$NAME" $PORT 3
  kill $SPID; wait $SPID 2>/dev/null
  echo "=== $NAME: done"
}
run gemma-4-26b-a4b-nothink "$HOME/.lmstudio/models/lmstudio-community/gemma-4-26B-A4B-it-GGUF/gemma-4-26B-A4B-it-Q4_K_M.gguf" --reasoning off
run devstral-small-2-24b "$(cd "$(dirname "$0")/.." && pwd)/models/mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf"
