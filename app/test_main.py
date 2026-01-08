from fastapi.testclient import TestClient

from app.main import app
from app.models.health import ServiceStatus
from app.models.weather import Weather
from app.weather_service.weather import CityNotFoundError, ExternalAPIError


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        return None


class FakeCityCache:
    def get_city(self, city_name: str):
        return None

    def save_city(self, city_name: str, city):
        return None


class FakeWeatherCache:
    def get_weather(self, city_name: str):
        return None

    def save_weather(self, city_name: str, weather_data):
        return None


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
        return ServiceStatus.available

    monkeypatch.setattr(
        "app.main.is_weather_api_available", fake_is_weather_api_available
    )
    monkeypatch.setattr("app.main.is_redis_available", fake_is_redis_available)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dependencies": {"weather_api": "available", "redis": "available"},
    }


def test_get_weather_integration_with_mocked_upstream(monkeypatch):
    client = TestClient(app)

    def fake_httpx_get(url, params=None, timeout=None):
        if "geocoding-api.open-meteo.com" in url:
            return FakeResponse(
                {
                    "results": [
                        {
                            "name": "London",
                            "country_code": "GB",
                            "latitude": 51.50853,
                            "longitude": -0.12574,
                        }
                    ]
                }
            )
        if "api.open-meteo.com" in url:
            return FakeResponse(
                {
                    "current_weather": {
                        "time": "2024-01-01T00:00",
                        "temperature": 10.5,
                        "windspeed": 5.0,
                        "winddirection": 180,
                        "is_day": 1,
                        "weathercode": 1,
                    }
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("app.weather_service.weather.httpx.get", fake_httpx_get)
    monkeypatch.setattr("app.weather_service.weather.city_cache", lambda: FakeCityCache())
    monkeypatch.setattr(
        "app.weather_service.weather.weather_cache", lambda: FakeWeatherCache()
    )

    response = client.get("/weather", params={"city_name": "London"})
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "London"
    assert data["temperature_c"] == 10.5
