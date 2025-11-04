FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e .

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 3001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]
