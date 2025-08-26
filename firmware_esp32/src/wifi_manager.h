#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>

// Funções principais
void setup_wifi();

// Funções auxiliares
bool is_wifi_connected();
void reconnect_wifi();
void print_wifi_info();
void monitor_wifi();

#endif