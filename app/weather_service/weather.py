import httpx

from app.models.city import City
from app.models.weather import Weather
from app.redis_cache.cache import city_cache, weather_cache

from app.logging_config import logger


def get_city_data(city_name: str) -> City:
    """Return data about specific city."""
    cache = city_cache()
    if city := cache.get_city(city_name):
        logger.info("CACHED_CITY_HIT", city=city_name)
        return city
    city = get_city_from_api(city, city_name)
    cache.save_city(city_name, city)
    return city


def get_city_from_api(city: City, city_name: str) -> City:
    logger.info("CACHE_CITY_MISS", city=city_name)
    req = httpx.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}")
    resp = req.json()["results"][0]
    city = City(
        name=resp["name"],
        country_code=resp["country_code"],
        latitude=resp["latitude"],
        longitude=resp["longitude"],
    )
    return city


def get_weather_data_from_api(city: City) -> Weather:
    """Return weather data about a specific city."""
    logger.info("CACHED_WEATHER_MISS", city=city.name)
    response = httpx.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={city.latitude}&longitude={city.longitude}&current_weather=true"
    ).json()
    return response


def get_weather(city_name: str):
    """Return weather data about a specific city."""
    city = get_city_data(city_name)
    cache = weather_cache()
    if weather_data := cache.get_weather(city_name):
        logger.info(
            "CACHED_WEATHER_HIT",
            city=city_name,
        )
        return weather_data
    weather_data = get_weather_data_from_api(city)
    cache.save_weather(city_name, weather_data)
    return Weather.from_api_response(city_name, weather_data)
