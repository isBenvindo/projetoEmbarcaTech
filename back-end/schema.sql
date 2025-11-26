-- Terelina Database Schema (UTC-aware)

-- ======================================================================
-- Tables
-- ======================================================================

-- Main table for product counts
CREATE TABLE IF NOT EXISTS pizza_counts (
    id SERIAL PRIMARY KEY,
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- System logs for monitoring and debugging
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL, -- INFO|WARNING|ERROR
    message TEXT NOT NULL,
    source VARCHAR(50) NOT NULL, -- backend|mqtt|sensor
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT system_logs_level_chk CHECK (level IN ('INFO','WARNING','ERROR'))
);

-- Dynamic system settings
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ======================================================================
-- Indexes (Performance Improvements)
-- ======================================================================

-- Speed up time-based queries and ordering
CREATE INDEX IF NOT EXISTS idx_pizza_counts_timestamp ON pizza_counts ("timestamp" DESC);

-- Speed up log filtering and ordering
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs ("timestamp" DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs (level);

-- ======================================================================
-- Views (Optimized for Grafana)
-- ======================================================================

-- Compatibility view (maps 'timestamp' to 'timestampz')
CREATE OR REPLACE VIEW pizza_counts_utc AS
SELECT
  id,
  "timestamp" AS timestampz
FROM pizza_counts;

-- Counts aggregated by hour
CREATE OR REPLACE VIEW hourly_counts AS
SELECT 
    DATE_TRUNC('hour', "timestamp") AS hour,
    COUNT(*) AS total_counts,
    EXTRACT(EPOCH FROM DATE_TRUNC('hour', "timestamp")) AS timestamp_unix
FROM pizza_counts
GROUP BY DATE_TRUNC('hour', "timestamp")
ORDER BY hour;

-- Counts aggregated by day
CREATE OR REPLACE VIEW daily_counts AS
SELECT 
    DATE("timestamp") AS date,
    COUNT(*) AS total_counts,
    EXTRACT(EPOCH FROM DATE("timestamp")) AS timestamp_unix
FROM pizza_counts
GROUP BY DATE("timestamp")
ORDER BY date;

-- Statistics for the current day
CREATE OR REPLACE VIEW today_stats AS
SELECT 
    COUNT(*) AS total_counts,
    MIN("timestamp"::time) AS first_count_time,
    MAX("timestamp"::time) AS last_count_time,
    DATE("timestamp") AS date,
    EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) AS timestamp_unix
FROM pizza_counts
WHERE DATE("timestamp") = CURRENT_DATE
GROUP BY DATE("timestamp");

-- Recent counts (last 24h)
CREATE OR REPLACE VIEW recent_counts_24h AS
SELECT 
    id,
    "timestamp",
    EXTRACT(EPOCH FROM "timestamp") AS timestamp_unix,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - "timestamp"))::INTEGER AS seconds_ago
FROM pizza_counts
WHERE "timestamp" >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY "timestamp" DESC;

-- Production speed (pizzas per hour)
CREATE OR REPLACE VIEW production_speed AS
SELECT 
    DATE_TRUNC('hour', "timestamp") AS hour,
    COUNT(*) AS pizzas_per_hour,
    EXTRACT(EPOCH FROM DATE_TRUNC('hour', "timestamp")) AS timestamp_unix,
    ROUND(COUNT(*)::NUMERIC / 1, 2) AS pizzas_per_hour_decimal
FROM pizza_counts
WHERE "timestamp" >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', "timestamp")
ORDER BY hour;

-- ======================================================================
-- Default Settings Seed
-- ======================================================================

INSERT INTO system_settings (key, value, description) VALUES
('system_name', 'Terelina Pizza Counter', 'System Display Name'),
('version', '1.0.0', 'Current System Version'),
('timezone', 'America/Sao_Paulo', 'System Timezone'),
('log_retention_days', '30', 'Days to keep logs'),
('cleanup_interval_hours', '24', 'Interval for automatic cleanup')
ON CONFLICT (key) DO NOTHING;

-- ======================================================================
-- Functions & Triggers
-- ======================================================================

-- Auto-update 'updated_at' column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Cleanup old logs
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS INTEGER AS $$
DECLARE
    retention_days INTEGER;
    deleted_count INTEGER;
BEGIN
    -- Get retention period
    SELECT value::INTEGER INTO retention_days
    FROM system_settings
    WHERE key = 'log_retention_days';

    IF retention_days IS NULL THEN
        retention_days := 30; -- default
    END IF;

    DELETE FROM system_logs
    WHERE "timestamp" < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    INSERT INTO system_logs (level, message, source)
    VALUES ('INFO', 'Auto cleanup: ' || deleted_count || ' logs removed', 'system');

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;