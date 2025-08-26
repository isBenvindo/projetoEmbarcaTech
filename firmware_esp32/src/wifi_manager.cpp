#include "wifi_manager.h"
#include "config.h"
#include <Arduino.h>
#include <WiFi.h> 

// Constantes
const unsigned long WIFI_TIMEOUT = 30000; // timeout WiFi
const unsigned long WIFI_RETRY_DELAY = 5000; // delay entre tentativas
const int MAX_WIFI_ATTEMPTS = 10; // tentativas máximas

// Variáveis globais
unsigned long wifiStartTime = 0;
int wifiAttempts = 0;

// Configuração WiFi
void setup_wifi() {
    wifiAttempts = 0;
    wifiStartTime = millis();
    
    Serial.println();
    Serial.println("Iniciando conexão WiFi...");
    Serial.printf("Rede: %s\n", ssid);
    
    // Modo WiFi
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    // Aguarda conexão com timeout
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        
        // Timeout
        if (millis() - wifiStartTime > WIFI_TIMEOUT) {
            Serial.println();
            Serial.println("Timeout na conexão WiFi!");
            Serial.println("Reiniciando tentativa...");
            
            wifiAttempts++;
            if (wifiAttempts >= MAX_WIFI_ATTEMPTS) {
                Serial.println("Máximo de tentativas WiFi atingido!");
                Serial.println("Reiniciando ESP32 em 10 segundos...");
                delay(10000);
                ESP.restart();
            }
            
            // Reinicia
            WiFi.disconnect();
            delay(WIFI_RETRY_DELAY);
            wifiStartTime = millis();
            WiFi.begin(ssid, password);
        }
    }
    
    Serial.println();
    Serial.println("WiFi conectado com sucesso!");
    Serial.printf("Endereço IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Força do sinal (RSSI): %d dBm\n", WiFi.RSSI());
    Serial.printf("Canal: %d\n", WiFi.channel());
    Serial.printf("Tentativas necessárias: %d\n", wifiAttempts + 1);
}

// Verifica status WiFi
bool is_wifi_connected() {
    return WiFi.status() == WL_CONNECTED;
}

// Reconecta WiFi
void reconnect_wifi() {
    Serial.println("Reconectando WiFi...");
    WiFi.disconnect();
    delay(1000);
    setup_wifi();
}

// Informações WiFi
void print_wifi_info() {
    Serial.println("\n=== INFORMAÇÕES WIFI ===");
    Serial.printf("Status: %s\n", WiFi.status() == WL_CONNECTED ? "Conectado" : "Desconectado");
    Serial.printf("SSID: %s\n", ssid);
    Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Gateway: %s\n", WiFi.gatewayIP().toString().c_str());
    Serial.printf("DNS: %s\n", WiFi.dnsIP().toString().c_str());
    Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
    Serial.printf("Canal: %d\n", WiFi.channel());
    Serial.printf("Tentativas: %d\n", wifiAttempts);
    Serial.println("========================\n");
}

// Monitora WiFi
void monitor_wifi() {
    static unsigned long lastCheck = 0;
    const unsigned long CHECK_INTERVAL = 30000; // 30 segundos
    
    if (millis() - lastCheck > CHECK_INTERVAL) {
        lastCheck = millis();
        
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("Conexão WiFi perdida! Tentando reconectar...");
            reconnect_wifi();
        } else {
            // Log periódico (opcional)
            Serial.printf("WiFi OK - RSSI: %d dBm\n", WiFi.RSSI());
        }
    }
}