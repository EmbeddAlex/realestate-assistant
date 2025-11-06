#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for Ollama at ${OLLAMA_HOST} ..."
# Wait for Ollama to be ready
until curl -fsS "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; do
  echo "  ... Ollama not ready yet, retrying ..."
  sleep 2
done

# Pull model via API if not present (idempotent)
MODEL="${OLLAMA_MODEL:-llama3.1}"
echo "Ensuring model is available: ${MODEL}"
# The pull call streams progress; we don't need to parse, just trigger it
curl -fsS -X POST "${OLLAMA_HOST}/api/pull" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"${MODEL}\"}" \
  || true

echo "Launching Streamlit on port ${STREAMLIT_SERVER_PORT:-8501} ..."
exec python -m streamlit run /app/apps/app.py --server.port=${STREAMLIT_SERVER_PORT:-8501} --server.headless=${STREAMLIT_SERVER_HEADLESS:-true}
