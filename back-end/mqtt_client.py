import paho.mqtt.client as mqtt
import json
import logging
import os
from datetime import datetime
from psycopg2 import Error
from dotenv import load_dotenv

# .env
load_dotenv()

# Logger
logger = logging.getLogger(__name__)

# MQTT
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "broker.hivemq.com")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC_STATE = os.getenv("MQTT_TOPIC_STATE", "sensores/barreira/estado")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "terelina_backend")

# Estado global
_db_connection_func = None
_last_state = "unknown"
_client = None
_reconnect_attempts = 0
_max_reconnect_attempts = 5

def on_connect(client, userdata, flags, rc):
    """Callback executado quando conecta ao broker MQTT"""
    global _reconnect_attempts
    
    if rc == 0:
        logger.info(f"MQTT Client conectado com sucesso ao broker {MQTT_BROKER_HOST}")
        _reconnect_attempts = 0  # Zera tentativas
        
        # Inscreve no tópico
        result = client.subscribe(MQTT_TOPIC_STATE, qos=1)
        if result[0] == 0:
            logger.info(f"Inscrito no tópico: {MQTT_TOPIC_STATE}")
        else:
            logger.error(f"Falha ao se inscrever no tópico {MQTT_TOPIC_STATE}")
    else:
        error_messages = {
            1: "Código de retorno incorreto do protocolo",
            2: "Identificador de cliente inválido",
            3: "Servidor não disponível",
            4: "Nome de usuário ou senha incorretos",
            5: "Não autorizado"
        }
        error_msg = error_messages.get(rc, f"Código de erro desconhecido: {rc}")
        logger.error(f"Falha na conexão MQTT: {error_msg}")

def on_disconnect(client, userdata, rc):
    """Callback executado quando desconecta do broker MQTT"""
    if rc != 0:
        logger.warning(f"Desconexão inesperada do MQTT broker. Código: {rc}")
    else:
        logger.info("Desconexão MQTT realizada com sucesso")

def on_message(client, userdata, msg):
    """Callback executado quando recebe mensagem MQTT"""
    global _last_state
    
    try:
        logger.debug(f"Mensagem recebida no tópico {msg.topic}: {msg.payload.decode()}")
        
        if msg.topic == MQTT_TOPIC_STATE:
            process_sensor_message(msg.payload.decode())
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem MQTT: {e}")

def process_sensor_message(payload):
    """Processa mensagem do sensor de barreira"""
    global _last_state
    
    try:
        json_payload = json.loads(payload)
        current_state = json_payload.get("state")
        timestamp_from_esp = json_payload.get("timestamp")
        sensor_id = json_payload.get("id", "ESP32_Barreira_001")

        if not current_state:
            logger.warning("Campo 'state' não encontrado no JSON da mensagem")
            return

        logger.info(f"Estado do sensor {sensor_id}: {current_state} (anterior: {_last_state})")

        # Detecta passagem (interrompida -> livre)
        if _last_state == "interrompida" and current_state == "livre":
            logger.info(f"Pizza detectada! Salvando no banco de dados...")
            handle_pizza_pass(timestamp_from_esp, sensor_id)

        _last_state = current_state

    except json.JSONDecodeError as e:
        logger.error(f"Payload MQTT não é um JSON válido: {payload}. Erro: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao processar mensagem do sensor: {e}")

def handle_pizza_pass(timestamp_from_esp, sensor_id):
    """Salva contagem de pizza no banco de dados"""
    try:
        if not _db_connection_func:
            logger.error("Função de conexão com o DB não configurada")
            return

        conn = _db_connection_func()
        cursor = conn.cursor()
        
        # Insere contagem
        if timestamp_from_esp:
            # Converte timestamp ESP32
            try:
                esp_timestamp = datetime.fromtimestamp(int(timestamp_from_esp)/1000)
                cursor.execute(
                    "INSERT INTO contagens_pizzas (timestamp) VALUES (%s)",
                    (esp_timestamp,)
                )
            except (ValueError, TypeError):
                # Fallback: timestamp atual
                cursor.execute("INSERT INTO contagens_pizzas DEFAULT VALUES")
        else:
            cursor.execute("INSERT INTO contagens_pizzas DEFAULT VALUES")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Pizza contabilizada com sucesso! Sensor: {sensor_id}")
        
    except Error as e:
        logger.error(f"Erro ao salvar no PostgreSQL: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao salvar contagem de pizza: {e}")

def on_publish(client, userdata, mid):
    """Callback executado quando mensagem é publicada"""
    logger.debug(f"Mensagem publicada com ID: {mid}")

def on_subscribe(client, userdata, mid, granted_qos):
    """Callback executado quando inscrição é confirmada"""
    logger.debug(f"Inscrição confirmada com ID: {mid}, QoS: {granted_qos}")

def on_log(client, userdata, level, buf):
    """Callback para logs do cliente MQTT"""
    if level == mqtt.MQTT_LOG_ERR:
        logger.error(f"MQTT Log: {buf}")
    elif level == mqtt.MQTT_LOG_WARNING:
        logger.warning(f"MQTT Log: {buf}")
    else:
        logger.debug(f"MQTT Log: {buf}")

def start_mqtt_client(db_connection_func):
    """Inicia o cliente MQTT"""
    global _db_connection_func, _client
    
    _db_connection_func = db_connection_func
    
    try:
        # Cria cliente
        _client = mqtt.Client(
            client_id=MQTT_CLIENT_ID,
            clean_session=True,
            protocol=mqtt.MQTTv311
        )
        
        # Callbacks
        _client.on_connect = on_connect
        _client.on_disconnect = on_disconnect
        _client.on_message = on_message
        _client.on_publish = on_publish
        _client.on_subscribe = on_subscribe
        _client.on_log = on_log
        
        # Autenticação (se houver)
        if MQTT_USERNAME and MQTT_PASSWORD:
            _client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            logger.info("Autenticação MQTT configurada")
        
        # TLS (produção)
        # _client.tls_set()
        
        # Conecta ao broker
        logger.info(f"Tentando conectar ao broker MQTT: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        _client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        
        # Loop em thread separada
        _client.loop_start()
        
        logger.info("Cliente MQTT iniciado com sucesso")
        return _client
        
    except Exception as e:
        logger.error(f"Erro ao iniciar cliente MQTT: {e}")
        raise

def stop_mqtt_client():
    """Para o cliente MQTT"""
    global _client
    
    if _client:
        try:
            _client.loop_stop()
            _client.disconnect()
            logger.info("Cliente MQTT parado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao parar cliente MQTT: {e}")

def get_mqtt_status():
    """Retorna status do cliente MQTT"""
    global _client
    
    if not _client:
        return {"status": "not_initialized", "connected": False}
    
    return {
        "status": "initialized",
        "connected": _client.is_connected(),
        "broker": f"{MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}",
        "topic": MQTT_TOPIC_STATE,
        "last_state": _last_state
    }