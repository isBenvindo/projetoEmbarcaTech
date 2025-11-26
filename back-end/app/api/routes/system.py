# back-end/app/api/routes/system.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extensions import connection

from app.db.session import db_dependency
from app.schemas.system import (
    HealthResponse, MqttStatusResponse, SystemLogResponse, ApiInfoResponse
)
from app.services.mqtt_client import get_mqtt_status

# APIRouter allows us to declare routes in different files
router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=ApiInfoResponse)
async def read_root():
    """Provides basic information about the API."""
    return {
        "message": "Welcome to the Terelina Pizza Counter API!",
        "version": "2.0.0", # Refactored version
        "status": "online",
        "docs_url": "/docs"
    }

@router.get("/health", response_model=HealthResponse)
async def health_check(db: connection = Depends(db_dependency)):
    """Performs a health check on the API and its database connection."""
    db_connected = False
    message = "API is running."
    try:
        with db.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        db_connected = True
        message = "API and database connection are healthy."
        logger.debug("Health check successful.")
    except Exception as e:
        message = f"Database connection failed: {e}"
        logger.error(f"Health check failed: {e}")

    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        message=message,
        database_connected=db_connected
    )

@router.get("/mqtt-status", response_model=MqttStatusResponse)
async def mqtt_status():
    """Returns the current status of the MQTT client."""
    try:
        return get_mqtt_status()
    except Exception as e:
        logger.error(f"Error getting MQTT status: {e}")
        raise HTTPException(
            status_code=500, detail="Could not retrieve MQTT status"
        )

@router.get("/logs", response_model=list[SystemLogResponse])
async def get_system_logs(
    db: connection = Depends(db_dependency),
    limit: int = Query(100, le=500),
    level: str | None = Query(None, pattern="^(INFO|WARNING|ERROR)$")
):
    """Retrieves system logs from the database."""
    try:
        with db.cursor() as cur:
            sql_query = "SELECT level, message, source, timestamp FROM system_logs"
            params = []
            if level:
                sql_query += " WHERE level = %s"
                params.append(level.upper())
            
            sql_query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(sql_query, tuple(params))
            logs = cur.fetchall()

            return [
                SystemLogResponse(level=row[0], message=row[1], source=row[2], timestamp=row[3])
                for row in logs
            ]
    except Exception as e:
        logger.error(f"Error fetching system logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch logs.")