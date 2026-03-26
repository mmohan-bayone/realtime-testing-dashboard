# Real-Time Testing Dashboard

A real-time QA observability dashboard with a FastAPI backend and a React frontend.

## Features

- Live updates over WebSocket (`/ws`)
- Run and case tracking (`/api/runs`, `/api/cases/{id}/status`)
- Dashboard summary aggregation (`/api/summary`)
- Module quality trends, environment spread, and KPI cards
- Demo simulator that auto-progresses running test cases
- Demo control to create synthetic runs instantly

## Tech stack

- Backend: FastAPI, SQLAlchemy, Alembic, Uvicorn
- Frontend: React + TypeScript + Vite
- Realtime transport: WebSocket

## Project structure

- `app/` - FastAPI app, models, repository, realtime manager, static/template fallback
- `migrations/` - Alembic migration scripts
- `scripts/seed_demo.py` - inserts sample data
- `frontend/` - React dashboard client
- `qa_dashboard.db` - SQLite database file
- `render.yaml` - Render Blueprint for backend + Postgres

## Local development

### 1) Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m scripts.seed_demo
```

### 2) Frontend setup

```bash
cd frontend
npm install
cd ..
```

### 3) Run in development mode (two terminals)

Terminal A (backend):

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal B (frontend):

```bash
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

Vite is configured to proxy:

- `/api` -> `http://127.0.0.1:8000`
- `/ws` -> `ws://127.0.0.1:8000`

Backend env vars:

- `DATABASE_URL` (default: `sqlite:///./qa_dashboard.db`)
- `CORS_ORIGINS` (comma-separated, example: `http://127.0.0.1:5173`)
- `AUTO_CREATE_SCHEMA` (`true` for local quick-start; set `false` in production with Alembic)

## Production-style run (FastAPI serves React build)

Build frontend:

```bash
cd frontend
npm run build
cd ..
```

Start backend:

```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

When `frontend/dist` exists, FastAPI serves the React app and asset bundle.

## Deploy as SaaS (Free tier): Vercel + Render

### A) Deploy backend and Postgres on Render

1. Push this project to a Git provider (GitHub/GitLab/Bitbucket).
2. In Render, create a new Blueprint deployment and point to this repo.
3. Render will read `render.yaml` and create:
   - `realtime-testing-dashboard-api` web service
   - `realtime-testing-dashboard-db` Postgres database
4. Update `CORS_ORIGINS` in Render after frontend deploy:
   - `https://<your-project>.vercel.app`

Backend startup command runs migrations before boot:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### B) Deploy frontend on Vercel

1. Import the `frontend/` directory as a Vercel project.
2. Set environment variable in Vercel:

```bash
VITE_API_BASE_URL=https://<your-render-service>.onrender.com
```

3. Build settings:
   - Build command: `npm run build`
   - Output directory: `dist`

### C) Verify production deployment

Run these checks after deploy:

- Open `https://<your-project>.vercel.app` and confirm dashboard loads.
- Confirm backend health: `https://<your-render-service>.onrender.com/api/health`.
- Click `Create Demo Test Run`; verify new run appears in the table.
- Keep the page open and confirm live updates continue via WebSocket.
- Restart backend in Render and verify data persists (Postgres-backed).

### D) Rollback and recovery

- Frontend rollback: redeploy a previous successful Vercel deployment.
- Backend rollback: redeploy previous Render service revision.
- DB protection: never drop production DB; use Alembic migrations for schema changes.

## API examples

### Create a run

```bash
curl -X POST http://127.0.0.1:8000/api/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "suite_name": "Nightly Regression",
    "environment": "QA",
    "build_version": "v2.1.0",
    "test_cases": [
      {"name": "Login", "module": "Auth", "status": "RUNNING", "duration_ms": 0},
      {"name": "Checkout", "module": "Checkout", "status": "RUNNING", "duration_ms": 0}
    ]
  }'
```

### Update a test case

```bash
curl -X POST http://127.0.0.1:8000/api/cases/1/status \
  -H 'Content-Type: application/json' \
  -d '{"status":"FAILED","duration_ms":2400,"defect_id":"DEF-201"}'
```
