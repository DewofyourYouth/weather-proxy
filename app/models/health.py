from enum import Enum

from pydantic import BaseModel


class ServiceStatus(str, Enum):
    available = "available"
    not_available = "not_available"


class Dependencies(BaseModel):
    weather_api: ServiceStatus
    redis: ServiceStatus


class HealthResponse(BaseModel):
    status: str
    dependencies: Dependencies
