#include "config.h"

// ===== WiFi =====
const char* ssid     = "Redmi Note 9S";   // Nome da sua rede WiFi
const char* password = "show1234";        // Senha da sua rede WiFi

// ===== MQTT =====
const char* mqtt_server         = "broker.hivemq.com"; // Broker MQTT público (teste)
const int   mqtt_port           = 1883;                // Porta padrão MQTT
const char* mqtt_user           = "";                  // Usuário MQTT (em branco se público)
const char* mqtt_pass           = "";                  // Senha MQTT (em branco se público)
const char* mqtt_topic_state    = "sensores/barreira/estado";
const char* mqtt_topic_heartbeat= "sensores/barreira/heartbeat";
const char* mqtt_client_id      = "ESP32_Barreira_001"; // usado como device_id no payload

// ===== Hardware =====
const int  SENSOR_PIN        = 27;   // GPIO conectado ao sensor
const bool SENSOR_USE_PULLUP = true; // true => INPUT_PULLUP no setup
const bool SENSOR_ACTIVE_LOW = true; // true => LOW = interrompido, HIGH = livre

// ===== Timing =====
const unsigned long HEARTBEAT_INTERVAL    = 60000; // ms
const unsigned long SENSOR_DEBOUNCE_DELAY = 50;    // ms (usado em µs no loop)
