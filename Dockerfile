# Real Estate Assistant (offline) — App image
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy project files (adjust if your structure differs)
# Expecting these in the build context:
#  - app.py
#  - engine.py
#  - properties.csv
#  - requirements.txt
#  - start.sh (entrypoint)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/app.py engine.py properties.csv start.sh ./
RUN chmod +x /app/start.sh

# Env: point to the Ollama container host (defined in docker-compose)
ENV OLLAMA_HOST=http://ollama:11434
# Default model (override via .env or compose)
ENV OLLAMA_MODEL=llama3.1
# Streamlit basics
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

# Start script waits for Ollama, requests a model pull via API, then starts Streamlit
ENTRYPOINT ["/app/start.sh"]
