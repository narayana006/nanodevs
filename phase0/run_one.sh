#!/bin/bash
# Usage: run_one.sh NAME MODEL_FILE [extra llama-server flags...]
cd "$(dirname "$0")"
NAME=$1; FILE=$2; shift 2
PORT=8082
llama-server -m "$FILE" -ngl 99 -c 8192 --host 127.0.0.1 --port $PORT "$@" > "results_server_$NAME.log" 2>&1 &
SPID=$!
for s in $(seq 1 180); do
  curl -s "http://127.0.0.1:$PORT/health" | grep -q '"ok"' && break
  kill -0 $SPID 2>/dev/null || { echo "server died"; exit 1; }
  sleep 1
done
python3 run_model.py "$NAME" $PORT 5
kill $SPID; wait $SPID 2>/dev/null
echo "=== $NAME done"
