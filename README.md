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
- `DATA_SOURCE` (`demo` or `github`)
- `GITHUB_ACTIONS_INGEST_TOKEN` (required when `DATA_SOURCE=github`)

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

If Render shows **Deploy failed** during **Build** (exit code 1), open **Logs** for the failed deploy and fix the pip error first — a broken build means the API never runs reliably (curl/GitHub Actions will time out). This repo pins Python in [`runtime.txt`](runtime.txt) and in [`render.yaml`](render.yaml) (`PYTHON_VERSION`) so the build does not use **Python 3.14+** (missing wheels for `pydantic-core` → Rust/maturin build → fails on Render’s read-only filesystem).

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

## Real data from GitHub Actions (optional)

Set `DATA_SOURCE=github` on the backend and set a strong `GITHUB_ACTIONS_INGEST_TOKEN`.

In GitHub repo settings, add a secret:

- `DASHBOARD_INGEST_TOKEN`: same value as `GITHUB_ACTIONS_INGEST_TOKEN`

Then add a workflow step to POST results to the dashboard:

```yaml
name: Tests
on:
  push:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          # run your tests here and produce results you can map into JSON
          echo "ok"

      - name: Publish results to dashboard
        env:
          DASHBOARD_URL: https://realtime-testing-dashboard-api.onrender.com
          DASHBOARD_INGEST_TOKEN: ${{ secrets.DASHBOARD_INGEST_TOKEN }}
        run: |
          cat > payload.json <<'EOF'
          {
            "suite_name": "GitHub Actions CI",
            "environment": "CI",
            "build_version": "${{ github.sha }}",
            "test_cases": [
              {"name":"Example test 1","module":"CI","status":"PASSED","duration_ms":10},
              {"name":"Example test 2","module":"CI","status":"FAILED","duration_ms":12,"defect_id":"GH-ISSUE-123"}
            ]
          }
          EOF

          curl -sS -X POST "$DASHBOARD_URL/api/ingest/github-actions/run" \
            -H "Content-Type: application/json" \
            -H "X-Ingest-Token: $DASHBOARD_INGEST_TOKEN" \
            --data-binary @payload.json
```

Notes:
- In `DATA_SOURCE=github` mode, the UI demo button is hidden and `POST /api/runs` is disabled; ingestion must go through `/api/ingest/github-actions/run`.
- You can map your real test framework output into the `test_cases` array (name/module/status/duration/optional defect_id).
- **Playwright JSON reports** nest tests under `suite.specs[].tests[]` (not only `suite.tests[]`). Use the uploader in [`examples/playwright-report-to-dashboard.mjs`](examples/playwright-report-to-dashboard.mjs), which parses both shapes. If CI logs show `0 test case(s)` but tests ran, copy the latest script into your Playwright repo and re-run the workflow.

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
