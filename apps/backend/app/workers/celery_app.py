from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.settings import settings

broker_url = settings.redis_url or "redis://localhost:6379/0"
app = Celery("kcu", broker=broker_url, backend=broker_url)
app.conf.beat_schedule = {
    "ingest-candles": {"task": "app.workers.tasks.ingest_candles", "schedule": 30.0},
    "poll-options": {"task": "app.workers.tasks.poll_options", "schedule": 15.0},
    "option-baselines": {
        "task": "app.workers.baselines.build_option_percentiles",
        "schedule": crontab(minute=30, hour=7),
    },
    "index-baselines": {
        "task": "app.workers.baselines.build_index_percentiles",
        "schedule": crontab(minute=0, hour=8),
    },
}

app.autodiscover_tasks(["app.workers"])
