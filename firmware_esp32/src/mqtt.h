#ifndef MQTT_H
#define MQTT_H

#include <PubSubClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>

// Global instance of the MQTT client, defined in mqtt.cpp
extern PubSubClient mqttClient;

// =====================================================================
// Core MQTT Functions (Initialization and Loop)
// =====================================================================

/**
 * @brief Initializes the MQTT client with broker details and sets up the callback.
 * Must be called once in the main setup() function.
 */
void setupMqtt();

/**
 * @brief Handles the MQTT connection and subscription logic.
 * Call this in the main loop() to maintain the connection.
 */
void handleMqttConnection();

/**
 * @brief Keeps the MQTT client running. Call this in every main loop() iteration.
 */
void loopMqtt();

// =====================================================================
// Data Publishing Functions
// =====================================================================

/**
 * @brief Publishes the current state of the barrier sensor.
 * @param isInterrupted True if the beam is broken, false otherwise.
 */
void publishSensorState(bool isInterrupted);

/**
 * @brief Publishes a heartbeat message to indicate the device is online.
 */
void publishHeartbeat();

// =====================================================================
// Status and Utility Functions
// =====================================================================

/**
 * @brief Checks if the MQTT client is currently connected to the broker.
 * @return True if connected, false otherwise.
 */
bool isMqttConnected();

#endif // MQTT_H