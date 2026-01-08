from fastapi import FastAPI

from app.health.health_check import is_redis_available, is_weather_api_available
from app.models.weather import Weather
from app.weather_service.weather import get_weather

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/weather")
async def get_weather_for_city(city_name: str) -> Weather:
    return get_weather(city_name)


@app.get("/health")
async def health():
    weather_api_available = await is_weather_api_available()
    return {
        "status": "ok",
        "dependencies": {
            "weather_api": "available" if weather_api_available else "not_available",
            "redis": is_redis_available(),
        },
    }
