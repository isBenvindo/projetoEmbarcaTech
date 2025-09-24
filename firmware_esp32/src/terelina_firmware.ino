#include <Arduino.h>
#include "config.h"
#include "wifi_manager.h"
#include "mqtt.h"

// Estado global
unsigned long lastMsg = 0;
bool lastSensorState = false;   // HIGH = livre, LOW = interrompido (com INPUT_PULLUP)
bool wifiConnected = false;
bool mqttConnected = false;

unsigned long pizzaCount = 0;
unsigned long mqttReconnectAttempts = 0;
unsigned long lastWifiCheck = 0;
const unsigned long WIFI_CHECK_INTERVAL = 30000; // 30 s

void setup() {
    Serial.begin(115200);
    Serial.println();
    Serial.println("==========================================");
    Serial.println("    SISTEMA DE CONTAGEM TERELINA");
    Serial.println("==========================================");
    Serial.println();

    // Sensor (pull-up interno; HIGH=livre, LOW=interrompido)
    pinMode(SENSOR_PIN, INPUT_PULLUP);
    Serial.printf("Sensor configurado no GPIO %d (INPUT_PULLUP)\n", SENSOR_PIN);

    // Sincroniza estado inicial para evitar transição falsa no boot
    lastSensorState = (digitalRead(SENSOR_PIN) == HIGH);

    // WiFi
    Serial.println("Iniciando conexão WiFi...");
    setup_wifi();
    wifiConnected = true;
    Serial.printf("WiFi conectado! IP: %s\n", WiFi.localIP().toString().c_str());

    // MQTT
    Serial.println("Configurando cliente MQTT...");
    mqtt_init(); // define servidor, buffer, keepalive, etc.
    Serial.printf("MQTT configurado para: %s:%d\n", mqtt_server, mqtt_port);

    // Conexão inicial MQTT
    reconnect_mqtt();

    Serial.println("Sistema inicializado com sucesso!");
    Serial.println("==========================================");
    Serial.println();
}

void loop() {
    unsigned long now = millis();

    // Verifica WiFi periodicamente
    if (now - lastWifiCheck > WIFI_CHECK_INTERVAL) {
        check_wifi_connection();
        lastWifiCheck = now;
    }

    // Gerencia MQTT
    if (!client.connected()) {
        mqttConnected = false;
        reconnect_mqtt();
    } else {
        mqttConnected = true;
    }

    // Processa MQTT
    mqtt_loop();

    // Lê sensor (HIGH=livre, LOW=interrompido)
    int raw = digitalRead(SENSOR_PIN);
    bool currentSensorState = (raw == HIGH);

    // Debug do pino bruto (a cada ~500 ms)
    static unsigned long lastDbg = 0;
    if (now - lastDbg > 500) {
        lastDbg = now;
        Serial.printf("[DBG] raw=%d  interpretado=%s\n",
                      raw, currentSensorState ? "LIVRE" : "INTERROMPIDO");
    }

    // Detecta mudança com debounce em micros (não bloqueante)
    static unsigned long lastChangeUs = 0;
    if (currentSensorState != lastSensorState) {
        unsigned long nowUs = micros();
        if (nowUs - lastChangeUs >= (SENSOR_DEBOUNCE_DELAY * 1000UL)) {
            lastChangeUs = nowUs;

            Serial.printf("Mudança de estado do sensor: %s -> %s\n",
                          lastSensorState ? "LIVRE" : "INTERROMPIDO",
                          currentSensorState ? "LIVRE" : "INTERROMPIDO");

            if (mqttConnected) {
                publish_sensor_state(currentSensorState);

                // Conta pizza (transição interrompido -> livre)
                if (!lastSensorState && currentSensorState) {
                    pizzaCount++;
                    Serial.printf("PIZZA DETECTADA! Total: %lu\n", pizzaCount);
                }
            } else {
                Serial.println("MQTT desconectado - não foi possível publicar estado");
            }

            lastSensorState = currentSensorState;
        }
    }

    // Heartbeat
    if (now - lastMsg > HEARTBEAT_INTERVAL) {
        lastMsg = now;
        if (mqttConnected) {
            client.publish(mqtt_topic_heartbeat, "ativo");
            Serial.println("Heartbeat enviado");
        } else {
            Serial.println("Heartbeat não enviado - MQTT desconectado");
        }
    }

    // Evitar travas longas no loop
    delay(1);
}

// WiFi helpers
void check_wifi_connection() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Conexão WiFi perdida! Tentando reconectar...");
        wifiConnected = false;
        setup_wifi();
        wifiConnected = true;
        Serial.printf("WiFi reconectado! IP: %s\n", WiFi.localIP().toString().c_str());
    }
}

void print_system_status() {
    Serial.println("\n=== STATUS DO SISTEMA ===");
    Serial.printf("WiFi: %s\n", wifiConnected ? "Conectado" : "Desconectado");
    Serial.printf("MQTT: %s\n", mqttConnected ? "Conectado" : "Desconectado");
    Serial.printf("Sensor: %s\n", lastSensorState ? "LIVRE" : "INTERROMPIDO");
    Serial.printf("Pizzas contadas: %lu\n", pizzaCount);
    Serial.printf("Tentativas MQTT: %lu\n", mqttReconnectAttempts);
    Serial.printf("Uptime: %lu s\n", millis() / 1000);
    Serial.println("========================\n");
}
