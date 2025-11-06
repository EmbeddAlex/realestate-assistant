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

From the folder containing Dockerfile

```bash
docker compose up --build
```
