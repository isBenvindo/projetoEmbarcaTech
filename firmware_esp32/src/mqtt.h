#ifndef MQTT_H
#define MQTT_H

#include <PubSubClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>

// Variáveis externas
extern PubSubClient client;

// Funções principais
void reconnect_mqtt();
void publish_sensor_state(bool is_free);
void mqtt_loop();

// Funções auxiliares
void publish_device_info();
bool is_mqtt_connected();
void print_mqtt_stats();

#endif