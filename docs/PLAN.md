# KCU LTP — Execution Plan

## Architecture Overview

- **Backend** (`apps/backend/app`): FastAPI + Celery, PostgreSQL (async SQLAlchemy) and Redis. Massive REST adapter already powers REST snapshots; upcoming WebSocket ingestion will drive real-time market microstructure with REST as a degradation/backfill path.
- **WebSockets**: `/ws/stream` (managed in `app/ws/manager.py`) broadcast `{"type":"tile","data": TileState}` messages that the frontend consumes. We will keep this schema stable while enriching the payload with market micro + managing context.
- **Frontend** (`apps/frontend`): React + Vite + Tailwind with TanStack Query. It already connects to the backend WS and falls back to REST polling; the new data will surface via upgraded tiles/drawers.
- **Settings**: `app/core/settings.py` exposes env vars (PORT, DATABASE_URL async, REDIS_URL, MASSIVE_API_KEY, etc.). CORS currently allows the production frontend plus localhost — we will leave this as-is.

REST polling remains for snapshots/backfill (cadence will drop to ~60s). The new streaming stack will ingest Massive WS (indices + option quotes) and merge live deltas into the tile state before broadcasting.

## Sprint Roadmap

| Sprint | Focus | Key Deliverables |
| --- | --- | --- |
| 1 | **WS-first real-time ingestion** | Massive WS adapter/client, index/option ring buffers (1s/1m), multi-timeframe microstructure metrics (minute thrust, micro-chop, ETF↔Index divergence), ETF↔Index coupling, and merge of real-time deltas into scoring while REST demoted to backfill. |
| 2 | **90-day baselines + LiquidityRiskScore v2** | Percentile storage (spread, flicker, IVR/VoV, thrust, divergence), nightly builder, percentile-aware penalties/bonuses, LiquidityRiskScore v2, and confidence-band widening tied to liquidity/microstructure stress. |
| 3 | **KCU Take-Profit Manager + Timing** | TP ladder with level snapping (ATR-derived targets aligned to premkt/prior/ORB/VWAP/rounds), EMA/ATR-based runner trail and continuation gating, Timing Considerations surfaced instead of hard blocks, and API wiring for managing state. |
| 4 | **Admin UI upgrades** | MTF matrix, Index Confluence strip, options liquidity micro-charts, Managing panel with TP ladder + runner sparkline, enriched What-If drawer, leveraging the streaming payload additions. |

### WS-First Data Flow

1. **Massive WS** delivers SPX/NDX minute aggregates, per-tick values, and selected SPX/NDX option quotes.
2. **Realtime engine** normalizes events, pushes them into bounded ring buffers, computes microstructure metrics (multi-timeframe), and calls `merge_realtime_into_tile` to update `TileState`.
3. **REST pipeline** (existing tile engine) runs at a slower interval to backfill missing data, persist snapshots, and guard against WS downtime.
4. **WebSocket hub** broadcasts coalesced tile updates (<5 Hz) to all clients; frontend renders live data with REST fallback for cold starts or reconnects.

### Sprint Log

| Sprint | Date | Summary |
| --- | --- | --- |
| _Phase 0_ | _TBD_ | Initial plan authored; no behavior changes yet. |
| Sprint 1 | 2025-11-04 | Massive WS ingestion, ring buffers, microstructure scoring merge, ETF↔Index coupling, REST demoted to 60s backfill. |
| Sprint 2 | 2025-11-04 | 90‑day percentile baselines, nightly Celery jobs, LiquidityRiskScore v2, percentile-aware penalties + CI widening, realtime options flicker metrics. |
