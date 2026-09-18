# Enterprise GLiNER NER

Product-grade named entity recognition platform built with:

- **Backend**: FastAPI + SQLAlchemy + GLiNER + deterministic PII extractors (`venv`)
- **Frontend**: Vite + React (admin / user roles, upload progress, history)

## Features

- Upload **files**, **folders**, or **archives** (any extension; text is extracted when possible)
- Unlimited file count; **100 MB per file**
- Hybrid detection: contextual **GLiNER** + Azure/Presidio-style **PII regex**
- Scan progress bar (`processed / remaining / percent`)
- History / activity logs
- Roles:
  - **user** — sees own uploads
  - **admin** — sees all uploads and can approve users

## Quick start

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\venv\Scripts\python.exe reset_users.py
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173/login

API docs: http://127.0.0.1:8001/docs

> Note: if port 8000 is already used by another project, this stack uses **8001**.

### Demo accounts

| Role  | Email           | Password  |
|-------|-----------------|-----------|
| Admin | admin@test.com  | Admin@123 |
| User  | user@test.com   | User@123  |

## Training (enterprise dataset)

```powershell
cd backend
.\venv\Scripts\python.exe training\run_enterprise_pipeline.py --samples 12000 --skip-train
.\venv\Scripts\python.exe training\train_enterprise.py --base-model urchade/gliner_small-v2.1 --max-steps 800 --batch-size 2
.\venv\Scripts\python.exe training\evaluate_model_v2.py --model checkpoints\best_model --test training\datasets\test.json
```

Checkpoints are written to `backend/checkpoints/best_model` and auto-loaded by the API.

## OpenAI comparison

Add to `backend/.env`:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

On a batch detail page, use **Run comparison** to see entities detected by both engines, GLiNER only, OpenAI only, and type differences. Click any entity text to list filenames only (never file content).
