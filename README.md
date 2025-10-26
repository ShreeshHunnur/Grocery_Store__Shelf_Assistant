# Retail Shelf Assistant

A voice-enabled retail assistant that helps customers find product locations and get product information using a local LLM and an SQLite product catalog. This README explains how to clone, set up, seed the database, run the backend, and run the Electron desktop wrapper on Windows (and how to run on Linux/macOS).

---

## Prerequisites

- Python 3.11+ (3.12 recommended). Ensure `python` on PATH points to the correct interpreter.
- Git
- Node.js + npm (only required for the Electron wrapper)
- Optional: CUDA-capable GPU and appropriate PyTorch build for local LLMs (if you plan to run large models locally).

Note: Some optional packages (FAISS) can be platform-sensitive on Windows. See the "Optional: Vector search / FAISS" section.

---

## Clone the repository

```powershell
git clone https://your.git.url/repo.git
cd grocery_assistant_project
```

---

## Create and activate a Python virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux (bash):

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Install Python dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Notes:
- On Windows, `faiss-cpu` wheels may be limited for some Python versions. If you need FAISS, try a pip-installable version (for example `faiss-cpu==1.12.0`) or use conda: `conda install -c conda-forge faiss-cpu`.
- If you plan to run local LLMs (Mistral/other large models), install `torch` with the appropriate CUDA variant per the PyTorch instructions.

---

## Initialize or regenerate the product database

This project ships with a deterministic seed generator to create a realistic store catalog in `data/products.db`.

To (re)generate the database (default: 1000 products):

```powershell
python .\database\seed_data.py --products 1000 --output .\data\products.db
```

Notes:
- Running the seed script will overwrite/create the `data/products.db` file at the path you pass with `--output`.
- If you want to start from a clean slate you can delete the file first:

```powershell
Remove-Item .\data\products.db -Force
```

---

## Optional: download models (STT / large LLMs)

- Whisper STT (if used):

```powershell
python -c "import whisper; whisper.load_model('base')"
```

- Local LLM (Mistral example): this will download large model files (several GB). Only needed if using local inference.

```powershell
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.1'); AutoModelForCausalLM.from_pretrained('mistralai/Mistral-7B-Instruct-v0.1')"
```

If you don't plan to run local LLMs you can configure the project to use a remote LLM/backend — see `config/settings.py`.

---

## Run the backend API (development)

Start the FastAPI app using `uvicorn` (from repo root; with virtualenv activated):

```powershell
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -Method Get
```

API endpoints (short):
- `POST /api/v1/ask` - text queries (JSON: {"query":"...","session_id":"..."})
- `POST /api/v1/ask-voice` - multipart upload for audio
- `GET /health` - health status

---

## Run the web UI (browser)

When the backend is running, open `http://127.0.0.1:8000/ui` in your browser to access the UI.

---

## Run as a desktop app (Electron) — Windows (dev)

The `electron/` folder contains a lightweight wrapper that spawns the Python backend and loads the UI.

1. Ensure Python venv is activated and backend dependencies are installed (see above).
2. From a PowerShell prompt in the repository root, start Electron:

```powershell
cd electron
npm install
npm start
```

Notes:
- The Electron main script spawns `scripts/start_server.py` using the `python` executable in PATH. Set `PYTHON_EXECUTABLE` if you need a specific interpreter.
- Packaging a single executable requires bundling a Python runtime and is out of scope for this repo; consider `electron-builder` plus a bundled Python installer.

---

## Troubleshooting tips

- If the app returns product names for generic informational queries (e.g. "what is 2 + 2"), restart the server after pulling the latest code — recent changes ensure information intents do not query the product DB.
- PowerShell `curl` gotchas: use `Invoke-RestMethod` or `curl.exe` directly when posting JSON with headers to avoid PowerShell header-binding issues.
- FAISS install errors on Windows: try `pip install faiss-cpu==1.12.0` or use conda `conda install -c conda-forge faiss-cpu`.
- If embedding/FAISS build fails during seeding, the script will skip vector index creation but still generate the DB and FTS index.

---

## Development and testing

- Run unit tests (from repo root; venv active):

```powershell
pytest
```

- Smoke tests and demo scripts are in the `scripts/` folder (e.g., `scripts/test_api_contracts.py`, `scripts/start_server.py`).

---

## Important files and where to look

- `database/schema.sql` — DB schema
- `database/seed_data.py` — deterministic data generator
- `src/api/` — FastAPI app, routes, orchestrator
- `src/services/` — DB queries, LLM service, audio I/O
- `electron/` — Electron wrapper to run desktop app

---

If you'd like, I can also:
- add a short PowerShell helper script `scripts/run_dev.ps1` that activates the venv and launches Electron;
- add a short `PACKAGING.md` that outlines options for bundling Python with Electron on Windows.

Thank you — tell me which of the optional helpers you'd like next.
