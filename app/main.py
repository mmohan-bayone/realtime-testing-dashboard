import asyncio
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import repository, schemas
from .database import Base, engine, get_db, SessionLocal
from .models import TestCaseResult
from .realtime import ConnectionManager
from .settings import AUTO_CREATE_SCHEMA, CORS_ORIGINS

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIST_DIR = PROJECT_DIR / 'frontend' / 'dist'
FRONTEND_INDEX_PATH = FRONTEND_DIST_DIR / 'index.html'

app = FastAPI(title='QA Real-Time Testing Dashboard')
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
if FRONTEND_DIST_DIR.exists():
    app.mount('/assets', StaticFiles(directory=FRONTEND_DIST_DIR / 'assets'), name='frontend-assets')
manager = ConnectionManager()


@app.on_event('startup')
def startup():
    if AUTO_CREATE_SCHEMA:
        Base.metadata.create_all(bind=engine)


@app.get('/', response_class=HTMLResponse)
def index():
    if FRONTEND_INDEX_PATH.exists():
        return FileResponse(FRONTEND_INDEX_PATH)
    html_path = BASE_DIR / 'templates' / 'index.html'
    return html_path.read_text(encoding='utf-8')


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/summary')
def summary(db: Session = Depends(get_db)):
    return repository.get_summary(db)


@app.get('/api/runs', response_model=list[schemas.TestRunResponse])
def runs(limit: int = 10, db: Session = Depends(get_db)):
    return repository.get_runs(db, limit)


@app.post('/api/runs', response_model=schemas.TestRunResponse)
async def create_run(payload: schemas.TestRunCreate, db: Session = Depends(get_db)):
    run = repository.create_run(db, payload)
    await manager.broadcast({'event': 'run_created', 'summary': repository.get_summary(db)})
    return run


@app.post('/api/cases/{case_id}/status')
async def update_case(case_id: int, payload: dict, db: Session = Depends(get_db)):
    run = repository.update_case_status(
        db,
        case_id=case_id,
        status=payload['status'],
        duration_ms=payload.get('duration_ms'),
        defect_id=payload.get('defect_id'),
    )
    if not run:
        raise HTTPException(status_code=404, detail='Test case not found')
    await manager.broadcast({'event': 'case_updated', 'summary': repository.get_summary(db), 'run_id': run.id})
    return {'message': 'updated', 'run_id': run.id}


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    db = SessionLocal()
    try:
        await websocket.send_json({'event': 'initial', 'summary': repository.get_summary(db)})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        db.close()


async def simulator_loop():
    from random import choice, randint

    await asyncio.sleep(2)
    while True:
        db = SessionLocal()
        try:
            running_cases = db.query(TestCaseResult).filter(TestCaseResult.status == 'RUNNING').all()
            if running_cases:
                candidate = choice(running_cases)
                outcome = choice(['PASSED', 'PASSED', 'FAILED', 'BLOCKED'])
                defect_id = f'DEF-{randint(101, 130)}' if outcome in {'FAILED', 'BLOCKED'} else None
                repository.update_case_status(
                    db,
                    case_id=candidate.id,
                    status=outcome,
                    duration_ms=randint(1000, 12000),
                    defect_id=defect_id,
                )
                await manager.broadcast({'event': 'simulation_tick', 'summary': repository.get_summary(db)})
        finally:
            db.close()
        await asyncio.sleep(3)


@app.on_event('startup')
async def start_simulator():
    asyncio.create_task(simulator_loop())


@app.get('/{full_path:path}')
def spa_fallback(full_path: str):
    if full_path.startswith(('api/', 'ws', 'static/', 'docs', 'redoc', 'openapi.json')):
        raise HTTPException(status_code=404, detail='Not found')
    if FRONTEND_INDEX_PATH.exists():
        return FileResponse(FRONTEND_INDEX_PATH)
    raise HTTPException(status_code=404, detail='Not found')
