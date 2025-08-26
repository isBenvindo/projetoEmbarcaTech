# Projeto Terelina - Sistema de Contagem Automática de Pizzas

## Descrição

Sistema IoT para contagem automática de pizzas na Terelina, composto por um sensor de barreira óptica conectado a um ESP32 que envia dados via MQTT para um backend FastAPI que salva as contagens em um banco PostgreSQL. **Otimizado para integração com Grafana para dashboards em tempo real.**

## Arquitetura

```
[Sensor Óptico] → [ESP32] → [MQTT Broker] → [FastAPI Backend] → [PostgreSQL] → [Grafana]
```

### Componentes

- **Firmware ESP32**: Monitora sensor e publica estados via MQTT
- **Backend FastAPI**: Recebe dados MQTT e salva no banco
- **Banco PostgreSQL**: Armazena contagens de pizzas (tabela existente)
- **MQTT Broker**: HiveMQ (broker público)
- **Grafana**: Dashboards e visualizações em tempo real

## Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- PostgreSQL (com tabela `contagens_pizzas` existente)
- PlatformIO (para firmware ESP32)
- ESP32 DevKit
- Grafana (opcional, para dashboards)

### Backend

1. **Instalar dependências**:
```bash
cd back-end
pip install -r requirements.txt
```

2. **Configurar variáveis de ambiente**:
```bash
# Copiar arquivo de exemplo
cp env.example .env

# Editar arquivo .env com suas configurações
DB_HOST=localhost
DB_NAME=terelina_db
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_PORT=5432
```

3. **Executar schema do banco** (apenas tabelas auxiliares):
```sql
-- Conectar ao banco existente
\c terelina_db

-- Executar schema (cria views e tabelas auxiliares)
\i back-end/schema.sql
```

4. **Executar backend**:
```bash
cd back-end
python start_server.py
```

### Firmware ESP32

1. **Instalar PlatformIO**
2. **Configurar credenciais WiFi** em `firmware_esp32/src/config.cpp`
3. **Compilar e fazer upload**:
```bash
cd firmware_esp32
pio run --target upload
```

### Grafana (Opcional)

Consulte o guia completo: [GRAFANA_SETUP.md](GRAFANA_SETUP.md)

**Configuração rápida:**
1. Instalar Grafana
2. Configurar data source PostgreSQL
3. Importar dashboards recomendados

## Endpoints da API

### Endpoints Básicos
- `GET /`: Página inicial
- `GET /health`: Status da aplicação
- `GET /test_db_connection`: Testa conexão com banco
- `GET /contagens`: Lista últimas contagens
- `GET /contagens/estatisticas`: Estatísticas gerais
- `GET /logs`: Logs do sistema

### Endpoints para Grafana
- `GET /grafana/contagens-por-hora`: Contagens agrupadas por hora
- `GET /grafana/contagens-por-dia`: Contagens agrupadas por dia
- `GET /grafana/velocidade-producao`: Velocidade de produção
- `GET /grafana/estatisticas-hoje`: Estatísticas do dia atual
- `GET /grafana/ultimas-contagens`: Últimas contagens em tempo real
- `GET /grafana/metrics`: Lista de métricas disponíveis

## Configuração

### Variáveis de Ambiente (Backend)
- `DB_HOST`: Host do PostgreSQL
- `DB_NAME`: Nome do banco
- `DB_USER`: Usuário do banco
- `DB_PASSWORD`: Senha do banco
- `DB_PORT`: Porta do PostgreSQL
- `MQTT_BROKER_HOST`: Broker MQTT
- `LOG_LEVEL`: Nível de log (INFO, DEBUG, ERROR)

### Configurações ESP32
- WiFi SSID e senha
- Pino do sensor (padrão: 15)
- Configurações MQTT

## Monitoramento e Dashboards

### Views do Banco de Dados
O sistema cria automaticamente as seguintes views para Grafana:
- `contagens_por_hora`: Contagens agrupadas por hora
- `contagens_por_dia`: Contagens agrupadas por dia
- `estatisticas_hoje`: Estatísticas do dia atual
- `velocidade_producao`: Velocidade de produção
- `ultimas_contagens_24h`: Últimas contagens das 24h

### Dashboards Recomendados
1. **Visão Geral da Produção**: Métricas gerais e tendências
2. **Monitoramento Tempo Real**: Contagens em tempo real
3. **Análise de Performance**: Velocidade e eficiência

## Segurança

**Importante**: Este projeto usa credenciais hardcoded para demonstração. Em produção:
- Use variáveis de ambiente
- Implemente autenticação MQTT
- Use HTTPS
- Configure firewall adequadamente
- Configure autenticação no Grafana

## Troubleshooting

### ESP32 não conecta ao WiFi
- Verificar SSID e senha em `config.cpp`
- Verificar distância do roteador

### Backend não conecta ao banco
- Verificar se PostgreSQL está rodando
- Verificar credenciais no arquivo `.env`
- Verificar se banco `terelina_db` existe
- Verificar se tabela `contagens_pizzas` existe

### Dados não chegam via MQTT
- Verificar conexão WiFi do ESP32
- Verificar se broker HiveMQ está acessível
- Verificar logs do ESP32 via Serial Monitor

### Grafana não mostra dados
- Verificar data source PostgreSQL
- Testar queries diretamente no banco
- Verificar timezone das consultas
- Consultar logs do Grafana

## Melhorias Implementadas

### Funcionalidades Adicionadas
- [x] **Logging estruturado** com arquivo de log
- [x] **Configuração via variáveis de ambiente** (.env)
- [x] **Validação com Pydantic** para todos os endpoints
- [x] **Tratamento de erros robusto** com handlers globais
- [x] **CORS configurado** para integração web
- [x] **Endpoints específicos para Grafana**
- [x] **Views otimizadas** para dashboards
- [x] **Sistema de logs** centralizado
- [x] **Monitoramento de saúde** da aplicação
- [x] **API documentada** com Swagger
- [x] **Configuração flexível** via arquivos .env

### Integração Grafana
- [x] **Views otimizadas** para consultas
- [x] **Endpoints específicos** para time series
- [x] **Queries otimizadas** para performance
- [x] **Guia completo** de configuração
- [x] **Dashboards recomendados**
- [x] **Alertas configuráveis**

## Próximos Passos

- [ ] Interface web para visualização
- [ ] Autenticação MQTT
- [ ] Métricas e alertas avançados
- [ ] Backup automático
- [ ] Dockerização
- [ ] Testes automatizados
- [ ] API REST para configurações
- [ ] Sistema de notificações

## Documentação Adicional

- [Guia de Instalação Completo](INSTALACAO.md)
- [Configuração do Grafana](GRAFANA_SETUP.md)
- [API Documentation](http://localhost:8000/docs) (quando rodando)

## Contribuição

Para contribuir com o projeto:
1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Suporte

Para problemas ou dúvidas:
1. Verificar logs do sistema
2. Consultar documentação
3. Abrir issue no repositório
4. Contatar equipe de desenvolvimento

---

**Sistema Terelina v1.0.0** - Otimizado para produção e monitoramento em tempo real!