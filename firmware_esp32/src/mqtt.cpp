/**
 * @file mqtt.cpp
 * @brief Handles all MQTT communication for the Terelina project.
 * 
 * Manages connection, reconnection with Last Will and Testament (LWT),
 * and publishing of sensor data and device status.
 */

#include "mqtt.h"
#include "config.h"
#include <Arduino.h>
#include <WiFiClient.h>

// =====================================================================
// Global and Static Variables
// =====================================================================
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

static unsigned long lastMqttReconnectAttempt = 0;
static const unsigned long RECONNECT_INTERVAL_MS = 5000; // Attempt to reconnect every 5 seconds

// =====================================================================
// Core MQTT Functions (Initialization and Loop)
// =====================================================================

void setupMqtt() {
  mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
  mqttClient.setBufferSize(256); // A buffer of 256 bytes is sufficient for our JSON payload
  mqttClient.setKeepAlive(30);   // More resilient to network fluctuations
  mqttClient.setSocketTimeout(5); // Prevent long blocking calls
}

void handleMqttConnection() {
  if (mqttClient.connected()) {
    return;
  }

  unsigned long now = millis();
  if (now - lastMqttReconnectAttempt < RECONNECT_INTERVAL_MS) {
    return;
  }
  lastMqttReconnectAttempt = now;

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[MQTT] WiFi not connected. Cannot attempt MQTT connection."));
    return;
  }

  Serial.print(F("[MQTT] Attempting connection... "));

  // --- LWT Configuration ---
  // If the device disconnects unexpectedly, the broker will publish "offline"
  // to the heartbeat topic. This is the correct topic for status updates.
  const char* lwtTopic = MQTT_TOPIC_HEARTBEAT;
  const char* lwtMessage = "offline";
  const bool lwtRetain = true;
  const int lwtQos = 1;

  bool connected = false;
  if (strlen(MQTT_USER) > 0) {
    Serial.print(F("with authentication... "));
    connected = mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD, lwtTopic, lwtQos, lwtRetain, lwtMessage);
  } else {
    Serial.print(F("without authentication... "));
    connected = mqttClient.connect(MQTT_CLIENT_ID, lwtTopic, lwtQos, lwtRetain, lwtMessage);
  }

  if (connected) {
    Serial.println(F("OK!"));
    // Once connected, publish the "online" status to the same heartbeat topic
    publishHeartbeat();
  } else {
    Serial.print(F("FAILED, rc="));
    Serial.print(mqttClient.state());
    Serial.println(F(". Retrying in 5 seconds."));
  }
}

void loopMqtt() {
  mqttClient.loop();
}

// =====================================================================
// Data Publishing Functions
// =====================================================================

void publishSensorState(bool isInterrupted) {
  if (!isMqttConnected()) {
    Serial.println(F("[MQTT] Not connected. Cannot publish sensor state."));
    return;
  }

  StaticJsonDocument<128> doc;
  doc["id"] = MQTT_CLIENT_ID;
  
  // --- PAYLOAD ALIGNMENT ---
  // The backend expects "interrupted" or "clear".
  doc["state"] = isInterrupted ? "interrupted" : "clear";
  
  // Optional diagnostic data
  doc["rssi"] = WiFi.RSSI();
  doc["uptime_s"] = millis() / 1000;

  char jsonBuffer[128];
  serializeJson(doc, jsonBuffer);

  if (mqttClient.publish(MQTT_TOPIC_STATE, jsonBuffer)) {
    Serial.print(F("[MQTT] State published: "));
    Serial.println(jsonBuffer);
  } else {
    Serial.println(F("[MQTT] Failed to publish state."));
  }
}

void publishHeartbeat() {
  if (!isMqttConnected()) {
    return;
  }
  // The heartbeat is a simple "online" message, retained by the broker.
  if (mqttClient.publish(MQTT_TOPIC_HEARTBEAT, "online", true)) {
    Serial.println(F("[MQTT] Heartbeat 'online' published."));
  } else {
    Serial.println(F("[MQTT] Failed to publish heartbeat."));
  }
}

// =====================================================================
// Status and Utility Functions
// =====================================================================

bool isMqttConnected() {
  return mqttClient.connected();
}