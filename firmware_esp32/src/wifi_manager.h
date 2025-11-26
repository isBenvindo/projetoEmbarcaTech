#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>

/**
 * @brief Initializes and manages the WiFi connection.
 * On first boot, or if the connection fails, it starts a configuration portal (Access Point).
 * Otherwise, it connects to the last known network. This is a blocking function.
 */
void setupWifi();

/**
 * @brief Checks if the device is currently connected to a WiFi network.
 * @return True if connected, false otherwise.
 */
bool isWifiConnected();

/**
 * @brief Prints current WiFi network details (IP, SSID, RSSI) to the Serial Monitor.
 * Useful for debugging.
 */
void printWifiStatus();

#endif // WIFI_MANAGER_H