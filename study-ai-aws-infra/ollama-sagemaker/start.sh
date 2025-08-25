#!/usr/bin/env bash
set -euo pipefail

# Defaults (can be overridden at runtime)
: "${PORT:=8080}"
: "${OLLAMA_HOST:=0.0.0.0}"
: "${OLLAMA_PORT:=11434}"
: "${OLLAMA_MODEL:=llama3:8b-instruct}"
: "${OLLAMA_PRELOAD:=true}"
: "${GUNICORN_WORKERS:=1}"
: "${GUNICORN_THREADS:=4}"
: "${GUNICORN_TIMEOUT:=120}"

echo "[start.sh] Starting Ollama server (host=$OLLAMA_HOST port=$OLLAMA_PORT)"
# Start Ollama server in background
ollama serve &
OLLAMA_PID=$!

# Wait for port to become ready
echo "[start.sh] Waiting for Ollama on :$OLLAMA_PORT ..."
for i in {1..60}; do
  if curl -sf "http://127.0.0.1:${OLLAMA_PORT}/api/tags" >/dev/null 2>&1; then
    echo "[start.sh] Ollama is up"
    break
  fi
  sleep 1
done

# Pre-pull model if OLLAMA_PRELOAD is true
if [[ "${OLLAMA_PRELOAD}" == "true" ]]; then
  echo "[start.sh] Pre-loading model '$OLLAMA_MODEL'"
  curl -s -X POST "http://127.0.0.1:${OLLAMA_PORT}/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${OLLAMA_MODEL}\"}" >/dev/null 2>&1 || true
fi

# Start gunicorn for the Flask app (SageMaker expects /ping + /invocations)
echo "[start.sh] Starting gunicorn on :$PORT"
exec gunicorn \
  --workers "${GUNICORN_WORKERS}" \
  --threads "${GUNICORN_THREADS}" \
  --timeout "${GUNICORN_TIMEOUT}" \
  --bind "0.0.0.0:${PORT}" \
  inference:app

