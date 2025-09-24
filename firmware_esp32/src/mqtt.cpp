#include "mqtt.h"
#include "config.h"
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// ===== Globais =====
WiFiClient espClient;
PubSubClient client(espClient);

static unsigned long lastReconnectAttempt = 0;
static const unsigned long RECONNECT_INTERVAL = 5000; // ms

// ===== NOVO: inicialização do cliente MQTT =====
void mqtt_init() {
  // Antes não havia setServer nem ajuste de buffer, causando falhas silenciosas.
  client.setServer(mqtt_server, mqtt_port);
  client.setBufferSize(512);   // JSONs >128 bytes
  client.setKeepAlive(30);     // mais resiliente
  client.setSocketTimeout(5);  // evita travas longas
}

// ===== Conexão MQTT com LWT + retain no "online" =====
void reconnect_mqtt() {
  unsigned long now = millis();
  if (now - lastReconnectAttempt < RECONNECT_INTERVAL) return;
  lastReconnectAttempt = now;

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado - não é possível conectar MQTT");
    return;
  }

  Serial.print("Tentando conexão MQTT... ");

  const char* willMsg = "{\"status\":\"offline\"}";
  bool useAuth = (mqtt_user && strlen(mqtt_user) > 0) || (mqtt_pass && strlen(mqtt_pass) > 0);
  bool connected = false;

  if (useAuth) {
    Serial.println("(com autenticação + LWT)");
    // overload: client.connect(clientId, user, pass, willTopic, willQos, willRetain, willMessage)
    connected = client.connect(
      mqtt_client_id,
      mqtt_user, mqtt_pass,
      mqtt_topic_state,  // willTopic
      1,                 // willQos (PubSubClient publica QoS0 por baixo, ok)
      true,              // willRetain
      willMsg
    );
  } else {
    Serial.println("(sem autenticação + LWT)");
    // overload: client.connect(clientId, willTopic, willQos, willRetain, willMessage)
    connected = client.connect(
      mqtt_client_id,
      mqtt_topic_state,
      1,
      true,
      willMsg
    );
  }

  if (connected) {
    Serial.println("MQTT conectado com sucesso!");

    // Publica "online" com retain => painéis/consumidores veem o estado atual imediatamente
    client.publish(mqtt_topic_state, "{\"status\":\"online\"}", true /*retain*/);
    Serial.println("Estado 'online' publicado (retain)");

    publish_device_info();
  } else {
    Serial.print("Falha na conexão MQTT, rc=");
    Serial.print(client.state());
    const char* error_msg = "erro desconhecido";
    switch (client.state()) {
      case -4: error_msg = "MQTT_CONNECTION_TIMEOUT"; break;
      case -3: error_msg = "MQTT_CONNECTION_LOST"; break;
      case -2: error_msg = "MQTT_CONNECT_FAILED"; break;
      case -1: error_msg = "MQTT_DISCONNECTED"; break;
      case 1:  error_msg = "MQTT_CONNECT_BAD_PROTOCOL"; break;
      case 2:  error_msg = "MQTT_CONNECT_BAD_CLIENT_ID"; break;
      case 3:  error_msg = "MQTT_CONNECT_UNAVAILABLE"; break;
      case 4:  error_msg = "MQTT_CONNECT_BAD_CREDENTIALS"; break;
      case 5:  error_msg = "MQTT_CONNECT_UNAUTHORIZED"; break;
    }
    Serial.printf(" (%s)\nPróxima tentativa em %lu s\n", error_msg, RECONNECT_INTERVAL / 1000);
  }
}

// ===== Publica estado do sensor =====
void publish_sensor_state(bool is_free) {
  if (!client.connected()) {
    Serial.println("MQTT desconectado - não foi possível publicar estado");
    return;
  }

  StaticJsonDocument<200> doc;
  doc["id"] = mqtt_client_id;
  doc["timestamp_ms"] = (uint64_t)millis();                // numérico
  doc["state"] = is_free ? "livre" : "interrompido";       // padronizado c/ backend
  doc["uptime_s"] = (uint32_t)(millis() / 1000);
  doc["rssi"] = WiFi.RSSI();

  char json_buffer[200];
  size_t n = serializeJson(doc, json_buffer);

  bool ok = client.publish(mqtt_topic_state, json_buffer, false /*retain*/);
  if (ok) Serial.printf("Estado publicado: %s\n", json_buffer);
  else    Serial.println("Falha ao publicar estado do sensor");
}

// ===== Publica informações do dispositivo =====
void publish_device_info() {
  StaticJsonDocument<320> doc;
  doc["id"] = mqtt_client_id;
  doc["type"] = "sensor_barreira";
  doc["version"] = "1.0.0";
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["uptime_s"] = (uint32_t)(millis() / 1000);
  doc["free_heap"] = ESP.getFreeHeap();
  doc["status"] = "online";

  char json_buffer[320];
  size_t n = serializeJson(doc, json_buffer);

  String topic = String(mqtt_topic_heartbeat) + "/info";
  client.publish(topic.c_str(), json_buffer, false);
  Serial.printf("Informações do dispositivo publicadas: %s\n", json_buffer);
}

// ===== Ciclo =====
void mqtt_loop() { client.loop(); }

// ===== Status / debug =====
bool is_mqtt_connected() { return client.connected(); }

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
