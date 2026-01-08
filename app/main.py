from fastapi import FastAPI

from app.weather_service.weather import get_weather

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/weather")
async def get_weather_for_city(city_name: str):
    return get_weather(city_name)
