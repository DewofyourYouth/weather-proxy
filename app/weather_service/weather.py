import time

import httpx

from app.logging_config import logger
from app.models.city import City
from app.models.weather import Weather
from app.redis_cache.cache import city_cache, weather_cache

RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 0.3
RETRY_MAX_DELAY_S = 2.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class WeatherServiceError(Exception):
    pass


class CityNotFoundError(WeatherServiceError):
    pass


class ExternalAPIError(WeatherServiceError):
    pass


def _request_with_retry(
    *,
    url: str,
    params: dict,
    timeout: float,
    event_prefix: str,
    log_context: dict,
    error_message: str,
) -> httpx.Response:
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            response = httpx.get(url, params=params, timeout=timeout)
            logger.info(
                f"{event_prefix}_RESPONSE",
                **log_context,
                status=response.status_code,
                attempt=attempt,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            retryable = status_code in RETRYABLE_STATUS_CODES
            logger.error(
                f"{event_prefix}_BAD_STATUS",
                **log_context,
                status=status_code,
                attempt=attempt,
                retryable=retryable,
            )
            if not retryable or attempt == RETRY_ATTEMPTS:
                raise ExternalAPIError(error_message) from exc
        except httpx.RequestError as exc:
            logger.error(
                f"{event_prefix}_REQUEST_FAILED",
                **log_context,
                error=str(exc),
                attempt=attempt,
            )
            if attempt == RETRY_ATTEMPTS:
                raise ExternalAPIError(error_message) from exc

        delay = min(RETRY_BASE_DELAY_S * (2 ** (attempt - 1)), RETRY_MAX_DELAY_S)
        logger.info(
            f"{event_prefix}_RETRY",
            **log_context,
            attempt=attempt + 1,
            delay_s=delay,
        )
        time.sleep(delay)

    raise ExternalAPIError(error_message)


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
    response = _request_with_retry(
        url="https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city_name},
        timeout=5,
        event_prefix="CITY_LOOKUP",
        log_context={"city": city_name},
        error_message="City lookup failed",
    )

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
    response = _request_with_retry(
        url="https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": city.latitude,
            "longitude": city.longitude,
            "current_weather": True,
        },
        timeout=5,
        event_prefix="WEATHER",
        log_context={"city": city.name},
        error_message="Weather lookup failed",
    )

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
