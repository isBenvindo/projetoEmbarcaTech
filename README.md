<p align="center">
  <img src="images/embarcatech_logo.png" alt="EmbarcaTech Logo" height="100"/>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/terelina_logo.png" alt="Terelina Logo" height="100"/>
</p>

# Terelina - Automated Pizza Counter System

An end-to-end IoT system for automatically counting products on a conveyor belt. This project utilizes an ESP32 with a barrier sensor, a Dockerized FastAPI backend, a PostgreSQL database, and Grafana for real-time data visualization and business insights.

This repository contains the **refactored version (v2.0)** of the project, focusing on robustness, scalability, and modern development best practices.

## System Architecture
```
[Barrier Sensor] → [ESP32] → [MQTT Broker] → [FastAPI Backend] → [PostgreSQL] → [Grafana]
```

## Core Features

- **Real-Time Counting:** An ESP32 microcontroller with an infrared barrier sensor detects and reports each product that passes.
- **Robust Communication:** Uses the MQTT protocol for reliable, low-latency communication between the device and the backend.
- **Dockerized Environment:** The entire backend, including the API and the PostgreSQL database, is containerized. A simple `docker-compose up` command is all that's needed to get started.
- **Modular FastAPI Backend:** A clean, modular, and high-performance API built with FastAPI, featuring a connection pool for efficient database handling.
- **Optimized Database:** The PostgreSQL schema is enhanced with `VIEW`s to pre-aggregate data, making Grafana queries extremely fast.
- **User-Friendly Device Setup:** The ESP32 firmware includes **WiFiManager**, which creates a web portal for easy WiFi configuration without needing to hardcode or re-flash for new credentials.
- **Advanced Data Simulation:** Includes Python scripts to populate the database with a year's worth of realistic data, enabling immediate and meaningful dashboard testing.

## Getting Started

This guide provides a quick start for the backend. For full details, see [INSTALLATION.md](./INSTALLATION.md).

### Prerequisites

- Git
- Docker & Docker Compose

### Quick Start Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-folder>
    ```

2.  **Build and run the containers:**
    ```bash
    # This will build the backend image and start the API and database services.
    docker-compose build
    docker-compose up -d
    ```

3.  **Verify the API:**
    - The API documentation will be available at **`http://localhost:8000/docs`**.
    - The API health check is at **`http://localhost:8000/health`**.

---

## Project Structure

The repository is organized into two main parts:

- **/firmware_esp32:** Contains the C++/Arduino code for the ESP32 microcontroller, managed with PlatformIO. It's responsible for reading the sensor and publishing data.
- **/back-end:** Contains the Dockerized Python FastAPI application, the database schema, and helper scripts for data population.

## Documentation

- **[INSTALLATION.md](./INSTALLATION.md):** A complete step-by-step guide to get the entire project running from scratch.
- **[GRAFANA_SETUP.md](./GRAFANA_SETUP.md):** Instructions on how to connect Grafana and create dashboards with useful, optimized queries.
- **API Documentation (Live):** Available at `http://localhost:8000/docs` when the backend is running.

---

## Partnership

This project is a collaboration between **Terelina** and the **EmbarcaTech Program - a Technological Residency in Embedded Systems**.