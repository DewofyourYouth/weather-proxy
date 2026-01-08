import pytest

from app.weather_service.weather import get_city_data, get_weather_data_from_api, City


def test_get_city_data():
    london_data = get_city_data("London")
    tel_aviv_data = get_city_data("Tel Aviv")
    assert london_data == City(
        **{
            "name": "London",
            "country_code": "GB",
            "latitude": 51.50853,
            "longitude": -0.12574,
        }
    )
    assert tel_aviv_data == City(
        **{
            "name": "Tel Aviv",
            "country_code": "IL",
            "latitude": 32.08088,
            "longitude": 34.78057,
        }
    )


def test_get_invalid_city_data():
    with pytest.raises(KeyError):
        get_city_data("Loooonnddonnn")


def test_get_weather_data():
    london_data = get_city_data("London")
    weather_data = get_weather_data_from_api(london_data)
    assert "current_weather_units" in weather_data
