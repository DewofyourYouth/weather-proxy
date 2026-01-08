from fastapi.testclient import TestClient

from app.main import app
from app.models.health import RedisStatus
from app.models.weather import Weather
from app.weather_service.weather import CityNotFoundError, ExternalAPIError


def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_weather_success(monkeypatch):
    client = TestClient(app)
    weather = Weather(
        city="london",
        time="2024-01-01T00:00:00",
        temperature_c=12.3,
        windspeed_kmh=5.1,
        winddirection_deg=180,
        is_day=True,
        weather_code=1,
        weather_description="Mainly clear",
    )

    def fake_get_weather(city_name: str):
        return weather

    monkeypatch.setattr("app.main.get_weather", fake_get_weather)
    response = client.get("/weather", params={"city_name": "London"})
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "london"
    assert data["temperature_c"] == 12.3


def test_get_weather_city_not_found(monkeypatch):
    client = TestClient(app)

    def fake_get_weather(city_name: str):
        raise CityNotFoundError("City not found: Nowhere")

    monkeypatch.setattr("app.main.get_weather", fake_get_weather)
    response = client.get("/weather", params={"city_name": "Nowhere"})
    assert response.status_code == 404
    assert response.json()["detail"] == "City not found: Nowhere"


def test_get_weather_external_api_error(monkeypatch):
    client = TestClient(app)

    def fake_get_weather(city_name: str):
        raise ExternalAPIError("Weather lookup failed")

    monkeypatch.setattr("app.main.get_weather", fake_get_weather)
    response = client.get("/weather", params={"city_name": "London"})
    assert response.status_code == 502
    assert response.json()["detail"] == "Weather lookup failed"


def test_health(monkeypatch):
    client = TestClient(app)

    async def fake_is_weather_api_available():
        return True

    def fake_is_redis_available():
        return RedisStatus.connected

    monkeypatch.setattr(
        "app.main.is_weather_api_available", fake_is_weather_api_available
    )
    monkeypatch.setattr("app.main.is_redis_available", fake_is_redis_available)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dependencies": {"weather_api": "available", "redis": "connected"},
    }
