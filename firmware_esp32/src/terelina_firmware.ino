#include <Arduino.h>
#include "config.h"
#include "wifi_manager.h"
#include "mqtt.h"

// Variáveis globais
unsigned long lastMsg = 0;
bool lastSensorState = false;
bool wifiConnected = false;
bool mqttConnected = false;

// Contadores para monitoramento
unsigned long pizzaCount = 0;
unsigned long mqttReconnectAttempts = 0;
unsigned long lastWifiCheck = 0;
const unsigned long WIFI_CHECK_INTERVAL = 30000; // 30 segundos

// Setup
void setup() {
    // Serial
    Serial.begin(115200);
    Serial.println();
    Serial.println("==========================================");
    Serial.println("    SISTEMA DE CONTAGEM TERELINA");
    Serial.println("==========================================");
    Serial.println();
    
    // Sensor
    pinMode(SENSOR_PIN, INPUT);
    Serial.printf("Sensor configurado no pino GPIO %d\n", SENSOR_PIN);
    
    // WiFi
    Serial.println("Iniciando conexão WiFi...");
    setup_wifi();
    wifiConnected = true;
    Serial.printf("WiFi conectado! IP: %s\n", WiFi.localIP().toString().c_str());
    
    // MQTT
    Serial.println("Configurando cliente MQTT...");
    client.setServer(mqtt_server, mqtt_port);
    Serial.printf("MQTT configurado para: %s:%d\n", mqtt_server, mqtt_port);
    
    // Conexão inicial MQTT
    reconnect_mqtt();
    
    Serial.println("Sistema inicializado com sucesso!");
    Serial.println("==========================================");
    Serial.println();
}

// Loop principal
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
    
    // Lê sensor
    bool currentSensorState = (digitalRead(SENSOR_PIN) == HIGH);
    
    // Detecta mudança de estado
    if (currentSensorState != lastSensorState) {
        Serial.printf("Mudança de estado do sensor: %s -> %s\n", 
                     lastSensorState ? "LIVRE" : "INTERROMPIDA",
                     currentSensorState ? "LIVRE" : "INTERROMPIDA");
        
        // Publica estado via MQTT
        if (mqttConnected) {
            publish_sensor_state(currentSensorState);
            
            // Conta pizza (interrompida -> livre)
            if (!lastSensorState && currentSensorState) {
                pizzaCount++;
                Serial.printf("PIZZA DETECTADA! Total: %lu\n", pizzaCount);
            }
        } else {
            Serial.println("MQTT desconectado - não foi possível publicar estado");
        }
        
        lastSensorState = currentSensorState;
        delay(SENSOR_DEBOUNCE_DELAY);
    }
    
    // Heartbeat periódico
    if (now - lastMsg > HEARTBEAT_INTERVAL) {
        lastMsg = now;
        if (mqttConnected) {
            client.publish(mqtt_topic_heartbeat, "ativo");
            Serial.println("Heartbeat enviado");
        } else {
            Serial.println("Heartbeat não enviado - MQTT desconectado");
        }
    }
    
    // Delay curto para estabilidade
    delay(10);
}

// Funções auxiliares
void check_wifi_connection() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Conexão WiFi perdida! Tentando reconectar...");
        wifiConnected = false;
        setup_wifi();
        wifiConnected = true;
        Serial.printf("WiFi reconectado! IP: %s\n", WiFi.localIP().toString().c_str());
    }
}

// Debug (opcional)
void print_system_status() {
    Serial.println("\n=== STATUS DO SISTEMA ===");
    Serial.printf("WiFi: %s\n", wifiConnected ? "Conectado" : "Desconectado");
    Serial.printf("MQTT: %s\n", mqttConnected ? "Conectado" : "Desconectado");
    Serial.printf("Sensor: %s\n", lastSensorState ? "LIVRE" : "INTERROMPIDA");
    Serial.printf("Pizzas contadas: %lu\n", pizzaCount);
    Serial.printf("Tentativas MQTT: %lu\n", mqttReconnectAttempts);
    Serial.printf("Uptime: %lu segundos\n", millis() / 1000);
    Serial.println("========================\n");
}