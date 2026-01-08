from pydantic import BaseModel


class City(BaseModel):
    name: str
    country_code: str
    latitude: float
    longitude: float
