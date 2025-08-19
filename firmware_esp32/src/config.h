#ifndef CONFIG_H
#define CONFIG_H

extern const char* ssid;
extern const char* password;

extern const char* mqtt_server;
extern const int mqtt_port;
extern const char* mqtt_user;
extern const char* mqtt_pass;
extern const char* mqtt_topic_state;
extern const char* mqtt_topic_heartbeat;
extern const char* mqtt_client_id;

extern const int SENSOR_PIN;

#endif