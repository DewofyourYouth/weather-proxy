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


def normalize_city_name(city_name: str):
    return city_name.lower().strip().replace(" ", "_")


class CityCache:
    def __init__(self, client):
        self.redis_client = client

    def save_city(self, city_name: str, city: City):
        """Save city data to Redis"""
        try:
            self.redis_client.set(
                f"city:{normalize_city_name(city_name)}", city.model_dump_json()
            )
        except RedisError as exc:
            logger.error("REDIS_SAVE_CITY_FAILED", city=city_name, error=str(exc))

    def get_city(self, city_name) -> City:
        """Get city data from Redis"""
        try:
            city = self.redis_client.get(f"city:{normalize_city_name(city_name)}")
        except RedisError as exc:
            logger.error("REDIS_GET_CITY_FAILED", city=city_name, error=str(exc))
            return None
        return City(**json.loads(city)) if city else None


class WeatherCache:
    def __init__(self, client):
        self.redis_client = client

    def save_weather(self, city_name: str, weather_data):
        """Save weather data to Redis"""
        city = normalize_city_name(city_name)
        try:
            self.redis_client.set(
                f"weather:{city}",
                Weather.from_api_response(city, weather_data).model_dump_json(),
            )
        except RedisError as exc:
            logger.error("REDIS_SAVE_WEATHER_FAILED", city=city_name, error=str(exc))

    def get_weather(self, city_name: str):
        """Get weather data from Redis"""
        try:
            weather = self.redis_client.get(f"weather:{normalize_city_name(city_name)}")
        except RedisError as exc:
            logger.error("REDIS_GET_WEATHER_FAILED", city=city_name, error=str(exc))
            return None
        return Weather(**json.loads(weather)) if weather else None


city_cache = partial(CityCache, client=redis_client)
weather_cache = partial(WeatherCache, client=redis_client)
