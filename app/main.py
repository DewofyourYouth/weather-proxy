import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.health.health_check import is_redis_available, is_weather_api_available
from app.logging_config import logger
from app.models.health import Dependencies, HealthResponse, ServiceStatus
from app.models.weather import Weather
from app.weather_service.weather import (
    CityNotFoundError,
    ExternalAPIError,
    WeatherServiceError,
    get_weather,
)
from structlog.contextvars import bind_contextvars, clear_contextvars

app = FastAPI()

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["path"]
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    bind_contextvars(request_id=request_id)
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
    finally:
        duration_s = time.perf_counter() - start
        duration_ms = round(duration_s * 1000, 2)
        status_code = getattr(response, "status_code", 500)
        logger.info(
            "HTTP_REQUEST",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
        )
        REQUEST_COUNT.labels(
            method=request.method, path=request.url.path, status_code=status_code
        ).inc()
        REQUEST_LATENCY.labels(path=request.url.path).observe(duration_s)
        clear_contextvars()


@app.exception_handler(CityNotFoundError)
async def city_not_found_handler(request: Request, exc: CityNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ExternalAPIError)
async def external_api_error_handler(request: Request, exc: ExternalAPIError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(WeatherServiceError)
async def weather_service_error_handler(request: Request, exc: WeatherServiceError):
    return JSONResponse(status_code=500, content={"detail": "Unexpected error"})


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/weather")
async def get_weather_for_city(city_name: str) -> Weather:
    return get_weather(city_name)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    weather_api_available = await is_weather_api_available()
    return HealthResponse(
        status="ok",
        dependencies=Dependencies(
            weather_api=ServiceStatus.available
            if weather_api_available
            else ServiceStatus.not_available,
            redis=is_redis_available(),
        ),
    )


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
