#include "mqtt.h"
#include "config.h"
#include <Arduino.h>
#include <WiFi.h> 
#include <WiFiClient.h>
#include <ArduinoJson.h> 

// Variáveis globais
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastReconnectAttempt = 0;
const unsigned long RECONNECT_INTERVAL = 5000; // intervalo de reconexão

// Reconeção MQTT
void reconnect_mqtt() {
    unsigned long now = millis();
    
    // Evita tentativas frequentes
    if (now - lastReconnectAttempt < RECONNECT_INTERVAL) {
        return;
    }
    
    lastReconnectAttempt = now;
    
    // Checa WiFi
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi desconectado - não é possível conectar MQTT");
        return;
    }
    
    Serial.print("Tentando conexão MQTT...");
    
    // Autenticação opcional
    bool useAuth = (strlen(mqtt_user) > 0 || strlen(mqtt_pass) > 0);
    bool connected = false;
    
    if (useAuth) {
        Serial.println(" (com autenticação)");
        connected = client.connect(mqtt_client_id, mqtt_user, mqtt_pass);
    } else {
        Serial.println(" (sem autenticação)");
        connected = client.connect(mqtt_client_id);
    }
    
    if (connected) {
        Serial.println("MQTT conectado com sucesso!");
        
        // Publica "online"
        client.publish(mqtt_topic_heartbeat, "online");
        Serial.println("Mensagem 'online' publicada");
        
        // Publica info do dispositivo
        publish_device_info();
        
    } else {
        Serial.print("Falha na conexão MQTT, rc=");
        Serial.print(client.state());
        
        // Tradução de erro
        const char* error_msg = "erro desconhecido";
        switch (client.state()) {
            case -4: error_msg = "MQTT_CONNECTION_TIMEOUT"; break;
            case -3: error_msg = "MQTT_CONNECTION_LOST"; break;
            case -2: error_msg = "MQTT_CONNECT_FAILED"; break;
            case -1: error_msg = "MQTT_DISCONNECTED"; break;
            case 1: error_msg = "MQTT_CONNECT_BAD_PROTOCOL"; break;
            case 2: error_msg = "MQTT_CONNECT_BAD_CLIENT_ID"; break;
            case 3: error_msg = "MQTT_CONNECT_UNAVAILABLE"; break;
            case 4: error_msg = "MQTT_CONNECT_BAD_CREDENTIALS"; break;
            case 5: error_msg = "MQTT_CONNECT_UNAUTHORIZED"; break;
        }
        
        Serial.printf(" (%s)\n", error_msg);
        Serial.printf("Próxima tentativa em %lu segundos\n", RECONNECT_INTERVAL / 1000);
    }
}

// Publica estado do sensor
void publish_sensor_state(bool is_free) {
    if (!client.connected()) {
        Serial.println("MQTT desconectado - não foi possível publicar estado");
        return;
    }
    
    StaticJsonDocument<200> doc;
    doc["id"] = mqtt_client_id;
    doc["timestamp"] = String(millis());
    doc["state"] = is_free ? "livre" : "interrompida";
    doc["uptime"] = String(millis() / 1000); // uptime (s)
    doc["rssi"] = WiFi.RSSI(); // RSSI

    char json_buffer[200];
    serializeJson(doc, json_buffer);

    bool published = client.publish(mqtt_topic_state, json_buffer);
    
    if (published) {
        Serial.printf("Estado publicado: %s\n", json_buffer);
    } else {
        Serial.println("Falha ao publicar estado do sensor");
    }
}

// Publica informações do dispositivo
void publish_device_info() {
    StaticJsonDocument<300> doc;
    doc["id"] = mqtt_client_id;
    doc["type"] = "sensor_barreira";
    doc["version"] = "1.0.0";
    doc["ip"] = WiFi.localIP().toString();
    doc["rssi"] = WiFi.RSSI();
    doc["uptime"] = String(millis() / 1000);
    doc["free_heap"] = ESP.getFreeHeap();
    doc["status"] = "online";

    char json_buffer[300];
    serializeJson(doc, json_buffer);

    String topic = String(mqtt_topic_heartbeat) + "/info";
    client.publish(topic.c_str(), json_buffer);
    
    Serial.printf("Informações do dispositivo publicadas: %s\n", json_buffer);
}

// Loop MQTT
void mqtt_loop() {
    client.loop();
}

// Verifica status MQTT
bool is_mqtt_connected() {
    return client.connected();
}

// Estatísticas MQTT
void print_mqtt_stats() {
    Serial.println("\n=== ESTATÍSTICAS MQTT ===");
    Serial.printf("Conectado: %s\n", client.connected() ? "Sim" : "Não");
    Serial.printf("Broker: %s:%d\n", mqtt_server, mqtt_port);
    Serial.printf("Client ID: %s\n", mqtt_client_id);
    Serial.printf("Tópico Estado: %s\n", mqtt_topic_state);
    Serial.printf("Tópico Heartbeat: %s\n", mqtt_topic_heartbeat);
    Serial.printf("Última tentativa: %lu ms atrás\n", millis() - lastReconnectAttempt);
    Serial.println("========================\n");
}