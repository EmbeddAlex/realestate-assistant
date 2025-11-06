#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for Ollama at ${OLLAMA_HOST} ..."
until curl -fsS "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; do
  echo "  ... Ollama not ready yet, retrying ..."
  sleep 2
done

MODEL="${OLLAMA_MODEL:-qwen2.5:3b-instruct-q4_K_M}"
echo "Ensuring model is available: ${MODEL}"

curl -fsS -X POST "${OLLAMA_HOST}/api/pull" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"${MODEL}\"}" \
  || true

echo "Launching Streamlit (apps/streamlit_app.py) on port ${STREAMLIT_SERVER_PORT:-8501} ..."
exec python -m streamlit run /app/apps/streamlit_app.py \
  --server.port="${STREAMLIT_SERVER_PORT:-8501}" \
  --server.headless="${STREAMLIT_SERVER_HEADLESS:-true}"