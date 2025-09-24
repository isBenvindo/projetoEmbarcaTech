#ifndef CONFIG_H
#define CONFIG_H

// ===== WiFi =====
extern const char* ssid;
extern const char* password;

// ===== MQTT =====
extern const char* mqtt_server;
extern const int   mqtt_port;
extern const char* mqtt_user;
extern const char* mqtt_pass;
extern const char* mqtt_topic_state;      // ex.: "sensores/barreira/estado"
extern const char* mqtt_topic_heartbeat;  // ex.: "sensores/barreira/heartbeat"
extern const char* mqtt_client_id;        // usado como device_id no payload

// ===== Hardware =====
extern const int  SENSOR_PIN;          // pino do sensor (INPUT_PULLUP por padrão)
extern const bool SENSOR_USE_PULLUP;   // NOVO: true => usa INPUT_PULLUP no setup
extern const bool SENSOR_ACTIVE_LOW;   // NOVO: true => LOW = interrompido, HIGH = livre

// ===== Timing =====
extern const unsigned long HEARTBEAT_INTERVAL;     // ms
extern const unsigned long SENSOR_DEBOUNCE_DELAY;  // ms (usamos em µs no código: *1000UL)

#endif
