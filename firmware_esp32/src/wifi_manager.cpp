/**
 * @file wifi_manager.cpp
 * @brief Handles WiFi connectivity using the WiFiManager library.
 *
 * Features:
 * - Captive Portal for on-demand configuration (no hardcoded passwords).
 * - Automatic reconnection to the last known network.
 * - Secure fallback to credentials defined in secrets.h if the portal times out.
 */

#include "wifi_manager.h"
#include "config.h"
#include "secrets.h"      // Include the secrets file for fallback credentials
#include <WiFi.h>
#include <WiFiManager.h>  // This line requires the "tzapu/WiFiManager" library in platformio.ini

// =====================================================================
// Private Event Handler
// =====================================================================

/**
 * @brief Captures WiFi events to provide detailed logs for debugging.
 */
static void onWifiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
    switch (event) {
        case ARDUINO_EVENT_WIFI_STA_CONNECTED:
            Serial.println(F("[WiFi Event] Station connected to AP."));
            break;
        case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
            Serial.print(F("[WiFi Event] Disconnected from AP. Reason: "));
            Serial.println((int)info.wifi_sta_disconnected.reason);
            // The ESP32 will automatically try to reconnect. We don't need manual code for this.
            break;
        case ARDUINO_EVENT_WIFI_STA_GOT_IP:
            Serial.print(F("[WiFi Event] IP Address obtained: "));
            Serial.println(WiFi.localIP());
            break;
        default:
            // Other events are ignored
            break;
    }
}

// =====================================================================
// Public Functions (defined in wifi_manager.h)
// =====================================================================

void setupWifi() {
    // Register the event handler for better debugging feedback
    WiFi.onEvent(onWifiEvent);

    // Initialize the WiFiManager object
    WiFiManager wm;

    // Set a timeout for the configuration portal (in seconds).
    // If no one configures the device within this time, it will proceed to the fallback.
    wm.setConfigPortalTimeout(180); // 3 minutes

    // Set the name of the Access Point that will be created if connection fails
    const char* apName = "Terelina-Config-Portal";

    Serial.println(F("[WiFi] Starting connection process via WiFiManager..."));

    // wm.autoConnect() is a blocking function with the following logic:
    // 1. Tries to connect to the last saved WiFi credentials.
    // 2. If it fails, it starts an Access Point (AP) with the name specified (apName).
    // 3. It waits for a user to connect to the AP, open the captive portal, and enter new credentials.
    // 4. Returns 'true' if connected successfully (either way), 'false' if the portal times out.
    if (!wm.autoConnect(apName)) {
        Serial.println(F("[WiFi] Portal timed out. Attempting fallback from secrets.h..."));
        
        // --- Fallback Logic ---
        // If the portal times out, try connecting with the credentials from secrets.h
        WiFi.begin(FALLBACK_WIFI_SSID, FALLBACK_WIFI_PASSWORD);
        
        unsigned long startAttemptTime = millis();
        // Wait for up to 20 seconds for the fallback connection
        while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 20000) {
            delay(500);
            Serial.print(".");
        }
        Serial.println();

        if (WiFi.status() != WL_CONNECTED) {
            Serial.println(F("[WiFi] CRITICAL: Fallback connection failed. Restarting in 10 seconds..."));
            delay(10000);
            ESP.restart();
        }
    }
    
    // If we reach this point, we are connected (either via Manager or fallback)
    Serial.println(F("[WiFi] Connection established!"));
    printWifiStatus();
}

bool isWifiConnected() {
    return (WiFi.status() == WL_CONNECTED);
}

void printWifiStatus() {
    if (isWifiConnected()) {
        Serial.println(F("\n--- WiFi Status ---"));
        Serial.print(F("SSID: ")); Serial.println(WiFi.SSID());
        Serial.print(F("IP Address: ")); Serial.println(WiFi.localIP());
        Serial.print(F("Signal Strength (RSSI): ")); Serial.print(WiFi.RSSI()); Serial.println(F(" dBm"));
        Serial.println(F("-------------------\n"));
    } else {
        Serial.println(F("[WiFi] Status: Currently Disconnected"));
    }
}