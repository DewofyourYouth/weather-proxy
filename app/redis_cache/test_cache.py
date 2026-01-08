import pytest
import fakeredis
from app.redis_cache.cache import *


@pytest.fixture
def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    client.flushall()
    return client


def test_normalize_city_name(fake_redis):
    assert normalize_city_name("New York") == "new_york"
    assert normalize_city_name("Tel Aviv") == "tel_aviv"
    assert normalize_city_name("Rio de Janeiro") == "rio_de_janeiro"


def test_save_city_to_cache(fake_redis):
    cache = CityCache(fake_redis)
    rio = "Rio de Janeiro"
    cache.save_city(
        rio,
        City(
            name="Rio de Janeiro",
            country_code="BR",
            latitude=-22.90642,
            longitude=-43.18223,
        ),
    )
    assert cache.get_city(rio) == City(
        name="Rio de Janeiro",
        country_code="BR",
        latitude=-22.90642,
        longitude=-43.18223,
    )


def test_get_city_cache_miss_returns_none(fake_redis):
    cache = CityCache(fake_redis)
    assert cache.get_city("Unknown City") is None


def test_save_weather_to_cache(fake_redis):
    cache = WeatherCache(fake_redis)
    weather_data = {
        "current_weather": {
            "time": "2024-01-01T00:00",
            "temperature": 10.5,
            "windspeed": 5.0,
            "winddirection": 180,
            "is_day": 1,
            "weathercode": 1,
        }
    }
    cache.save_weather("New York", weather_data)
    weather = cache.get_weather("New York")
    assert weather is not None
    assert weather.city == "new_york"
    assert weather.temperature_c == 10.5


def test_get_weather_cache_miss_returns_none(fake_redis):
    cache = WeatherCache(fake_redis)
    assert cache.get_weather("Unknown City") is None
