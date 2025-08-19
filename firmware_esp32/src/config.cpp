#include "config.h"

const char* ssid = "NOME_DA_SUA_REDE_WIFI";
const char* password = "SUA_SENHA_WIFI";

const char* mqtt_server = "IP_DO_SEU_BROKER_MQTT_OU_URL";
const int mqtt_port = 1883;
const char* mqtt_user = "SEU_USUARIO_MQTT";
const char* mqtt_pass = "SUA_SENHA_MQTT";
const char* mqtt_topic_state = "sensores/barreira/estado";
const char* mqtt_topic_heartbeat = "sensores/barreira/heartbeat";
const char* mqtt_client_id = "ESP32_Barreira_001";

const int SENSOR_PIN = 15;