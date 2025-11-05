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

1. **Provision data stores**
   - Create PostgreSQL → set `DATABASE_URL` on the backend.
   - Create Redis → set `REDIS_URL` (Celery broker + cache).
2. **Backend service** (apps/backend)
   - Build: `python`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Required env vars:
     - `PORT=3001`, `DATABASE_URL`, `REDIS_URL`, `MASSIVE_API_KEY`, `SERVICE_ENV=production`, `API_KEY=<admin token>`
     - `WATCHLIST=SPY,AAPL,MSFT,NVDA,QQQ,TSLA,AMZN,GOOGL`
     - `OPTIONS_DATA_ENABLED=true` (set `false` while options data warms up)
     - `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/<id>`
     - `FRONTEND_ORIGIN=https://your-frontend.up.railway.app` (comma-separated if multiple UI domains; drives CORS)
3. **Frontend service** (apps/frontend)
   - Build: `node`
   - Start: `npm run preview -- --host --port $PORT`
   - Env vars: `VITE_BACKEND_URL=https://<backend>.up.railway.app`

Deploy backend first so the UI can hit a live API. Make sure both Railway services share the same Discord webhook so one-tap alerts reach the channel.

### Railway smoke test

1. `curl https://<backend>.up.railway.app/api/health` → `status: ok`.
2. Open the frontend URL, confirm the heartbeat pill reads **Live** and the Market Clock/guideline chip matches the ET session.
3. Tiles should stream via WebSocket (grades update without reload). Expand a ticker → confirm Top 3 OTM contracts render with live mid/delta.
4. Click **Load Contract**, hit **Enter**, add a note, send → observe alert in Discord and the Active Trades panel shows the new entry with captured price and %PnL.

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

## API Endpoints

- `GET /api/health` – service heartbeat + baseline timestamps.
- `GET /api/tickers`, `GET /api/tickers/{symbol}/state` – REST fallback for tiles.
- `POST /api/what-if` – recalc probability under hypothetical deltas.
- `POST /api/admin/policy` / `POST /api/admin/override` – mode and per-symbol overrides (API key).
- `POST /api/positions/start` / `/stop` – trigger KCU Take-Profit Manager (API key).

## Sprint Log

- **2025-11-04 · Sprint 1** — Massive WS ingestion online (SPX/NDX indices + option quotes), new realtime engine with ring buffers & MTF microstructure, ETF↔Index coupling, REST pipeline demoted to 60 s backfill, plan doc updated.
- **2025-11-04 · Sprint 2** — Added 90-day percentile baselines + nightly Celery jobs, percentile-aware penalties + LiquidityRiskScore v2, realtime options flicker tracking, CI widening logic, and persisted market-micro JSON for calibration.
- **2025-11-04 · Sprint 3** — Introduced KCU Take-Profit Manager (level snapping, runner trail/extension), timing considerations chip, managing panel payloads, and secured `/api/positions` endpoints for human-in-the-loop starts/stops.
