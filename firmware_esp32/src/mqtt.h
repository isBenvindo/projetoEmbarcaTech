#ifndef MQTT_H
#define MQTT_H

#include <PubSubClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>

extern PubSubClient client;

void reconnect_mqtt();
void publish_sensor_state(bool is_free);
void mqtt_loop();

#endif