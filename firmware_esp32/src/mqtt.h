#ifndef MQTT_H
#define MQTT_H

#include <PubSubClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>

// Instância global do cliente MQTT (declarada em mqtt.cpp)
extern PubSubClient client;

// ===== Setup / ciclo =====
void mqtt_init();                 // NOVO: setServer, buffer, keepalive, etc.
void reconnect_mqtt();
void mqtt_loop();

// ===== Publicações =====
void publish_sensor_state(bool is_free);
void publish_device_info();

// ===== Status / debug =====
bool is_mqtt_connected();
void print_mqtt_stats();

#endif