# back-end/app/schemas/system.py

from pydantic import BaseModel, Field
from datetime import datetime

class HealthResponse(BaseModel):
    """Schema for the application health check."""
    status: str
    message: str
    database_connected: bool
    timestamp: datetime = Field(default_factory=datetime.now)

class MqttStatusResponse(BaseModel):
    """Schema for the MQTT client status."""
    status: str
    connected: bool
    broker: str
    subscribed_topic: str
    last_sensor_state: str

class SystemLogResponse(BaseModel):
    """Schema for a single system log entry."""
    level: str
    message: str
    source: str
    timestamp: datetime

class ApiInfoResponse(BaseModel):
    """Schema for the root endpoint response."""
    message: str
    version: str
    status: str
    docs_url: str