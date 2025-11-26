#include "config.h"

// =====================================================================
// WiFi Settings
// =====================================================================
// Fallback credentials. In a real-world scenario, these might be left
// blank to force the use of a WiFi Manager portal.
const char* WIFI_SSID     = "";      // Your WiFi network name
const char* WIFI_PASSWORD = "";  // Your WiFi network password

// =====================================================================
// MQTT Broker Settings
// =====================================================================
const char* MQTT_BROKER_HOST   = "broker.hivemq.com"; // Public MQTT broker for testing
const int   MQTT_BROKER_PORT   = 1883;                // Default MQTT port
const char* MQTT_USER          = "";                  // MQTT username (leave blank if not required)
const char* MQTT_PASSWORD      = "";                  // MQTT password (leave blank if not required)

// --- TOPIC CONFIGURATION ---
// IMPORTANT: These topics MUST match what the backend is subscribed to.
const char* MQTT_TOPIC_STATE     = "sensors/barrier/state";
const char* MQTT_TOPIC_HEARTBEAT = "sensors/barrier/heartbeat";
const char* MQTT_CLIENT_ID       = "ESP32_Barrier_001"; // Unique device identifier

// =====================================================================
// Hardware Pinout & Behavior
// =====================================================================
const int  SENSOR_PIN        = 27;   // GPIO pin connected to the sensor's output
const bool SENSOR_USE_PULLUP = true; // Use true if the sensor is a simple switch/contact to GND
const bool SENSOR_ACTIVE_LOW = true; // Use true if the sensor outputs a LOW signal when the beam is broken

// =====================================================================
// Timing Configuration
// =====================================================================
const unsigned long HEARTBEAT_INTERVAL_MS    = 60000; // 60 seconds
const unsigned long SENSOR_DEBOUNCE_DELAY_MS = 50;    // 50 milliseconds