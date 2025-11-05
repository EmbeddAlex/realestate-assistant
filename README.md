# Real Estate Assistant — Offline (Ollama) Demo

Runs **completely offline** using [Ollama](https://ollama.com) and a local model like `llama3.1` or `mistral`.

### Setup


```bash
cd /mnt/data/realestate-assistant-demo

# Install Ollama: https://ollama.com/download
ollama pull llama3.1      # or: ollama pull mistral
export OLLAMA_MODEL=llama3.1   # optional

pip install -r requirements.txt

# Streamlit UI
streamlit run apps/app.py

# or CLI
python apps/cli.py
```

## Dockerfile

From the folder containing Dockerfile, app.py, engine.py, properties.csv, start.sh

```bash
docker compose up --build
```

## Notes
- The app container does not embed models; Ollama service manages models in a named volume (ollama_models).
- start.sh triggers a pull via Ollama’s API for ${OLLAMA_MODEL} on startup; safe to run repeatedly.
- To switch models: set OLLAMA_MODEL in .env or compose env.