/**
 * @file wifi_manager.cpp
 * @brief Handles WiFi connectivity using the WiFiManager library.
 *
 * Features:
 * - Captive Portal for on-demand configuration (no hardcoded passwords).
 * - Automatic reconnection to the last known network.
 * - Maintenance Mode: hold BOOT (GPIO0) for 5s during boot to clear saved WiFi and force portal.
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
// Maintenance Mode Settings
// =====================================================================
// BOOT button on most ESP32 devkits is GPIO0 (active LOW).
static constexpr int      MAINT_PIN   = 0;       // GPIO0 (BOOT)
static constexpr uint32_t MAINT_HOLD_MS = 5000;  // 5 seconds hold to trigger

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

static bool maintenanceRequested() {
    // Check only at boot time. Holding BOOT (GPIO0) LOW for MAINT_HOLD_MS triggers maintenance.
    pinMode(MAINT_PIN, INPUT_PULLUP);
    delay(30); // stabilize read

    if (digitalRead(MAINT_PIN) == HIGH) {
        return false; // not pressed
    }

    Serial.println(F("[WiFi] BOOT detected. Hold for 5s to enter Maintenance Mode..."));

    uint32_t start = millis();
    while (millis() - start < MAINT_HOLD_MS) {
        if (digitalRead(MAINT_PIN) == HIGH) {
            Serial.println(F("[WiFi] Maintenance canceled (button released)."));
            return false;
        }

        // Optional progress tick each second (non-spammy)
        static uint32_t lastTick = 0;
        uint32_t elapsed = millis() - start;
        if (elapsed - lastTick >= 1000) {
            lastTick = elapsed;
            uint32_t remaining = (MAINT_HOLD_MS - elapsed + 999) / 1000;
            Serial.print(F("[WiFi] Holding... "));
            Serial.print(remaining);
            Serial.println(F("s"));
        }

        delay(10);
    }

    Serial.println(F("[WiFi] Maintenance Mode confirmed."));
    return true;
}

static void clearSavedWifi(WiFiManager& wm) {
    Serial.println(F("[WiFi] Clearing saved WiFi credentials (WiFiManager + ESP32 WiFi)..."));
    // Clears WiFiManager saved credentials
    wm.resetSettings();

    // Clears ESP32 WiFi stored credentials (NVS for WiFi)
    WiFi.disconnect(true, true);
    delay(200);
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

    // Unique AP name
    String apName = buildApName();

    // Maintenance Mode: hold BOOT during boot to clear creds and force portal
    if (maintenanceRequested()) {
        clearSavedWifi(wm);
    }

    // Portal timeout: if nobody configures within this time, we can try fallback
    // or re-open portal again without reboot loop.
    wm.setConfigPortalTimeout(180); // 3 minutes

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
            wm.setConfigPortalTimeout(0); // 0 = no timeout (wait indefinitely)
            if (!wm.startConfigPortal(apName.c_str())) {
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