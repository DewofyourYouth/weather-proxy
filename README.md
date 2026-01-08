# Weather Proxy Service

This is a production-ready FastAPI service that acts as a proxy to the [Open-Meteo](https://open-meteo.com/) weather API. It includes Redis-based caching, observability features, structured logging, and basic CI/CD integration.

---

## Features

- `GET /weather?city=CityName`: Returns current weather (cached or fresh).
- `GET /health`: Returns service health status.
- Caching: Redis-backed, with configurable TTL per city.
- Observability: Structured logging, request tracing, and metrics support.
- Resilience: Retry logic and graceful upstream error handling.
- Containerized: Dockerfile and docker-compose for easy local setup.
- Tests: Unit and integration test coverage with pytest and test doubles.
- CI-ready: Includes configuration for linting, testing, and Docker builds.

---

## Python Version

> Developed and tested with Python 3.12

---

## Quickstart

### Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```
## Run with Docker

Build and start the application along with its dependencies (Redis):

```bash
docker compose up --build
```

The API will be available at:

```
http://localhost:8000
```

---

## Tests

Run the full test suite with:

```bash
pytest
```

The test suite includes:

- **Unit tests** for core business logic (e.g. city normalization, cache behavior)
- **Integration tests** that verify API endpoints while mocking the upstream weather provider

---

## Endpoints

| Method | Path                 | Description                           |
| ------ | -------------------- | ------------------------------------- |
| GET    | `/weather?city=City` | Returns weather data for a city       |
| GET    | `/health`            | Returns service and dependency status |
| GET    | `/metrics`           | Prometheus metrics                    |

---

## Environment Variables

| Variable      | Default | Description                    |
| ------------- | ------- | ------------------------------ |
| `REDIS_HOST`  | redis   | Redis hostname                 |
| `REDIS_PORT`  | 6379    | Redis port                     |
| `REDIS_DB`    | 0       | Redis database index           |
| `WEATHER_TTL` | 600     | Weather cache expiration (sec) |

---

## Architectural Decisions

- **FastAPI** was selected for its async support, type hints, and rapid development.
- **Redis** is used as a high-performance caching layer to minimize upstream calls.
- **Structured logging** is implemented using `structlog`, with request tracing enabled via unique request IDs.
- **City name resolution** is done via Open-Meteo’s geocoding API to obtain latitude/longitude.
- **Metrics endpoint** (`/metrics`) exposes Prometheus-compatible data such as request latency and cache hit rates.
- **Graceful shutdown** uvicorn handles SIGTERM gracefully by default. Application shutdown events are available for cleanup (not yet customized).

---

## Improvements (Given More Time)

- Implement authentication and request throttling for external-facing environments.
- Disambiguate cities by supporting country and state parameters.
- Improve caching strategy by adjusting TTL based on weather volatility.
- Add support for batch querying multiple cities.
- Provide Helm chart and Kubernetes manifests for easy deployment.
- Deploy the service publicly and provide a live demo link.

---

## Bonus Points

- [x] Docker and Docker Compose support
- [x] Structured logging and observability (`/metrics` exposed for Prometheus)
- [x] Health checks for Redis and upstream API
- [x] CI-ready (linting, testing, Docker image build)
- [ ] Helm chart not included
- [ ] Public deployment not included
