#ifndef CONFIG_H
#define CONFIG_H

// =====================================================================
// WiFi Settings
// =====================================================================
// Note: These are fallback credentials if WiFi Manager fails or is not used.
extern const char* WIFI_SSID;
extern const char* WIFI_PASSWORD;

// =====================================================================
// MQTT Broker Settings
// =====================================================================
extern const char* MQTT_BROKER_HOST;
extern const int   MQTT_BROKER_PORT;
extern const char* MQTT_USER;
extern const char* MQTT_PASSWORD;
extern const char* MQTT_TOPIC_STATE;     // Topic to publish sensor state, e.g., "sensors/barrier/state"
extern const char* MQTT_TOPIC_HEARTBEAT; // Topic for device status heartbeat, e.g., "sensors/barrier/heartbeat"
extern const char* MQTT_CLIENT_ID;       // Unique client ID, also used as device_id in the payload

// =====================================================================
// Hardware Pinout & Behavior
// =====================================================================
extern const int  SENSOR_PIN;        // GPIO pin connected to the barrier sensor
extern const bool SENSOR_USE_PULLUP; // If true, enables the internal pull-up resistor (INPUT_PULLUP)
extern const bool SENSOR_ACTIVE_LOW; // If true, a LOW signal means the beam is interrupted (active state)

// =====================================================================
// Timing Configuration
// =====================================================================
extern const unsigned long HEARTBEAT_INTERVAL_MS;   // Interval for sending MQTT heartbeat messages (in milliseconds)
extern const unsigned long SENSOR_DEBOUNCE_DELAY_MS; // Debounce delay to prevent false readings (in milliseconds)

#endif // CONFIG_H