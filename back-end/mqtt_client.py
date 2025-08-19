import paho.mqtt.client as mqtt
import json
from psycopg2 import Error


MQTT_BROKER_HOST = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_STATE = "sensores/barreira/estado"


_db_connection_func = None

_last_state = "unknown" 


def on_connect(client, userdata, flags, rc):
    print(f"MQTT Client Connected with result code {rc}")
    if rc == 0:
        client.subscribe(MQTT_TOPIC_STATE)
        print(f"Subscribed to topic: {MQTT_TOPIC_STATE}")
    else:
        print(f"Failed to connect, return code {rc}\n")


def on_message(client, userdata, msg):
    global _last_state
    print(f"Message received on topic {msg.topic}: {msg.payload.decode()}")
    

    if msg.topic == MQTT_TOPIC_STATE:
        try:
            json_payload = json.loads(msg.payload.decode())
            current_state = json_payload.get("state")
            timestamp_from_esp = json_payload.get("timestamp")

            if current_state:
                if _last_state == "interrompida" and current_state == "livre":
                    handle_pizza_pass(timestamp_from_esp)

                _last_state = current_state
            else:
                print("Erro: 'state' não encontrado no JSON da mensagem.")

        except json.JSONDecodeError:
            print(f"Erro: Payload MQTT não é um JSON válido: {msg.payload.decode()}")
        except Exception as e:
            print(f"Erro inesperado no on_message: {e}")


def handle_pizza_pass(timestamp_from_esp):
    try:
        if _db_connection_func:
            conn = _db_connection_func()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO contagens_pizzas (quantidade_pizzas) VALUES (%s)",
                (1,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Uma pizza salva no DB.")
        else:
            print("Erro: Função de conexão com o DB não configurada para o cliente MQTT.")
    except Error as e:
        print(f"Erro ao salvar no PostgreSQL (MQTT callback): {e}")
    except Exception as e:
        print(f"Erro inesperado ao salvar pizza: {e}")


def start_mqtt_client(db_connection_func):
    global _db_connection_func
    _db_connection_func = db_connection_func

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_start() 
        print(f"MQTT client attempting to connect to {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")

    return client