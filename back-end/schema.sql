-- Schema Terelina (UTC-aware, sem índices)

-- ======================================================================
-- Tabelas
-- ======================================================================

-- Tabela principal
CREATE TABLE IF NOT EXISTS contagens_pizzas (
    id SERIAL PRIMARY KEY,
    -- timestamptz armazena em UTC e converte na leitura conforme timezone da sessão
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela: logs do sistema
CREATE TABLE IF NOT EXISTS logs_sistema (
    id SERIAL PRIMARY KEY,
    nivel VARCHAR(10) NOT NULL, -- INFO|WARNING|ERROR
    mensagem TEXT NOT NULL,
    origem VARCHAR(50) NOT NULL, -- backend|mqtt|sensor
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela: configurações do sistema
CREATE TABLE IF NOT EXISTS configuracoes_sistema (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    descricao TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================================
-- Views (UTC friendly) - recriáveis
-- ======================================================================

CREATE OR REPLACE VIEW contagens_por_hora AS
SELECT 
    DATE_TRUNC('hour', timestamp) AS hora,
    COUNT(*) AS total_contagens,
    EXTRACT(EPOCH FROM DATE_TRUNC('hour', timestamp)) AS timestamp_unix
FROM contagens_pizzas
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hora;

CREATE OR REPLACE VIEW contagens_por_dia AS
SELECT 
    DATE(timestamp) AS data,
    COUNT(*) AS total_contagens,
    EXTRACT(EPOCH FROM DATE(timestamp)) AS timestamp_unix
FROM contagens_pizzas
GROUP BY DATE(timestamp)
ORDER BY data;

CREATE OR REPLACE VIEW estatisticas_hoje AS
SELECT 
    COUNT(*) AS total_contagens,
    MIN(timestamp::time) AS primeiro_horario,
    MAX(timestamp::time) AS ultimo_horario,
    DATE(timestamp) AS data,
    EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) AS timestamp_unix
FROM contagens_pizzas
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY DATE(timestamp);

CREATE OR REPLACE VIEW ultimas_contagens_24h AS
SELECT 
    id,
    timestamp,
    EXTRACT(EPOCH FROM timestamp) AS timestamp_unix,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - timestamp))::INTEGER AS segundos_atras
FROM contagens_pizzas
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY timestamp DESC;

CREATE OR REPLACE VIEW velocidade_producao AS
SELECT 
    DATE_TRUNC('hour', timestamp) AS hora,
    COUNT(*) AS pizzas_por_hora,
    EXTRACT(EPOCH FROM DATE_TRUNC('hour', timestamp)) AS timestamp_unix,
    ROUND(COUNT(*)::NUMERIC / 1, 2) AS pizzas_por_hora_decimal
FROM contagens_pizzas
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hora;

-- ======================================================================
-- Funções (ajustadas para TIMESTAMPTZ)
-- ======================================================================

