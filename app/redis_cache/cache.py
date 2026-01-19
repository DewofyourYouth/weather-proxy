"""Redis cache helpers for city and weather data."""

import json
import os
from functools import partial

from redis import Redis
from redis.exceptions import RedisError

from app.logging_config import logger
from app.models.city import City
from app.models.weather import Weather

print("REDIS HOST: ", os.getenv("REDIS_HOST"))

redis_client = Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=True,
)
WEATHER_TTL_S = int(os.getenv("WEATHER_TTL", "0"))


def normalize_city_name(city_name: str):
    """Normalize city names for stable cache keys.

    Args:
        city_name: Raw city name string.

    Returns:
        Normalized city name for Redis keys.
    """
    return city_name.lower().strip().replace(" ", "_")


class CityCache:
    """Cache wrapper for storing and retrieving City models."""

    def __init__(self, client):
        self.redis_client = client

    def save_city(self, city_name: str, city: City):
        """Save city data to Redis.

        Args:
            city_name: City name key.
            city: City model to serialize.
        """
        try:
            self.redis_client.set(
                f"city:{normalize_city_name(city_name)}", city.model_dump_json()
            )
        except RedisError as exc:
            logger.error("REDIS_SAVE_CITY_FAILED", city=city_name, error=str(exc))

    def get_city(self, city_name) -> City:
        """Get city data from Redis.

        Args:
            city_name: City name key.

        Returns:
            City model if present, otherwise None.
        """
        try:
            city = self.redis_client.get(f"city:{normalize_city_name(city_name)}")
        except RedisError as exc:
            logger.error("REDIS_GET_CITY_FAILED", city=city_name, error=str(exc))
            return None
        return City(**json.loads(city)) if city else None


class WeatherCache:
    """Cache wrapper for storing and retrieving Weather models."""

    def __init__(self, client):
        self.redis_client: Redis = client

    def save_weather(self, city_name: str, weather_data):
        """Save weather data to Redis.

        Args:
            city_name: City name key.
            weather_data: Raw API payload to serialize.
        """
        city = normalize_city_name(city_name)
        try:
            ttl = WEATHER_TTL_S if WEATHER_TTL_S > 0 else None
            self.redis_client.set(
                f"weather:{city}",
                Weather.from_api_response(city, weather_data).model_dump_json(),
                ex=ttl,
            )
        except RedisError as exc:
            logger.error("REDIS_SAVE_WEATHER_FAILED", city=city_name, error=str(exc))

    def get_weather(self, city_name: str):
        """Get weather data from Redis.

        Args:
            city_name: City name key.

        Returns:
            Weather model if present, otherwise None.
        """
        try:
            weather = self.redis_client.get(f"weather:{normalize_city_name(city_name)}")
        except RedisError as exc:
            logger.error("REDIS_GET_WEATHER_FAILED", city=city_name, error=str(exc))
            return None
        return Weather(**json.loads(weather)) if weather else None


city_cache = partial(CityCache, client=redis_client)
weather_cache = partial(WeatherCache, client=redis_client)
