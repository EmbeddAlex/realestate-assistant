# Real Estate Assistant (offline) — App image
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code (structured layout)
COPY src/ /app/src/
COPY apps/ /app/apps/
COPY data/properties.csv /app/data/properties.csv
COPY scripts/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Env for imports & runtime
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV OLLAMA_HOST=http://ollama:11434

ENV OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

ENTRYPOINT ["/app/start.sh"]