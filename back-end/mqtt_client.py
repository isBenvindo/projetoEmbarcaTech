import paho.mqtt.client as mqtt
import json
import logging
import os
import time
from datetime import datetime
from psycopg2 import Error
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# MQTT env
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "broker.hivemq.com")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC_STATE = os.getenv("MQTT_TOPIC_STATE", "sensores/barreira/estado")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
# dê um ID único! (ex.: sufixo com pid)
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", f"terelina_backend_{os.getpid()}")

# estado global
_db_connection_func = None
_client = None
_last_state = "unknown"
_last_transition_ms = 0
_initialized = False   # já recebemos a primeira msg (baseline)?
_DEBOUNCE_MS = 100     # ignora transições mais rápidas que isso

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"MQTT conectado ao broker {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        client.subscribe(MQTT_TOPIC_STATE, qos=1)
        logger.info(f"Inscrito no tópico: {MQTT_TOPIC_STATE}")
        # publica heartbeat online
        try:
            client.publish("sensores/barreira/heartbeat", "online", qos=1, retain=True)
        except Exception:
            pass
    else:
        logger.error(f"Falha na conexão MQTT: rc={rc}")

def on_disconnect(client, userdata, rc, properties=None):
    if rc != 0:
        logger.warning(f"Desconexão inesperada do MQTT broker. Código: {rc}")  # rc=7 -> CONN_LOST
    # loop_start + reconnect_delay_set já cuidam da reconexão

def on_message(client, userdata, msg):
    global _last_state, _initialized, _last_transition_ms

    payload_raw = msg.payload.decode(errors="ignore")
    is_retained = getattr(msg, "retain", False)

    # evita spam de retained: usa a primeira retained como baseline e ignora as seguintes
    if is_retained and _initialized:
        logger.debug(f"Ignorando mensagem retained repetida em {msg.topic}")
        return

    try:
        logger.debug(f"Mensagem recebida no tópico {msg.topic}: {payload_raw} (retained={is_retained})")
        data = json.loads(payload_raw)
        current_state = data.get("state")
        sensor_id = data.get("id", "ESP32_Barreira_001")
        ts_ms = data.get("timestamp")  # opcional (epoch ms vindo do ESP)

        if not current_state:
            logger.warning("Campo 'state' ausente no JSON")
            return

        logger.info(f"Sensor {sensor_id}: {current_state} (anterior: {_last_state})")

        now_ms = int(time.time() * 1000)
        # debounce de transições muito rápidas
        if _last_transition_ms and (now_ms - _last_transition_ms) < _DEBOUNCE_MS:
            logger.debug("Transição ignorada por debounce")
            _last_state = current_state
            return

        # detecção de pizza: interrompida -> livre
        if _last_state == "interrompida" and current_state == "livre":
            handle_pizza_pass(ts_ms, sensor_id)

        _last_state = current_state
        _last_transition_ms = now_ms
        _initialized = True

    except json.JSONDecodeError:
        logger.error(f"Payload não é JSON válido: {payload_raw}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

def handle_pizza_pass(timestamp_from_esp_ms, sensor_id):
    try:
        if not _db_connection_func:
            logger.error("Função de conexão com o DB não configurada")
            return
        conn = _db_connection_func()
        cur = conn.cursor()
        # grava com timestamp do servidor (UTC)
        cur.execute("INSERT INTO contagens_pizzas (timestamp) VALUES (NOW())")
        conn.commit()
        try:
            from main import log_system_event
            log_system_event("INFO", "Pizza contabilizada via MQTT", "mqtt")
        except Exception:
            pass
        cur.close()
        conn.close()
        logger.info(f"Pizza contabilizada! Sensor: {sensor_id}")
    except Error as e:
        logger.error(f"Erro ao salvar no PostgreSQL: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao salvar contagem: {e}")

def on_publish(client, userdata, mid):
    logger.debug(f"Mensagem publicada ID: {mid}")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    logger.debug(f"Inscrição confirmada ID: {mid}, QoS: {granted_qos}")

def start_mqtt_client(db_connection_func):
    global _db_connection_func, _client
    _db_connection_func = db_connection_func

    _client = mqtt.Client(
        client_id=MQTT_CLIENT_ID,
        clean_session=True,
        protocol=mqtt.MQTTv311
    )
    _client.enable_logger(logger)

    # LWT: se o backend cair, marca offline
    _client.will_set("sensores/barreira/heartbeat", "offline", qos=1, retain=True)

    if MQTT_USERNAME and MQTT_PASSWORD:
        _client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # reconexão com backoff (1..30s)
    _client.reconnect_delay_set(min_delay=1, max_delay=30)
    # limitar inflight / retry ajuda em broker público
    _client.max_inflight_messages_set(10)
    _client.message_retry_set(5)

    _client.on_connect = on_connect
    _client.on_disconnect = on_disconnect
    _client.on_message = on_message
    _client.on_publish = on_publish
    _client.on_subscribe = on_subscribe

    logger.info(f"Tentando conectar ao broker MQTT: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    _client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=20)
    _client.loop_start()
    logger.info("Cliente MQTT iniciado com sucesso")
    return _client

def stop_mqtt_client():
    global _client
    if _client:
        try:
            _client.loop_stop()
            _client.disconnect()
            logger.info("Cliente MQTT parado")
        except Exception as e:
            logger.error(f"Erro ao parar cliente MQTT: {e}")

def get_mqtt_status():
    global _client, _last_state
    if not _client:
        return {"status": "not_initialized", "connected": False}
    return {
        "status": "initialized",
        "connected": bool(_client.is_connected()),
        "broker": f"{MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}",
        "topic": MQTT_TOPIC_STATE,
        "last_state": _last_state
    }
