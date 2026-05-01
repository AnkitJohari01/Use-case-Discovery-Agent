# ML Use Case Explorer App

This is a production-ready Web App consisting of a Streamlit frontend and a FastAPI backend designed to explore Traditional Machine Learning use cases. Result caching and LLM integration (Ollama / HuggingFace) is built-in.

## Prerequisites

- Python 3.9+ 
- (Optional) Local Ollama instance configured with `llama3.2` running on port 11434.
- (Optional) Hugging Face `HF_TOKEN` environment variable if local Ollama is not used.

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Backend

You can use the local server (Ollama). If you prefer Hugging Face's API, set your terminal environment variable first:

**Windows Command Prompt:**
```cmd
set HF_TOKEN=your_token_here
```
**Powershell:**
```powershell
$env:HF_TOKEN="your_token_here"
```

Start the backend:
```bash
uvicorn backend:app --reload --port 8000
```
*Note: The backend automatically handles 24-hour background refreshes using `APScheduler` linked to the FastAPI lifespan events.*

## Running the Frontend

Once the backend is live, open a new terminal window and run:

```bash
streamlit run frontend.py
```

## How It Works

- **Self-Update:** An in-memory cache maintains all usage data. The APScheduler triggers every 24h. Any keyword mapping older than 24h is pushed back through the LLM for re-generation.
- **Failovers:** The backend gracefully tries Ollama (local) first. If it cannot connect or the model errors, it falls back to HuggingFace Inference API (Mistral Instruct). If the rate limits hit on HF, a static fallback resolves cleanly avoiding app crashes.
