"""City model for geocoding results."""

from pydantic import BaseModel


class City(BaseModel):
    """City information returned by the geocoding API."""

    name: str
    country_code: str
    latitude: float
    longitude: float
