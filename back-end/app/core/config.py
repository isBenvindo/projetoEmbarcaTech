# back-end/app/core/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Database
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # MQTT
    MQTT_BROKER_HOST: str
    MQTT_BROKER_PORT: int
    MQTT_TOPIC_STATE: str
    MQTT_USERNAME: str | None = None
    MQTT_PASSWORD: str | None = None
    MQTT_CLIENT_ID: str

    # Application
    LOG_LEVEL: str = "INFO"

    class Config:
        # This tells Pydantic to read variables from a .env file
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Use lru_cache to create a singleton-like settings object
# This ensures the .env file is read only once
@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Instantiate it once to be easily imported elsewhere
settings = get_settings()