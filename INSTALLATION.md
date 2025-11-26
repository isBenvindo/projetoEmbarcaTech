# Installation and Setup Guide

This guide provides step-by-step instructions to set up and run the Terelina Pizza Counter project locally. The recommended method is using Docker, which is simpler and more reliable for development and testing.

## 1. Docker Installation (Recommended)

This method sets up the backend API and the PostgreSQL database.

### 1.1. Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/downloads)
- [Python 3.9+](https://www.python.org/downloads/) (for running helper scripts)

### 1.2. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

### 1.3. Build and Run the System
From the project's root directory, execute the following commands:

```bash
# 1. Build the backend's Docker image
docker-compose build

# 2. Start the backend and database containers in the background
docker-compose up -d
```

### 1.4. Verify the Containers are Running
Check the status of the running containers:
```bash
docker ps
```
You should see the database and backend containers (by service or container name). The compose file defines a `db` service with `container_name: terelina_db` and a `backend` service with `container_name: terelina_backend`.

### 1.5. Test the API
You can test if the API is live by accessing its health check endpoint:

```bash
curl http://localhost:8000/health
```

Alternatively, open your browser and navigate to the interactive API documentation at `http://localhost:8000/docs`.

---

## 1.6. Populate the Database (Optional)

To test dashboards with realistic data, run the provided SQL script which inserts one year of simulated data.

First, ensure you have the required Python libraries installed in a local virtual environment (optional, only if you will run Python helper scripts):

```bash
# Create and activate a virtual environment
python -m venv venv
# On Windows (PowerShell): .\venv\Scripts\Activate.ps1
# On macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Then, execute the population SQL using `docker-compose`. Use the service name (`db`) shown in the compose file when using `docker-compose exec`, or use the container name if you prefer `docker exec`:

PowerShell (recommended on Windows):

```powershell
Get-Content back-end/scripts/populate_db.sql | docker-compose exec -T db psql -U postgres -d terelina_db
```

POSIX shells (Linux/macOS):

```bash
docker-compose exec -T db psql -U postgres -d terelina_db < back-end/scripts/populate_db.sql
```

If you prefer to use the container name directly:

```bash
docker exec -i terelina_db psql -U postgres -d terelina_db < back-end/scripts/populate_db.sql
```

### 1.7. Shutting Down the System

To stop and remove the containers, run:

```bash
docker-compose down
```

---

## 2. Firmware Setup (ESP32)

### 2.1. Prerequisites

- [Visual Studio Code](https://code.visualstudio.com/)
- [PlatformIO IDE Extension for VS Code](https://platformio.org/install/ide?install=vscode)

### 2.2. Open the Project in PlatformIO

1.  In VS Code, open the PlatformIO extension tab (plug/ant icon).
2.  Click **"Open Project"**.
3.  Navigate to and select the `firmware_esp32` folder from this repository.
4.  PlatformIO will detect `platformio.ini` and install required libraries (e.g., `PubSubClient`, `WiFiManager`).

### 2.3. Configure Fallback Credentials (For Development)

For development convenience, you can set fallback WiFi credentials used if the configuration portal times out.

1.  In the `firmware_esp32/src/` folder, create a file named `secrets.h` (this file is ignored by Git).
2.  Add the following content, replacing the placeholders with your local WiFi details:

```cpp
#ifndef SECRETS_H
#define SECRETS_H

#define FALLBACK_WIFI_SSID "your_ssid"
#define FALLBACK_WIFI_PASSWORD "your_password"

#endif
```

### 2.4. Build and Upload

1.  Connect your ESP32 board to your computer via USB.
2.  In the PlatformIO toolbar at the bottom of VS Code, click the **Upload** button to compile and flash the ESP32.

### 2.5. Configure WiFi via Web Portal

1.  After uploading, open the **Serial Monitor** (plug icon) to view device logs.
2.  On first boot without saved credentials, the ESP32 creates a WiFi Access Point named **`Terelina-Config-Portal`**.
3.  Connect to that network from a phone/computer and complete the captive portal form to save local WiFi credentials.
4.  The ESP32 will restart and connect to your network; verify via the Serial Monitor logs.

---

## 3. Environment Configuration (`.env` file)

The backend's configuration is managed through an environment file named `back-end/.env`.

If you clone the repository and `back-end/.env` is missing, create one by copying the provided example file:

PowerShell:

```powershell
Copy-Item back-end/env.example back-end/.env
```

POSIX shells:

```bash
cp back-end/env.example back-end/.env
```

Only modify the values if you need to connect to an external database or MQTT broker. For a standard local installation with Docker Compose, the defaults in `env.example` should work.

### 3.1. Example `.env` (for reference)

```ini
# Database
DB_HOST=db
DB_NAME=terelina_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432

# MQTT Broker
MQTT_BROKER_HOST=broker.hivemq.com
MQTT_BROKER_PORT=1883
MQTT_TOPIC_STATE=sensors/barrier/state
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=terelina_backend_refactored

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
RELOAD=false
```

---

## 4. Security Note

- The project uses default credentials for development convenience (Postgres: `postgres/postgres`, Grafana: `admin/admin`). These are intended only for local testing. Do not use these credentials in production or on exposed networks.
- If you expose services beyond localhost, change passwords and secure access appropriately.

## 5. Next Steps / Recommendations

- Consider adding Grafana provisioning or exporting a dashboard JSON to `images/` or a `grafana/` folder so dashboards can be imported automatically in tests/CI.
- Keep `back-end/.env` out of version control and document any changes in a developer setup section.