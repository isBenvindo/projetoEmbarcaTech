# Configuração do Grafana - Sistema Terelina

## Visão Geral

Este guia explica como configurar o Grafana para visualizar os dados de contagem de pizzas do sistema Terelina.  
O sistema já está preparado com endpoints específicos para Grafana e views otimizadas no PostgreSQL.

---

## Pré-requisitos

- **Grafana** instalado (versão 8.0+)
- **Sistema Terelina** rodando (backend + banco PostgreSQL)
- **Acesso** ao banco de dados PostgreSQL

---

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
````

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

---

## Configuração Inicial

### 1. Acessar Grafana

* Navegar para `http://localhost:3000`
* Login padrão: `admin` / `admin`
* Alterar senha ao primeiro acesso

### 2. Configurar Data Source PostgreSQL

1. Ir para **Configuration → Data Sources**
2. Clicar em **"Add data source"**
3. Selecionar **"PostgreSQL"**
4. Configurar conexão:

```yaml
Name: Terelina PostgreSQL
Host: localhost:5432
Database: terelina_db
User: terelina_user
Password: sua_senha_aqui
SSL Mode: disable
```

5. Testar conexão e salvar

---

## Dashboards Recomendados

### Dashboard 1: Visão Geral da Produção

* **Título:** "Terelina - Visão Geral da Produção"
* **Refresh:** 30s

#### Painéis

**1. Total de Pizzas Hoje (Stat)**

```sql
SELECT total_contagens 
FROM estatisticas_hoje;
```

**2. Contagens por Hora (Time Series)**

```sql
SELECT 
    hora as time,
    total_contagens as value
FROM contagens_por_hora 
WHERE hora >= $__timeFrom() AND hora <= $__timeTo()
ORDER BY hora;
```

**3. Velocidade de Produção (Time Series)**

```sql
SELECT 
    hora as time,
    pizzas_por_hora as value
FROM velocidade_producao 
WHERE hora >= $__timeFrom() AND hora <= $__timeTo()
ORDER BY hora;
```

**4. Contagens por Dia (Bar Chart)**

```sql
SELECT 
    data as time,
    total_contagens as value
FROM contagens_por_dia 
WHERE data >= $__timeFrom() AND data <= $__timeTo()
ORDER BY data;
```

---

### Dashboard 2: Monitoramento em Tempo Real

* **Título:** "Terelina - Monitoramento Tempo Real"
* **Refresh:** 10s

#### Painéis

**1. Últimas Contagens (Time Series)**

```sql
SELECT 
    timestampz as time,
    1 as value
FROM contagens_pizzas 
WHERE timestampz >= $__timeFrom() AND timestampz <= $__timeTo()
ORDER BY timestampz;
```

**2. Status do Sistema (Stat)**

```sql
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 'Ativo'
        ELSE 'Inativo'
    END as value
FROM contagens_pizzas 
WHERE timestampz >= NOW() - INTERVAL '1 hour';
```

---

## Configuração de Alertas

### Alerta 1: Produção Parada

```yaml
Name: Produção Parada
Query: 
  SELECT COUNT(*) as contagens
  FROM contagens_pizzas 
  WHERE timestampz >= NOW() - INTERVAL '30 minutes'
Condition: contagens < 1
Duration: 5m
```

### Alerta 2: Baixa Produção

```yaml
Name: Baixa Produção
Query:
  SELECT COUNT(*) as contagens_hora
  FROM contagens_pizzas 
  WHERE timestampz >= NOW() - INTERVAL '1 hour'
Condition: contagens_hora < 10
Duration: 10m
```

---

## Queries Avançadas

**1. Média Móvel de Produção**

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

**2. Comparação com Dia Anterior**

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

**3. Horários de Pico**

```sql
SELECT 
    EXTRACT(hour FROM timestampz) as hora,
    COUNT(*) as contagens
FROM contagens_pizzas 
WHERE timestampz >= $__timeFrom() AND timestampz <= $__timeTo()
GROUP BY EXTRACT(hour FROM timestampz)
ORDER BY contagens DESC;
```

---

## Personalização Visual

### Cores Recomendadas

* **Verde:** Produção normal (> 80% da média)
* **Amarelo:** Produção moderada (50–80% da média)
* **Vermelho:** Baixa produção (< 50% da média)

### Configurações de Painéis

**Time Series**

```yaml
Draw mode: Lines
Line width: 2
Fill opacity: 10
Show points: Never
```

**Stat**

```yaml
Unit: short
Decimals: 0
Thresholds: 0, 50, 100
Color mode: value
```

---

## Automação

### Script de Backup de Dashboards

```bash
#!/bin/bash
# backup_dashboards.sh

GRAFANA_URL="http://localhost:3000"
API_KEY="sua_api_key_aqui"
BACKUP_DIR="/backup/grafana"

mkdir -p $BACKUP_DIR

curl -H "Authorization: Bearer $API_KEY" \
     "$GRAFANA_URL/api/search?type=dash-db" | \
jq -r '.[].uid' | \
while read uid; do
    curl -H "Authorization: Bearer $API_KEY" \
         "$GRAFANA_URL/api/dashboards/uid/$uid" | \
    jq '.dashboard' > "$BACKUP_DIR/dashboard_$uid.json"
done
```

---

## Troubleshooting

### Problemas Comuns

**1. Dados não aparecem**

* Verificar backend
* Testar conexão PostgreSQL
* Conferir se há registros em `contagens_pizzas`

**2. Queries lentas**

* Garantir índices no banco
* Usar views otimizadas
* Limitar dados com `LIMIT`

**3. Timezone incorreto**

```sql
SHOW timezone;
SET timezone = 'America/Sao_Paulo';
```

---

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

---

## Próximos Passos

1. Configurar alertas por email/SMS
2. Criar dashboards por turno
3. Implementar comparações históricas
4. Adicionar métricas de eficiência
5. Automatizar backup de dashboards

---

**Sistema Terelina v1.0.0 – Integração Grafana pronta para produção**