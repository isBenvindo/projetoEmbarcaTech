/**
 * @file wifi_manager.cpp
 * @brief Handles WiFi connectivity using the WiFiManager library.
 *
 * Features:
 * - Captive Portal for on-demand configuration (no hardcoded passwords).
 * - Automatic reconnection to the last known network.
 * - Optional secure fallback via secrets.h (compile-time gated).
 * - Avoids infinite reboot loops: if fallback fails, returns to portal mode.
 */

#include "wifi_manager.h"
#include "config.h"

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>  // tzapu/WiFiManager

// ---------------------------------------------------------------------
// Optional fallback credentials (compile-time gated)
// To enable: add in platformio.ini -> build_flags = -DTERELINA_USE_WIFI_FALLBACK
// And provide a secrets.h with FALLBACK_WIFI_SSID / FALLBACK_WIFI_PASSWORD
// ---------------------------------------------------------------------
#ifdef TERELINA_USE_WIFI_FALLBACK
  #include "secrets.h"
#endif

// =====================================================================
// Private helpers
// =====================================================================

static void onWifiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
    switch (event) {
        case ARDUINO_EVENT_WIFI_STA_CONNECTED:
            Serial.println(F("[WiFi Event] Station connected to AP."));
            break;

        case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
            Serial.print(F("[WiFi Event] Disconnected from AP. Reason: "));
            Serial.println((int)info.wifi_sta_disconnected.reason);
            // ESP32 will attempt to reconnect automatically (we also enforce it in setupWifi()).
            break;

        case ARDUINO_EVENT_WIFI_STA_GOT_IP:
            Serial.print(F("[WiFi Event] IP Address obtained: "));
            Serial.println(WiFi.localIP());
            break;

        default:
            break;
    }
}

static String buildApName() {
    // Unique AP name to avoid collisions when multiple devices are in the same area.
    // Example: Terelina-3FA2
    uint64_t mac = ESP.getEfuseMac();
    uint16_t suffix = (uint16_t)(mac & 0xFFFF);

    char buf[32];
    snprintf(buf, sizeof(buf), "Terelina-%04X", suffix);
    return String(buf);
}

static bool tryFallbackCredentials(uint32_t timeoutMs = 20000) {
#ifdef TERELINA_USE_WIFI_FALLBACK
    if (strlen(FALLBACK_WIFI_SSID) == 0) {
        Serial.println(F("[WiFi] Fallback enabled but SSID is empty. Skipping fallback."));
        return false;
    }

    Serial.println(F("[WiFi] Attempting fallback connection (secrets.h)..."));
    WiFi.begin(FALLBACK_WIFI_SSID, FALLBACK_WIFI_PASSWORD);

    uint32_t start = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - start) < timeoutMs) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(F("[WiFi] Fallback connection OK."));
        return true;
    }

    Serial.println(F("[WiFi] Fallback connection FAILED."));
    return false;
#else
    (void)timeoutMs;
    return false;
#endif
}

// =====================================================================
// Public Functions (defined in wifi_manager.h)
// =====================================================================

void setupWifi() {
    WiFi.onEvent(onWifiEvent);

    // Enforce station mode and reconnection behavior (good for corporate networks).
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);
    WiFi.persistent(true);

    WiFiManager wm;

    // Portal timeout: if nobody configures within this time, we can try fallback
    // or re-open portal again without reboot loop.
    wm.setConfigPortalTimeout(180); // 3 minutes

    // Unique AP name
    String apName = buildApName();
    Serial.print(F("[WiFi] Starting connection via WiFiManager. AP name: "));
    Serial.println(apName);

    // Attempt connection:
    // 1) last known credentials
    // 2) if fail: portal
    // 3) if portal times out: return false
    if (!wm.autoConnect(apName.c_str())) {
        Serial.println(F("[WiFi] Portal timed out."));

        // Optional fallback
        if (!tryFallbackCredentials(20000)) {
            // Avoid infinite reboot loops: return to portal mode and wait for config.
            Serial.println(F("[WiFi] No connection. Re-opening portal (no reboot loop)."));

            // Start config portal and wait until configured (blocking, but predictable in the field).
            // You can change to startConfigPortal + manual loop if you want non-blocking behavior.
            wm.setConfigPortalTimeout(0); // 0 = no timeout (wait indefinitely)
            if (!wm.startConfigPortal(apName.c_str())) {
                // In practice startConfigPortal should not return false with timeout=0,
                // but if it does, we fallback to a safe reboot.
                Serial.println(F("[WiFi] CRITICAL: Config portal failed unexpectedly. Rebooting..."));
                delay(3000);
                ESP.restart();
            }
        }
    }

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
