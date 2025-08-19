#include "mqtt.h"
#include "config.h"
#include <Arduino.h>
#include <WiFi.h> 
#include <WiFiClient.h>
#include <ArduinoJson.h> 

WiFiClient espClient;
PubSubClient client(espClient);

void reconnect_mqtt() {
    while (!client.connected()) {
        Serial.print("Tentando conexão MQTT...");
        if (client.connect(mqtt_client_id, mqtt_user, mqtt_pass)) {
            Serial.println("conectado!");
            client.publish(mqtt_topic_heartbeat, "online");
        } else {
            Serial.print("falhou, rc=");
            Serial.print(client.state());
            Serial.println(" tentando novamente em 5 segundos");
            delay(5000);
        }
    }
}

void publish_sensor_state(bool is_free) {
    StaticJsonDocument<200> doc;
    doc["id"] = mqtt_client_id;
    doc["timestamp"] = String(millis());
    doc["state"] = is_free ? "livre" : "interrompida";

    char json_buffer[200];
    serializeJson(doc, json_buffer);

    client.publish(mqtt_topic_state, json_buffer);
    Serial.print("Publicado: ");
    Serial.println(json_buffer);
}

void mqtt_loop() {
    client.loop();
}