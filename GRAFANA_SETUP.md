# Configuração do Grafana - Sistema Terelina

## Visão Geral

Este guia explica como configurar o Grafana para visualizar os dados de contagem de pizzas do sistema Terelina. O sistema já está preparado com endpoints específicos para Grafana e views otimizadas no PostgreSQL.

## Pré-requisitos

- **Grafana** instalado (versão 8.0+)
- **Sistema Terelina** rodando (backend + banco PostgreSQL)
- **Acesso** ao banco de dados PostgreSQL

## Instalação do Grafana

### Ubuntu/Debian
```bash
# Adicionar repositório Grafana
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

# Instalar Grafana
sudo apt update
sudo apt install grafana

# Iniciar e habilitar serviço
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### Windows
1. Baixar o instalador do [site oficial do Grafana](https://grafana.com/grafana/download)
2. Executar o instalador
3. O Grafana estará disponível em `http://localhost:3000`

### Docker
```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana:latest
```

## Configuração Inicial

### 1. Acessar Grafana
- Abrir navegador em `http://localhost:3000`
- Login padrão: `admin` / `admin`
- Alterar senha quando solicitado

### 2. Configurar Data Source PostgreSQL

1. **Ir para Configuration → Data Sources**
2. **Clicar em "Add data source"**
3. **Selecionar "PostgreSQL"**
4. **Configurar conexão:**

```yaml
Name: Terelina PostgreSQL
Host: localhost:5432
Database: terelina_db
User: terelina_user
Password: sua_senha_aqui
SSL Mode: disable
```

5. **Testar conexão** e salvar

## Dashboards Recomendados

### Dashboard 1: Visão Geral da Produção

**Configuração:**
- **Título:** "Terelina - Visão Geral da Produção"
- **Refresh:** 30s

**Painéis:**

#### 1. Total de Pizzas Hoje (Single Stat)
```sql
-- Query
SELECT total_contagens 
FROM estatisticas_hoje;
```

#### 2. Contagens por Hora (Time Series)
```sql
-- Query
SELECT 
    hora as time,
    total_contagens as value
FROM contagens_por_hora 
WHERE hora >= $__timeFrom() AND hora <= $__timeTo()
ORDER BY hora;
```

#### 3. Velocidade de Produção (Time Series)
```sql
-- Query
SELECT 
    hora as time,
    pizzas_por_hora as value
FROM velocidade_producao 
WHERE hora >= $__timeFrom() AND hora <= $__timeTo()
ORDER BY hora;
```

#### 4. Contagens por Dia (Bar Chart)
```sql
-- Query
SELECT 
    data as time,
    total_contagens as value
FROM contagens_por_dia 
WHERE data >= $__timeFrom() AND data <= $__timeTo()
ORDER BY data;
```

### Dashboard 2: Monitoramento em Tempo Real

**Configuração:**
- **Título:** "Terelina - Monitoramento Tempo Real"
- **Refresh:** 10s

**Painéis:**

#### 1. Últimas Contagens (Time Series)
```sql
-- Query
SELECT 
    timestamp as time,
    1 as value
FROM contagens_pizzas 
WHERE timestamp >= $__timeFrom() AND timestamp <= $__timeTo()
ORDER BY timestamp;
```

#### 2. Status do Sistema (Stat)
```sql
-- Query
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 'Ativo'
        ELSE 'Inativo'
    END as value
FROM contagens_pizzas 
WHERE timestamp >= NOW() - INTERVAL '1 hour';
```

## Configuração de Alertas

### Alerta: Produção Parada

1. **Ir para Alerting → Alert Rules**
2. **Criar nova regra:**

```yaml
Name: Produção Parada
Query: 
  SELECT COUNT(*) as contagens
  FROM contagens_pizzas 
  WHERE timestamp >= NOW() - INTERVAL '30 minutes'
Condition: contagens < 1
Duration: 5m
```

### Alerta: Baixa Produção

```yaml
Name: Baixa Produção
Query:
  SELECT COUNT(*) as contagens_hora
  FROM contagens_pizzas 
  WHERE timestamp >= NOW() - INTERVAL '1 hour'
Condition: contagens_hora < 10
Duration: 10m
```

## Queries Avançadas

### 1. Média Móvel de Produção
```sql
SELECT 
    hora as time,
    AVG(total_contagens) OVER (
        ORDER BY hora 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as media_movel
FROM contagens_por_hora 
WHERE hora >= $__timeFrom() AND hora <= $__timeTo()
ORDER BY hora;
```

### 2. Comparação com Dia Anterior
```sql
SELECT 
    c1.data as time,
    c1.total_contagens as hoje,
    c2.total_contagens as ontem,
    (c1.total_contagens - c2.total_contagens) as diferenca
FROM contagens_por_dia c1
LEFT JOIN contagens_por_dia c2 ON c2.data = c1.data - INTERVAL '1 day'
WHERE c1.data >= $__timeFrom() AND c1.data <= $__timeTo()
ORDER BY c1.data;
```

