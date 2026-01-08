import json
from functools import partial

from redis import Redis

from app.models.weather import Weather
from app.weather_service.weather import City

redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)

def normalize_city_name(city_name: str):
    return city_name.lower().strip().replace(" ", "_")

class CityCache:
    def __init__(self, client):
        self.redis_client = client

    def save_city(self, city_name: str, city: City):
        """Save city data to Redis"""
        self.redis_client.set(f"city:{normalize_city_name(city_name)}", city.model_dump_json())

    def get_city(self, city_name) -> City:
        """Get city data from Redis"""
        city = self.redis_client.get(f"city:{normalize_city_name(city_name)}")
        return City(**json.loads(city)) if city else None

class WeatherCache:
    def __init__(self, client):
        self.redis_client = client

    def save_weather(self, city_name: str, weather_data):
        """Save weather data to Redis"""
        city = normalize_city_name(city_name)
        self.redis_client.set(f"weather:{city}", Weather.from_api_response(city, weather_data).model_dump_json())

    def get_weather(self, city_name: str):
        """Get weather data from Redis"""
        weather = self.redis_client.get(f"weather:{normalize_city_name(city_name)}")
        return Weather(**json.loads(weather)) if weather else None

city_cache = partial(CityCache, client=redis_client)
weather_cache = partial(WeatherCache, client=redis_client)