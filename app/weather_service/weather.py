from pydantic import BaseModel

import httpx


class City(BaseModel):
    name: str
    country_code: str
    latitude: float
    longitude: float


def get_city_data_from_api(city_name: str) -> City:
    """Return data about specific city."""
    req = httpx.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}")
    resp = req.json()["results"][0]
    return City(
        name=resp["name"],
        country_code=resp["country_code"],
        latitude=resp["latitude"],
        longitude=resp["longitude"],
    )


def get_weather_data_from_api(city: City):
    """Return weather data about a specific city."""
    try:
        return httpx.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={city.latitude}&longitude={city.longitude}&current_weather=true"
        ).json()
    except KeyError:
        raise Exception("Unknown city name.")


def get_weather(city_name: str):
    """Return weather data about a specific city."""
    # TODO check if the city already exists in the cache

    city = get_city_data_from_api(city_name)
    return get_weather_data_from_api(city)
