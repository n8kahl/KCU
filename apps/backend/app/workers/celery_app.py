from __future__ import annotations

from celery import Celery

from app.core.settings import settings

broker_url = settings.redis_url or "redis://localhost:6379/0"
app = Celery("kcu", broker=broker_url, backend=broker_url)
app.conf.beat_schedule = {
    "ingest-candles": {"task": "app.workers.tasks.ingest_candles", "schedule": 30.0},
    "poll-options": {"task": "app.workers.tasks.poll_options", "schedule": 15.0},
}
