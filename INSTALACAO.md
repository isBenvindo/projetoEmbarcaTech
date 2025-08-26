# Guia de Instalação - Sistema Terelina

## Pré-requisitos

### Software Necessário
- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 12+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **PlatformIO** - Para desenvolvimento do firmware ESP32
- **Git** - Para clonar o repositório

### Hardware Necessário
- **ESP32 DevKit** (qualquer versão)
- **Sensor de barreira óptica** (IR ou laser)
- **Cabo USB** para ESP32
- **Cabo de rede** para conexão com banco de dados

## Instalação Passo a Passo

### 1. Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd "Projeto EmbarcaTech Terelina - V1"
```

### 2. Configurar Banco de Dados PostgreSQL

#### 2.1 Instalar PostgreSQL
- **Windows**: Baixar e instalar do site oficial
- **Linux**: `sudo apt-get install postgresql postgresql-contrib`
- **macOS**: `brew install postgresql`

#### 2.2 Criar Banco de Dados
```bash
# Conectar ao PostgreSQL
sudo -u postgres psql

# Criar banco e usuário
CREATE DATABASE terelina_db;
CREATE USER terelina_user WITH PASSWORD 'sua_senha_aqui';
GRANT ALL PRIVILEGES ON DATABASE terelina_db TO terelina_user;
\q
```

#### 2.3 Executar Schema
```bash
# Conectar ao banco criado
psql -U terelina_user -d terelina_db -h localhost

# Executar o schema
\i back-end/schema.sql
```

### 3. Configurar Backend

#### 3.1 Instalar Dependências Python
```bash
cd back-end
pip install -r requirements.txt
```

#### 3.2 Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp env.example .env

# Editar arquivo .env com suas configurações
nano .env
```

**Exemplo de configuração `.env`:**
```env
# Configurações do Banco de Dados PostgreSQL
DB_HOST=localhost
DB_NAME=terelina_db
DB_USER=terelina_user
DB_PASSWORD=sua_senha_aqui
DB_PORT=5432

# Configurações MQTT
MQTT_BROKER_HOST=broker.hivemq.com
MQTT_BROKER_PORT=1883
MQTT_TOPIC_STATE=sensores/barreira/estado
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=terelina_backend

# Configurações da Aplicação
LOG_LEVEL=INFO
```

#### 3.3 Testar Backend
```bash
# Usar script de inicialização
python start_server.py

# Ou usar uvicorn diretamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Configurar Firmware ESP32

#### 4.1 Instalar PlatformIO
```bash
# Via pip
pip install platformio

# Ou via VS Code extension
# Instalar extensão "PlatformIO IDE"
```

#### 4.2 Configurar WiFi e MQTT
Editar arquivo `firmware_esp32/src/config.cpp`:

```cpp
// Configurações de rede WiFi
const char* ssid = "SUA_REDE_WIFI";
const char* password = "SUA_SENHA_WIFI";

// Configurações MQTT (manter padrão para HiveMQ)
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
```

#### 4.3 Compilar e Fazer Upload
```bash
cd firmware_esp32

# Compilar
pio run

# Fazer upload para ESP32
pio run --target upload

# Monitorar serial
pio device monitor
```

### 5. Conectar Hardware

#### 5.1 Conexões ESP32
- **VCC** do sensor → **3.3V** do ESP32
- **GND** do sensor → **GND** do ESP32
- **Sinal** do sensor → **GPIO 15** do ESP32

#### 5.2 Posicionamento do Sensor
- Instalar sensor de barreira na linha de produção
- Alinhar emissor e receptor
- Testar detecção de objetos

## Configurações Avançadas

### Configurações de Segurança
```env
# Para produção, use um broker MQTT privado
MQTT_BROKER_HOST=seu_broker_mqtt.com
MQTT_USERNAME=seu_usuario
MQTT_PASSWORD=sua_senha

# Configurar HTTPS
USE_HTTPS=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### Configurações de Performance
```env
# Pool de conexões do banco
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Configurações de cache
CACHE_TTL=300
```

## Testes

### 1. Testar Backend
```bash
# Verificar saúde da API
curl http://localhost:8000/health

# Testar conexão com banco
curl http://localhost:8000/test_db_connection

# Ver estatísticas
curl http://localhost:8000/contagens/estatisticas
```

### 2. Testar MQTT
```bash
# Instalar cliente MQTT
pip install paho-mqtt

# Testar publicação
python -c "
import paho.mqtt.publish as publish
publish.single('sensores/barreira/estado', 
               '{\"id\":\"test\",\"state\":\"livre\",\"timestamp\":\"123456\"}', 
               hostname='broker.hivemq.com')
"
```

### 3. Testar Sensor
- Passar objeto pela barreira óptica
- Verificar logs no ESP32
- Confirmar recebimento no backend

## Monitoramento

### Logs do Sistema
```bash
# Ver logs do backend
tail -f back-end/terelina_backend.log

# Ver logs do banco
psql -U terelina_user -d terelina_db -c "SELECT * FROM logs_sistema ORDER BY timestamp DESC LIMIT 10;"
```

### Métricas
- **API**: http://localhost:8000/docs (Swagger UI)
- **Estatísticas**: http://localhost:8000/contagens/estatisticas
- **Logs**: http://localhost:8000/logs

## Troubleshooting

### Problemas Comuns

#### ESP32 não conecta ao WiFi
- Verificar SSID e senha
- Verificar distância do roteador
- Verificar se a rede é 2.4GHz

#### Backend não conecta ao banco
- Verificar se PostgreSQL está rodando
- Verificar credenciais no `.env`
- Verificar se banco existe

#### Dados não chegam via MQTT
- Verificar conexão WiFi do ESP32
- Verificar se broker está acessível
- Verificar tópicos MQTT

#### Sensor não detecta
- Verificar conexões elétricas
- Verificar alinhamento do sensor
- Verificar tensão de alimentação

### Comandos de Diagnóstico
```bash
# Status do PostgreSQL
sudo systemctl status postgresql

# Logs do PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log

# Testar conectividade MQTT
ping broker.hivemq.com

# Verificar portas abertas
netstat -tulpn | grep :8000
```

## Suporte

Para problemas ou dúvidas:
1. Verificar logs do sistema
2. Consultar documentação
3. Abrir issue no repositório
4. Contatar equipe de desenvolvimento

## Atualizações

Para atualizar o sistema:
```bash
# Atualizar código
git pull origin main

# Atualizar dependências
pip install -r requirements.txt

# Recompilar firmware
cd firmware_esp32
pio run --target upload

# Reiniciar backend
python start_server.py
```
