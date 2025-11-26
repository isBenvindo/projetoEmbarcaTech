# back-end/app/services/mqtt_client.py

import paho.mqtt.client as mqtt
import json
import logging
import time
import os
from psycopg2 import Error

from app.core.config import settings
from app.db.session import get_db_connection

logger = logging.getLogger(__name__)

# Module-level state for the MQTT client
_client = None
_last_state = "unknown"
_last_transition_ms = 0
_initialized = False
_DEBOUNCE_MS = 100  # Ignore state transitions faster than this (in ms)

# =====================================================================
# Database Interaction
# =====================================================================

def _log_system_event(level: str, message: str, source: str = "mqtt"):
    """Logs an event into the system_logs table."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO system_logs (level, message, source) VALUES (%s, %s, %s)",
                    (level.upper(), message, source)
                )
                conn.commit()
    except Exception as e:
        logger.error(f"Failed to log system event to DB: {e}")

def _handle_pizza_count(sensor_id: str):
    """Inserts a new pizza count record into the database."""
    try:
        # get_db_connection() uses the connection pool
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # The timestamp is handled by the database's NOW() function
                cur.execute("INSERT INTO pizza_counts (timestamp) VALUES (NOW())")
                conn.commit()
        
        logger.info(f"Pizza count saved! Sensor ID: {sensor_id}")
        _log_system_event("INFO", f"Pizza counted from sensor: {sensor_id}")
        
    except Error as e:
        logger.error(f"PostgreSQL error while saving count: {e}")
        _log_system_event("ERROR", f"PostgreSQL error on save: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while saving count: {e}")
        _log_system_event("ERROR", f"Unexpected error on save: {e}")

# =====================================================================
# MQTT Callbacks
# =====================================================================

def _on_connect(client, userdata, flags, rc, properties=None):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        logger.info(f"Successfully connected to MQTT broker at {settings.MQTT_BROKER_HOST}")
        _log_system_event("INFO", "MQTT client connected")
        client.subscribe(settings.MQTT_TOPIC_STATE, qos=1)
    else:
        logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
        _log_system_event("ERROR", f"MQTT connection failed (code: {rc})")

def _on_disconnect(client, userdata, rc, properties=None):
    """Callback for when the client disconnects."""
    if rc != 0:
        logger.warning(f"Unexpected MQTT disconnection. Code: {rc}. Will attempt to reconnect.")
        _log_system_event("WARNING", f"Unexpected MQTT disconnection (code: {rc})")

def _normalize_state(raw_state: str) -> str | None:
    """Normalizes the received state to 'interrupted' or 'clear'."""
    if raw_state is None:
        return None
    s = str(raw_state).strip().lower()
    if s.startswith("interrompid") or s.startswith("interrupted"):
        return "interrupted"
    if s == "livre" or s == "clear":
        return "clear"
    return None

def _on_message(client, userdata, msg):
    """Callback for when a message is received from the broker."""
    global _last_state, _initialized, _last_transition_ms

    try:
        payload_str = msg.payload.decode(errors="ignore")
        logger.debug(f"Message received on topic {msg.topic}: {payload_str}")

        if not payload_str:
            logger.debug("Empty payload received, ignoring.")
            return

        data = json.loads(payload_str)
        
        state = _normalize_state(data.get("state"))
        if not state:
            logger.warning(f"Message ignored: missing or invalid 'state' field in JSON: {data}")
            return

        sensor_id = data.get("id", "ESP32_Barrier_001")
        now_ms = int(time.time() * 1000)

        # Debounce to prevent false positives from sensor flickering
        if _last_transition_ms and (now_ms - _last_transition_ms) < _DEBOUNCE_MS:
            logger.debug(f"State transition ignored due to debounce. New state: {state}")
            _last_state = state # Update state anyway to prevent false triggers
            return

        # --- Core Logic: Detect product on state transition ---
        # A product is counted when the beam goes from 'interrupted' to 'clear'.
        if _last_state == "interrupted" and state == "clear":
            logger.info("Product detected (interrupted -> clear). Saving count.")
            _handle_pizza_count(sensor_id)

        _last_state = state
        _last_transition_ms = now_ms
        _initialized = True

    except json.JSONDecodeError:
        logger.warning(f"Could not decode JSON from payload: {payload_str!r}")
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

# =====================================================================
# Client Initialization
# =====================================================================

def start_mqtt_client():
    """Initializes and starts the MQTT client."""
    global _client
    if _client:
        logger.warning("MQTT client already started.")
        return _client

    try:
        client_id = settings.MQTT_CLIENT_ID or f"terelina_backend_{os.getpid()}"
        
        _client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            _client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        _client.on_connect = _on_connect
        _client.on_disconnect = _on_disconnect
        _client.on_message = _on_message

        logger.info(f"Connecting to MQTT broker: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
        _client.connect(
            settings.MQTT_BROKER_HOST,
            settings.MQTT_BROKER_PORT,
            keepalive=60
        )
        _client.loop_start() # Starts a background thread for the client
        logger.info("MQTT client started successfully.")
        return _client
    
    except Exception as e:
        logger.error(f"Failed to start MQTT client: {e}")
        _log_system_event("ERROR", f"Failed to start MQTT client: {e}")
        raise

def stop_mqtt_client():
    """Stops the MQTT client gracefully."""
    global _client
    if _client and _client.is_connected():
        logger.info("Stopping MQTT client...")
        _client.loop_stop()
        _client.disconnect()
        logger.info("MQTT client stopped.")

def get_mqtt_status():
    """Returns the current status of the MQTT client."""
    if not _client:
        return {"status": "not_initialized", "connected": False}
    
    return {
        "status": "running",
        "connected": _client.is_connected(),
        "broker": f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}",
        "subscribed_topic": settings.MQTT_TOPIC_STATE,
        "last_sensor_state": _last_state
    }