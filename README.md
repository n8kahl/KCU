# KCU LTP — Probabilistic Admin Copilot

End-to-end Railway-ready project combining a FastAPI backend (PostgreSQL, Redis, Celery, WebSockets) with a React + Vite admin dashboard. It tracks confluence buckets, probability-to-action, human overrides, and streaming tiles for operators.

## Repository map

- `apps/backend`: FastAPI app, Celery workers, domain engines, pytest suite.
- `apps/frontend`: Vite + React + Tailwind dashboard with TanStack Query + WebSockets.
- `.github/workflows/ci.yml`: Dual pipeline for Python + Node (lint/test/build).

## Backend quickstart

```bash
cd apps/backend
python -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e .
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload

# optional: run the live data worker (requires MASSIVE_API_KEY, Redis URL)
celery -A app.workers.celery_app.app worker -l INFO
```

## Frontend quickstart

```bash
cd apps/frontend
npm install
npm run dev
```

## Railway deployment

1. **Create Postgres** → set `DATABASE_URL` on backend service.
2. **Create Redis** → set `REDIS_URL` on backend service (Celery broker/backend).
3. **Backend service**
   - Build: `python`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Required variables: `PORT=3001`, `DATABASE_URL`, `REDIS_URL`, `MASSIVE_API_KEY`, `FRONTEND_ORIGIN=https://kcu-ui-production.up.railway.app`, `SERVICE_ENV=production`, `API_KEY=<admin>`, `WATCHLIST=SPY,AAPL,MSFT,NVDA,QQQ,TSLA,AMZN,GOOGL`, optional `DISCORD_WEBHOOK_URL`.
4. **Frontend service**
   - Build: `node`
   - Start: `npm run preview -- --host --port $PORT`
   - Variables: `VITE_BACKEND_URL=https://kcu.up.railway.app`

Deploy backend first so Vite preview can target the production API URL for smoke tests.

## CI overview

The GitHub Actions workflow installs backend deps, runs `pytest --cov`, builds the FastAPI bundle, then installs frontend deps, runs `npm run lint`, `npm run test`, and `npm run build`.

## Observability & guardrails

- Structured JSON logs via structlog/loguru with API key redaction.
- API key auth on `/api/admin/*` plus rate safer defaults.
- WebSocket hub broadcasts tile deltas and periodic heartbeats.
- Celery schedules ingest workers so Railway can run worker dynos or separate service.

## LOCAL DEV

- Backend dev server: `cd apps/backend && make dev`
- Backend tests: `cd apps/backend && make test`
- Frontend dev server: `cd apps/frontend && npm run dev`
- Frontend tests: `cd apps/frontend && npm run test`
- Smoke health: `curl http://localhost:3001/api/health`

## Sprint Log

- **2025-11-04 · Sprint 1** — Massive WS ingestion online (SPX/NDX indices + option quotes), new realtime engine with ring buffers & MTF microstructure, ETF↔Index coupling, REST pipeline demoted to 60 s backfill, plan doc updated.
- **2025-11-04 · Sprint 2** — Added 90-day percentile baselines + nightly Celery jobs, percentile-aware penalties + LiquidityRiskScore v2, realtime options flicker tracking, CI widening logic, and persisted market-micro JSON for calibration.
