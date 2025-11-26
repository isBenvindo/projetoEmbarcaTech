/**
 * @file terelina_firmware.ino
 * @brief Main firmware for the Terelina Pizza Counter device.
 *
 * This firmware initializes the hardware, connects to WiFi via WiFiManager,
 * connects to MQTT, reads the barrier sensor with debounce, and publishes state changes.
 */

#include <Arduino.h>
#include "config.h"
#include "wifi_manager.h"
#include "mqtt.h"

// =====================================================================
// Global State
// =====================================================================

// 'true' means the sensor beam is currently interrupted.
bool isBeamInterrupted = false;

// Timer for the non-blocking heartbeat task.
unsigned long lastHeartbeatMillis = 0;


// =====================================================================
// SETUP - Runs once on boot.
// =====================================================================
void setup() {
    Serial.begin(115200);
    Serial.println();
    Serial.println(F("=========================================="));
    Serial.println(F("    Terelina Pizza Counter System"));
    Serial.println(F("=========================================="));
    Serial.println();

    // --- 1. Configure Hardware Sensor ---
    if (SENSOR_USE_PULLUP) {
        pinMode(SENSOR_PIN, INPUT_PULLUP);
        Serial.printf("[HW] Sensor pin %d configured with INPUT_PULLUP.\n", SENSOR_PIN);
    } else {
        pinMode(SENSOR_PIN, INPUT);
        Serial.printf("[HW] Sensor pin %d configured as standard INPUT.\n", SENSOR_PIN);
    }

    // Read the initial state to prevent a false trigger on boot.
    isBeamInterrupted = (digitalRead(SENSOR_PIN) == (SENSOR_ACTIVE_LOW ? LOW : HIGH));
    Serial.printf("[HW] Initial sensor state: %s\n", isBeamInterrupted ? "INTERRUPTED" : "CLEAR");

    // --- 2. Connect to WiFi ---
    // This function is blocking. It will handle the connection, AP portal,
    // and fallback logic automatically.
    setupWifi();

    // --- 3. Initialize MQTT Client ---
    Serial.println(F("[MQTT] Initializing MQTT client..."));
    setupMqtt(); // Sets the broker server, port, buffer, etc.

    Serial.println(F("=========================================="));
    Serial.println(F("System initialized. Starting main loop..."));
    Serial.println();
}


// =====================================================================
// LOOP - Runs repeatedly.
// =====================================================================
void loop() {
    // This is the core of the firmware. Each function is non-blocking.

    // 1. Maintain MQTT connection and process messages.
    handleMqttConnection();
    loopMqtt();

    // 2. Read the sensor and publish any state changes.
    handleSensor();

    // 3. Perform periodic tasks, like sending the heartbeat.
    handleTimedTasks();

    // Small delay to allow the ESP32's background tasks to run.
    delay(1);
}


// =====================================================================
// Helper Functions for the Main Loop
// =====================================================================

/**
 * @brief Reads the sensor, applies debounce logic, and publishes if the state changes.
 */
void handleSensor() {
    // 'static' variables retain their value between calls to loop().
    static bool lastPublishedState = isBeamInterrupted;
    static unsigned long lastFlickerTime = 0;

    bool currentState = (digitalRead(SENSOR_PIN) == (SENSOR_ACTIVE_LOW ? LOW : HIGH));

    if (currentState != lastPublishedState) {
        // If the state has changed, wait for the debounce delay to ensure it's a stable change.
        if (millis() - lastFlickerTime > SENSOR_DEBOUNCE_DELAY_MS) {
            
            Serial.printf("[Sensor] State change confirmed: %s -> %s\n",
                          lastPublishedState ? "INTERRUPTED" : "CLEAR",
                          currentState ? "INTERRUPTED" : "CLEAR");

            // Update the global state and publish it.
            isBeamInterrupted = currentState;
            lastPublishedState = currentState;
            publishSensorState(isBeamInterrupted);
        }
    } else {
        // If the state has not changed, reset the flicker timer.
        // This means the signal is stable.
        lastFlickerTime = millis();
    }
}

/**
 * @brief Handles periodic tasks that are not checked in every loop cycle.
 */
void handleTimedTasks() {
    unsigned long now = millis();

    // --- MQTT Heartbeat Task ---
    if (now - lastHeartbeatMillis > HEARTBEAT_INTERVAL_MS) {
        lastHeartbeatMillis = now;
        
        // This function already checks for MQTT connection before publishing.
        publishHeartbeat();
        
        // Also print a general status update for debugging.
        printSystemStatus();
    }
}

/**
 * @brief Prints a summary of the system's current status to the Serial Monitor.
 */
void printSystemStatus() {
    Serial.println(F("\n--- System Status ---"));
    Serial.printf("WiFi: %s\n", isWifiConnected() ? "Connected" : "Disconnected");
    Serial.printf("MQTT: %s\n", isMqttConnected() ? "Connected" : "Disconnected");
    Serial.printf("Sensor: %s\n", isBeamInterrupted ? "INTERRUPTED" : "CLEAR");
    Serial.printf("Free Heap: %u bytes\n", ESP.getFreeHeap());
    Serial.printf("Uptime: %lu s\n", millis() / 1000);
    Serial.println(F("---------------------\n"));
}