-- Contagens por intervalo
CREATE OR REPLACE FUNCTION get_contagens_intervalo(
    inicio_timestamp TIMESTAMPTZ,
    fim_timestamp    TIMESTAMPTZ,
    intervalo_minutos INTEGER DEFAULT 60
)
RETURNS TABLE (
    periodo TIMESTAMPTZ,
    contagens BIGINT,
    timestamp_unix BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE_TRUNC('hour', c.timestamp) + 
        (EXTRACT(MINUTE FROM c.timestamp)::INTEGER / intervalo_minutos) * 
        (intervalo_minutos || ' minutes')::INTERVAL AS periodo,
        COUNT(*)::BIGINT AS contagens,
        EXTRACT(EPOCH FROM (
            DATE_TRUNC('hour', c.timestamp) + 
            (EXTRACT(MINUTE FROM c.timestamp)::INTEGER / intervalo_minutos) * 
            (intervalo_minutos || ' minutes')::INTERVAL
        ))::BIGINT AS timestamp_unix
    FROM contagens_pizzas c
    WHERE c.timestamp BETWEEN inicio_timestamp AND fim_timestamp
    GROUP BY periodo
    ORDER BY periodo;
END;
$$ LANGUAGE plpgsql;

-- Estatísticas de produção
CREATE OR REPLACE FUNCTION get_estatisticas_producao(
    dias_atras INTEGER DEFAULT 7
)
RETURNS TABLE (
    data DATE,
    total_contagens BIGINT,
    media_por_hora NUMERIC,
    pico_hora TIME,
    timestamp_unix BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(c.timestamp) AS data,
        COUNT(*)::BIGINT AS total_contagens,
        ROUND(COUNT(*)::NUMERIC / 24, 2) AS media_por_hora,
        (SELECT c2.timestamp::time 
         FROM contagens_pizzas c2 
         WHERE DATE(c2.timestamp) = DATE(c.timestamp)
         GROUP BY c2.timestamp::time
         ORDER BY COUNT(*) DESC
         LIMIT 1) AS pico_hora,
        EXTRACT(EPOCH FROM DATE(c.timestamp))::BIGINT AS timestamp_unix
    FROM contagens_pizzas c
    WHERE c.timestamp >= CURRENT_DATE - (dias_atras || ' days')::INTERVAL
    GROUP BY DATE(c.timestamp)
    ORDER BY data;
END;
$$ LANGUAGE plpgsql;

-- ======================================================================
-- Seed de configurações padrão
-- ======================================================================

INSERT INTO configuracoes_sistema (chave, valor, descricao) VALUES
('sistema_nome', 'Terelina Pizza Counter', 'Nome do sistema'),
('versao', '1.0.0', 'Versão atual do sistema'),
('timezone', 'America/Sao_Paulo', 'Fuso horário do sistema'),
('retencao_logs_dias', '30', 'Dias para manter logs'),
('intervalo_limpeza_horas', '24', 'Intervalo para limpeza de logs antigos')
ON CONFLICT (chave) DO NOTHING;

-- ======================================================================
-- Triggers e manutenção
-- ======================================================================

-- Atualiza updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: atualiza updated_at em configurações
DROP TRIGGER IF EXISTS update_configuracoes_updated_at ON configuracoes_sistema;
CREATE TRIGGER update_configuracoes_updated_at 
    BEFORE UPDATE ON configuracoes_sistema 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Limpeza de logs antigos
CREATE OR REPLACE FUNCTION limpar_logs_antigos()
RETURNS INTEGER AS $$
DECLARE
    dias_retencao INTEGER;
    registros_removidos INTEGER;
BEGIN
    -- Lê retenção (dias)
    SELECT valor::INTEGER INTO dias_retencao 
    FROM configuracoes_sistema 
    WHERE chave = 'retencao_logs_dias';
    
    IF dias_retencao IS NULL THEN
        dias_retencao := 30; -- padrão
    END IF;
    
    -- Remove logs antigos
    DELETE FROM logs_sistema 
    WHERE timestamp < CURRENT_TIMESTAMP - (dias_retencao || ' days')::INTERVAL;
    
    GET DIAGNOSTICS registros_removidos = ROW_COUNT;
    
    -- Log da limpeza
    INSERT INTO logs_sistema (nivel, mensagem, origem) 
    VALUES ('INFO', 'Limpeza automática: ' || registros_removidos || ' registros removidos', 'sistema');
    
    RETURN registros_removidos;
END;
$$ LANGUAGE plpgsql;

-- Comentários nas entidades
COMMENT ON TABLE contagens_pizzas IS 'Tabela existente: pizzas detectadas (timestamptz, UTC)';
COMMENT ON TABLE logs_sistema IS 'Logs de eventos do sistema para monitoramento';
COMMENT ON TABLE configuracoes_sistema IS 'Configurações do sistema';
COMMENT ON VIEW contagens_por_hora IS 'View para gráficos de contagens por hora no Grafana (UTC-aware)';
COMMENT ON VIEW contagens_por_dia IS 'View para gráficos de contagens por dia no Grafana (UTC-aware)';
COMMENT ON VIEW velocidade_producao IS 'View para análise de velocidade de produção (UTC-aware)';
