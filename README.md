# Real Estate Assistant — Offline (Ollama) Demo

Runs **completely offline** using [Ollama](https://ollama.com) and a local model like `llama3.1` or `mistral`.

### Setup


```bash
# Install Ollama: https://ollama.com/download

ollama pull qwen2.5:3b-instruct-q4_K_M # or: ollama pull llama3.1

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
