#include "config.h"

// WiFi
// ATENÇÃO: ajuste para sua rede
const char* ssid = "Redmi Note 9S";           // Nome da sua rede WiFi
const char* password = "show1234";            // Senha da sua rede WiFi

// MQTT
const char* mqtt_server = "broker.hivemq.com";  // Broker MQTT público
const int mqtt_port = 1883;                     // Porta padrão MQTT
const char* mqtt_user = "";                     // Usuário MQTT (vazio para broker público)
const char* mqtt_pass = "";                     // Senha MQTT (vazio para broker público)

// Tópicos
const char* mqtt_topic_state = "sensores/barreira/estado";     // Tópico para estados do sensor
const char* mqtt_topic_heartbeat = "sensores/barreira/heartbeat"; // Tópico para heartbeat

// Client ID
const char* mqtt_client_id = "ESP32_Barreira_001";

// Hardware
const int SENSOR_PIN = 15;  // Pino GPIO conectado ao sensor de barreira óptica

// Timing
// Intervalo de heartbeat (ms)
const unsigned long HEARTBEAT_INTERVAL = 60000;

// Debounce do sensor (ms)
const unsigned long SENSOR_DEBOUNCE_DELAY = 50;