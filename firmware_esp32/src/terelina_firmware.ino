#include <Arduino.h>
#include "config.h"
#include "wifi_manager.h"
#include "mqtt.h"

unsigned long lastMsg = 0;
bool lastSensorState = false;

void setup() {
    Serial.begin(115200);
    pinMode(SENSOR_PIN, INPUT);

    setup_wifi();

    client.setServer(mqtt_server, mqtt_port);
}

void loop() {
    if (!client.connected()) {
        reconnect_mqtt();
    }
    mqtt_loop();

    unsigned long now = millis();
    bool currentSensorState = (digitalRead(SENSOR_PIN) == HIGH);

    if (currentSensorState != lastSensorState) {
        publish_sensor_state(currentSensorState);
        lastSensorState = currentSensorState;
        delay(50);
    }

    if (now - lastMsg > 60000) {
        lastMsg = now;
        client.publish(mqtt_topic_heartbeat, "ativo");
        Serial.println("Heartbeat enviado.");
    }
}