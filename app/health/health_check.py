"""Health checks for Redis and the external weather API."""

import httpx

from app.logging_config import logger
from app.models.health import ServiceStatus
from app.redis_cache.cache import redis_client


def is_redis_available() -> ServiceStatus:
    """Check Redis connectivity.

    Returns:
        ServiceStatus.available when Redis responds, else not_available.
    """
    try:
        redis_client.ping()
        logger.info("REDIS CONNECTED")
        return ServiceStatus.available
    except Exception as e:
        logger.error("REDIS UNAVAILABLE")
        return ServiceStatus.not_available


async def is_weather_api_available() -> bool:
    """Check the external weather API for availability.

    Returns:
        True if the API responds with current weather data.
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": 51.5, "longitude": 0.12, "current_weather": True},
            )
            return response.status_code == 200 and "current_weather" in response.json()
    except Exception:
        return False
