import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "HTTP_REQUEST",
            method=request.method,
            path=request.url.path,
            status_code=getattr(response, "status_code", None),
            duration_ms=duration_ms,
        )
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
