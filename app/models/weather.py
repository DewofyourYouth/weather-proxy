"""Weather model and code mapping helpers."""

from datetime import datetime

from pydantic import BaseModel

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm (no hail)",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class Weather(BaseModel):
    """Weather payload exposed by the API."""

    city: str  # You’ll likely be injecting this from your own lookup
    time: datetime
    temperature_c: float
    windspeed_kmh: float
    winddirection_deg: int
    is_day: bool
    weather_code: int
    weather_description: str

    @classmethod
    def from_api_response(cls, city: str, api_data: dict) -> "Weather":
        """Create a Weather model from the external API payload.

        Args:
            city: City name string.
            api_data: API payload containing current weather data.

        Returns:
            A populated Weather model.
        """
        current = api_data["current_weather"]
        code = current["weathercode"]
        return cls(
            city=city,
            time=datetime.fromisoformat(current["time"]),
            temperature_c=current["temperature"],
            windspeed_kmh=current["windspeed"],
            winddirection_deg=current["winddirection"],
            is_day=bool(current["is_day"]),
            weather_code=code,
            weather_description=WEATHER_CODE_MAP.get(code, "Unknown"),
        )
