# Guia de Instalação - Sistema Terelina

## 0. Execução Rápida

Se já possui o **Docker** instalado, siga apenas estes passos:

```bash
# Clonar o repositório
git clone https://github.com/FayrosSky/Projeto-Terelina.git
cd Projeto-Terelina

# Subir os containers (banco + backend)
docker compose up --build -d

# Verificar status
docker ps

# Testar API
curl http://localhost:8000/health
```

Para encerrar os serviços:

```bash
docker compose down
```

Pronto — o sistema estará em execução no endereço `http://localhost:8000`.

---

## 1. Visão Geral

O sistema **Terelina** é composto por:

* Um backend desenvolvido em **FastAPI**, responsável pelo processamento das contagens;
* Um banco de dados **PostgreSQL**, utilizado para armazenamento;
* Um firmware para **ESP32**, responsável pela leitura do sensor de barreira óptica;
* Um painel de visualização opcional em **Grafana**.

A instalação pode ser feita de duas formas:

1. **Via Docker (recomendada)** – configuração automática e reprodutível.
2. **Manual (modo avançado)** – configuração tradicional e manual.

---

## 2. Instalação via Docker (Recomendada)

### 2.1 Pré-requisitos

* [Docker Desktop](https://www.docker.com/products/docker-desktop/)
* [Git](https://git-scm.com/downloads)

---

### 2.2 Clonar o Repositório

```bash
git clone https://github.com/FayrosSky/Projeto-Terelina.git
cd Projeto-Terelina
```

---

### 2.3 Subir o Sistema

O projeto contém os arquivos `Dockerfile` e `docker-compose.yml` configurados.

```bash
docker compose up --build -d
```

Isso inicia automaticamente:

* **PostgreSQL** (`terelina_db`)
* **Backend FastAPI** (`terelina_backend`)

---

### 2.4 Verificar Containers

```bash
docker ps
```

Saída esperada:

| CONTAINER NAME   | STATUS       | PORTS        |
| ---------------- | ------------ | ------------ |
| terelina_backend | Up (healthy) | 0.0.0.0:8000 |
| terelina_db      | Up (healthy) | 0.0.0.0:5432 |

---

### 2.5 Testar Conexão

```bash
curl http://localhost:8000/health
```

Saída esperada:

```json
{"status": "ok"}
```

---

### 2.6 Acessar o Banco de Dados

```bash
docker exec -it terelina_db psql -U postgres -d terelina_db
```

Exemplo de consulta:

```sql
SELECT * FROM contagens_pizzas ORDER BY timestamp DESC LIMIT 10;
```

---

### 2.7 Encerrar o Sistema

```bash
docker compose down
```

---

## 3. Instalação Manual (Modo Avançado)

> Use este modo apenas se preferir não utilizar Docker.

### 3.1 Requisitos

* **Python 3.8+**
* **PostgreSQL 12+**
* **PlatformIO** (para desenvolvimento do firmware ESP32)

---

### 3.2 Banco de Dados PostgreSQL

Conecte-se ao PostgreSQL e execute:

```sql
CREATE DATABASE terelina_db;
CREATE USER terelina_user WITH PASSWORD 'sua_senha_aqui';
GRANT ALL PRIVILEGES ON DATABASE terelina_db TO terelina_user;

CREATE TABLE IF NOT EXISTS contagens_pizzas (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 3.3 Configuração do Backend

```bash
pip install -r requirements.txt
cp env.example .env
nano .env
```

Exemplo de configuração `.env`:

```env
DB_HOST=localhost
DB_NAME=terelina_db
DB_USER=terelina_user
DB_PASSWORD=sua_senha_aqui
DB_PORT=5432
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

---

### 3.4 Executar Servidor

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 4. Firmware ESP32

### 4.1 Configurar Wi-Fi e MQTT

Arquivo: `firmware_esp32/src/config.cpp`

```cpp
const char* ssid = "SUA_REDE_WIFI";
const char* password = "SUA_SENHA_WIFI";
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const int sensor_pin = 15;
```

---

### 4.2 Compilar e Enviar

```bash
cd firmware_esp32
pio run
pio run --target upload
pio device monitor
```

---

## 5. Monitoramento com Grafana (Opcional)

Para visualizar as contagens em tempo real:

1. Acesse o Grafana em `http://localhost:3000`
2. Adicione uma nova fonte de dados **PostgreSQL**

   * Host: `localhost:5432`
   * Database: `terelina_db`
   * User: `postgres`
   * Password: `postgres`
3. Teste a conexão.
4. Crie um painel com a consulta:

```sql
SELECT COUNT(*) FROM contagens_pizzas;
```

---

## 6. Testes do Sistema

### 6.1 Testar API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/contagens/estatisticas
```

### 6.2 Testar Sensor

* Passe um objeto pela barreira óptica;
* Observe os logs no ESP32;
* Confirme a inserção no banco de dados.

---

## 7. Atualizações do Sistema

```bash
git pull origin main
docker compose down
docker compose up --build -d
```

---

## 8. Solução de Problemas

| Problema                      | Causa Provável                  | Solução                             |
| ----------------------------- | ------------------------------- | ----------------------------------- |
| Backend não conecta ao banco  | Banco de dados não inicializado | Verificar `docker ps`               |
| Dados não aparecem no Grafana | Query incorreta                 | Verificar fonte de dados no Grafana |
| ESP32 não conecta ao Wi-Fi    | Credenciais incorretas          | Revisar `config.cpp`                |
| Backend reinicia em loop      | `RELOAD=true` no `.env`         | Definir `RELOAD=false`              |

---

## 9. Créditos

**Sistema Terelina v1.0.0**
Desenvolvido em parceria com a empresa **Terelina** e o programa **EmbarcaTech**.

---