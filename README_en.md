# Project Helper

Project Helper is a full-stack web app that helps developers understand unfamiliar GitHub repositories quickly.

It clones a GitHub repository, analyzes source files, caches completed reports in SQLite, streams progress to the browser with SSE, and provides an interactive source-code Q&A assistant with file-reading and code-search tools.

## Stack

- Backend: Python, FastAPI, LangChain, SQLite, OpenAI-compatible DeepSeek client
- Frontend: Vue 3, Vite, Markdown rendering, syntax highlighting

## Quick Start

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Set `DEEPSEEK_API_KEY` in `backend/.env` to enable DeepSeek-powered reports and Q&A. Without a key, the app still runs with deterministic local analysis.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`.

## Notes

- Cloned repositories are stored under `backend/data/repos`.
- Reports and chat history are cached in `backend/data/project_helper.db`.
- Only GitHub HTTPS repository URLs are accepted.
