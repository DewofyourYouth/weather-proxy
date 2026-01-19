"""Health check response models."""

from enum import Enum

from pydantic import BaseModel


class ServiceStatus(str, Enum):
    """Availability status for dependencies."""

    available = "available"
    not_available = "not_available"


class Dependencies(BaseModel):
    """Dependency status values for health checks."""

    weather_api: ServiceStatus
    redis: ServiceStatus


class HealthResponse(BaseModel):
    """API health response payload."""

    status: str
    dependencies: Dependencies