### 3. Horários de Pico
```sql
SELECT 
    EXTRACT(hour FROM timestamp) as hora,
    COUNT(*) as contagens
FROM contagens_pizzas 
WHERE timestamp >= $__timeFrom() AND timestamp <= $__timeTo()
GROUP BY EXTRACT(hour FROM timestamp)
ORDER BY contagens DESC;
```

## Personalização Visual

### Cores Recomendadas
- **Verde:** Produção normal (> 80% da média)
- **Amarelo:** Produção moderada (50-80% da média)
- **Vermelho:** Baixa produção (< 50% da média)

### Configurações de Painéis

#### Time Series
```yaml
Display:
  - Draw mode: Lines
  - Line width: 2
  - Fill opacity: 10
  - Gradient mode: None
  - Show points: Never
```

#### Single Stat
```yaml
Display:
  - Unit: short
  - Decimals: 0
  - Color mode: value
  - Thresholds: 0, 50, 100
```

## Automação

### Script de Backup de Dashboards
```bash
#!/bin/bash
# backup_dashboards.sh

GRAFANA_URL="http://localhost:3000"
API_KEY="sua_api_key_aqui"
BACKUP_DIR="/backup/grafana"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup de todos os dashboards
curl -H "Authorization: Bearer $API_KEY" \
     "$GRAFANA_URL/api/search?type=dash-db" | \
jq -r '.[].uid' | \
while read uid; do
    curl -H "Authorization: Bearer $API_KEY" \
         "$GRAFANA_URL/api/dashboards/uid/$uid" | \
    jq '.dashboard' > "$BACKUP_DIR/dashboard_$uid.json"
done
```

### Configuração de API Key
1. **Ir para Configuration → API Keys**
2. **Criar nova key** com permissões de Admin
3. **Usar a key** nos scripts de automação

## Troubleshooting

### Problemas Comuns

#### 1. Dados não aparecem
- Verificar se o backend está rodando
- Testar conexão com PostgreSQL
- Verificar se há dados na tabela `contagens_pizzas`

#### 2. Queries lentas
- Verificar se os índices foram criados
- Otimizar queries com LIMIT
- Usar views em vez de queries complexas

#### 3. Timezone incorreto
```sql
-- Verificar timezone atual
SHOW timezone;

-- Alterar timezone se necessário
SET timezone = 'America/Sao_Paulo';
```

### Comandos de Diagnóstico
```bash
# Verificar se Grafana está rodando
sudo systemctl status grafana-server

# Verificar logs do Grafana
sudo tail -f /var/log/grafana/grafana.log

# Testar conexão com PostgreSQL
psql -h localhost -U terelina_user -d terelina_db -c "SELECT COUNT(*) FROM contagens_pizzas;"
```

## Dashboard Mobile

### Configuração para Dispositivos Móveis
1. **Usar painéis menores** (6x4 ou menor)
2. **Configurar refresh** mais frequente (15-30s)
3. **Usar cores contrastantes**
4. **Simplificar queries** para melhor performance

### Layout Responsivo
```yaml
Grid:
  - x: 0, y: 0, w: 12, h: 8  # Painel principal
  - x: 0, y: 8, w: 6, h: 4  # Painel secundário
  - x: 6, y: 8, w: 6, h: 4  # Painel secundário
```

## Segurança

### Configurações Recomendadas
```ini
# /etc/grafana/grafana.ini
[security]
allow_embedding = true
cookie_secure = true
cookie_samesite = strict

[server]
protocol = https
cert_file = /path/to/cert.pem
key_file = /path/to/key.pem
```

### Autenticação LDAP (Opcional)
```ini
[auth.ldap]
enabled = true
config_file = /etc/grafana/ldap.toml
```

## Métricas de Performance

### Monitoramento do Grafana
- **CPU:** < 50%
- **Memória:** < 2GB
- **Queries por segundo:** < 100
- **Tempo de resposta:** < 500ms

### Otimizações
1. **Usar cache** para queries frequentes
2. **Limitar dados** por painel
3. **Configurar timeouts** adequados
4. **Monitorar logs** regularmente

## Próximos Passos

1. **Configurar alertas** por email/SMS
2. **Criar dashboards** específicos por turno
3. **Implementar** comparações históricas
4. **Adicionar** métricas de eficiência
5. **Configurar** backup automático

---

**Nota:** Este guia assume que o sistema Terelina está rodando e acessível. Para problemas específicos, consulte a documentação oficial do Grafana ou entre em contato com a equipe de desenvolvimento.
