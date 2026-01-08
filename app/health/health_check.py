import httpx

from app.logging_config import logger
from app.redis_cache.cache import redis_client


def is_redis_available():
    try:
        redis_client.ping()
        logger.info("REDIS CONNECTED")
        return "connected"
    except Exception as e:
        logger.error("REDIS UNAVAILABLE")
        return "unavailable"


async def is_weather_api_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": 51.5, "longitude": 0.12, "current_weather": True},
            )
            return response.status_code == 200 and "current_weather" in response.json()
    except Exception:
        return False
