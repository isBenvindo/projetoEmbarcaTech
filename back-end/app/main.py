# back-end/app/main.py

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import system, counts
from app.services.mqtt_client import start_mqtt_client, stop_mqtt_client

# --- Logging Configuration ---
# Configure logging at the application's entry point
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('terelina_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Terelina Pizza Counter API",
    description="API for automatic pizza counting, optimized for Grafana.",
    version="2.0.0" # Bumping version for the refactored app
)

# --- Middleware ---
# Configure CORS to allow requests from any origin (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# Include the modularized routers with prefixes for versioning and organization
app.include_router(system.router, tags=["System & Health"])
app.include_router(counts.router, prefix="/v1", tags=["Counts & Statistics"])

# --- Startup and Shutdown Events ---
@app.on_event("startup")
async def startup_event():
    """Starts the MQTT client when the application starts."""
    logger.info("FastAPI application starting up...")
    try:
        start_mqtt_client()
        logger.info("MQTT client started successfully.")
    except Exception as e:
        logger.error(f"Failed to start MQTT client on startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stops the MQTT client when the application shuts down."""
    logger.info("FastAPI application shutting down...")
    stop_mqtt_client()