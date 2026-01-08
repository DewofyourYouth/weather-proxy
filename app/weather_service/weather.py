import httpx

from app.logging_config import logger
from app.models.city import City
from app.models.weather import Weather
from app.redis_cache.cache import city_cache, weather_cache


class WeatherServiceError(Exception):
    pass


class CityNotFoundError(WeatherServiceError):
    pass


class ExternalAPIError(WeatherServiceError):
    pass


def get_city_data(city_name: str) -> City:
    """Return data about specific city."""
    cache = city_cache()
    if city := cache.get_city(city_name):
        logger.info("CACHED_CITY_HIT", city=city_name)
        return city
    city = get_city_from_api(city_name)
    cache.save_city(city_name, city)
    return city


def get_city_from_api(city_name: str) -> City:
    logger.info("CACHE_CITY_MISS", city=city_name)
    try:
        response = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city_name},
            timeout=5,
        )
        logger.info("CITY_LOOKUP_RESPONSE", city=city_name, status=response.status_code)
        response.raise_for_status()
    except httpx.RequestError as exc:
        logger.error("CITY_LOOKUP_REQUEST_FAILED", city=city_name, error=str(exc))
        raise ExternalAPIError("City lookup failed") from exc
    except httpx.HTTPStatusError as exc:
        logger.error(
            "CITY_LOOKUP_BAD_STATUS", city=city_name, status=exc.response.status_code
        )
        raise ExternalAPIError("City lookup failed") from exc

    try:
        results = response.json().get("results") or []
        if not results:
            raise CityNotFoundError(f"City not found: {city_name}")
        data = results[0]
        return City(
            name=data["name"],
            country_code=data["country_code"],
            latitude=data["latitude"],
            longitude=data["longitude"],
        )
    except (TypeError, KeyError) as exc:
        logger.error("CITY_LOOKUP_BAD_PAYLOAD", city=city_name, error=str(exc))
        raise ExternalAPIError("City lookup failed") from exc


def get_weather_data_from_api(city: City) -> Weather:
    """Return weather data about a specific city."""
    logger.info("CACHED_WEATHER_MISS", city=city.name)
    try:
        response = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": city.latitude,
                "longitude": city.longitude,
                "current_weather": True,
            },
            timeout=5,
        )
        logger.info("WEATHER_RESPONSE", city=city.name, status=response.status_code)
        response.raise_for_status()
    except httpx.RequestError as exc:
        logger.error("WEATHER_REQUEST_FAILED", city=city.name, error=str(exc))
        raise ExternalAPIError("Weather lookup failed") from exc
    except httpx.HTTPStatusError as exc:
        logger.error(
            "WEATHER_BAD_STATUS", city=city.name, status=exc.response.status_code
        )
        raise ExternalAPIError("Weather lookup failed") from exc

    data = response.json()
    if "current_weather" not in data:
        logger.error("WEATHER_BAD_PAYLOAD", city=city.name)
        raise ExternalAPIError("Weather lookup failed")
    return data


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
