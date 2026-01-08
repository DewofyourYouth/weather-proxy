# Weather Proxy

Small FastAPI service that fetches city + weather data from Open-Meteo and caches results in Redis.

## Requirements

- Python 3.12
- Redis

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Run locally

```bash
# If you run Redis on localhost
export REDIS_HOST=localhost
uvicorn app.main:app --reload
```

## Run with Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Endpoints

- `GET /` health-style hello
- `GET /weather?city_name=London` returns current weather for the city
- `GET /health` shows dependency status

## Tests

```bash
pytest
```

## Environment variables

- `REDIS_HOST` (default: `redis`)
- `REDIS_PORT` (default: `6379`)
- `REDIS_DB` (default: `0`)
