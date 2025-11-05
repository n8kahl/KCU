# KCU LTP Backend

Python 3.11+ FastAPI service powering the probabilistic admin copilot. It exposes REST + WebSocket APIs, Celery-driven ingestion, and snapshot persistence.

## Key features

- Async FastAPI w/ structured logging, API key auth, and error redaction
- SQLAlchemy 2.0 async models for candles, levels, option snapshots, and decision snapshots
- Celery worker + beat for ingest, scoring, and Discord alerts
- Domain layer covering features, scoring, regimes, options health, contract picker, what-if engine
- WebSocket hub broadcasting tile updates to the frontend

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

## Testing

```bash
pytest --cov=app/domain --cov=app/services
```

## Celery

```bash
celery -A app.workers.celery_app.app worker -l INFO
celery -A app.workers.celery_app.app beat -l INFO
```

## Environment variables

See `.env.example` for required values (e.g., `OPTIONS_DATA_ENABLED` to toggle Massive options-chain fetches). Never commit secrets; Railway manages runtime secrets.

### Railway deployment checklist

- **Core envs** (Backend service):
  - `PORT=3001`
  - `DATABASE_URL`, `REDIS_URL`
  - `MASSIVE_API_KEY` (live data), `SERVICE_ENV=production`, `API_KEY=<admin token>`
  - `WATCHLIST=SPY,AAPL,MSFT,NVDA,QQQ,TSLA,AMZN,GOOGL`
  - `OPTIONS_DATA_ENABLED=true` (set `false` if options stream unavailable)
  - `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/<id>`
  - `FRONTEND_ORIGIN=https://your-frontend.up.railway.app` (comma-separated if multiple clients)
- **Frontend service** needs `VITE_BACKEND_URL=https://<backend>.up.railway.app` so the UI targets the deployed API.
- After deploy: hit `/api/health`, confirm `/api/tickers` returns watchlist, open the UI, expand a ticker, send an `Enter` alert, and verify it lands in Discord. The WebSocket stream should immediately reorder cards by grade/confidence when probabilities change.
