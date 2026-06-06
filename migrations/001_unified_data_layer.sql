-- ═══════════════════════════════════════════════════════════════════════════
-- AKHENATON — The Aten Architecture
-- Unified Data Layer Migration
-- ═══════════════════════════════════════════════════════════════════════════

-- Create pgvector extension if not exists (already in init.sql but safe)
CREATE EXTENSION IF NOT EXISTS vector;

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: market_data
-- Stores price snapshots from Chainlink feeds every 30 seconds
-- The sun that feeds all rays
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS market_data (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,          -- ETH, BTC, LINK, etc.
    pair            VARCHAR(20) NOT NULL,          -- ETH/USD, BTC/USD
    network         VARCHAR(50) NOT NULL DEFAULT 'ethereum',
    price           NUMERIC(32, 18) NOT NULL,
    price_usd       NUMERIC(32, 8) NOT NULL,
    volume_24h      NUMERIC(32, 8),
    high_24h        NUMERIC(32, 18),
    low_24h         NUMERIC(32, 18),
    change_24h      NUMERIC(32, 18),
    change_pct_24h  NUMERIC(10, 4),
    source          VARCHAR(50) NOT NULL DEFAULT 'chainlink', -- chainlink, coingecko_fallback
    feed_address    VARCHAR(66),                    -- Chainlink aggregator address
    round_id        VARCHAR(78),                    -- Chainlink round ID
    decimals        SMALLINT DEFAULT 8,
    reliable        BOOLEAN DEFAULT TRUE,
    freshness_ms    INTEGER,                        -- How stale the data is
    metadata        JSONB,                          -- Extra analytics from the feed
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_pair ON market_data(pair);
CREATE INDEX IF NOT EXISTS idx_market_data_network ON market_data(network);
CREATE INDEX IF NOT EXISTS idx_market_data_created_at ON market_data(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_created ON market_data(symbol, created_at DESC);

-- Partition-friendly: in production, partition by created_at (range, monthly)
-- For now, simple indexing is sufficient

COMMENT ON TABLE market_data IS 'Price snapshots from Chainlink feeds — refreshed every 30s by the Golden Pipeline';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: agent_decisions
-- Logs every AI decision from consciousness, trading agents, and shield
-- The memory of the machine mind
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS agent_decisions (
    id              BIGSERIAL PRIMARY KEY,
    agent_type      VARCHAR(50) NOT NULL,           -- consciousness, trading-agent, shield, hive-mind
    agent_id        VARCHAR(100) NOT NULL,          -- Unique agent identifier
    decision_type   VARCHAR(50) NOT NULL,             -- trade_signal, state_transition, risk_eval, strategy
    symbol          VARCHAR(20),                    -- ETH, BTC, etc.
    action          VARCHAR(20),                    -- BUY, SELL, HOLD, ANALYZE, ALERT
    confidence      NUMERIC(5, 4) DEFAULT 0.5,      -- 0.0 to 1.0
    reasoning       TEXT,                           -- Human-readable reasoning
    raw_input       JSONB,                          -- What the agent saw
    raw_output      JSONB,                          -- What the agent decided
    risk_score      NUMERIC(5, 4),                  -- 0.0 to 1.0
    expected_return NUMERIC(10, 4),                 -- Percentage expected
    execution_status VARCHAR(20) DEFAULT 'pending', -- pending, executed, rejected, expired
    executed_at     TIMESTAMP WITH TIME ZONE,
    tx_hash         VARCHAR(256),
    metadata        JSONB,                          -- Agent-specific extras
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_decisions_agent_type ON agent_decisions(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_agent_id ON agent_decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_symbol ON agent_decisions(symbol);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_created_at ON agent_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_type_created ON agent_decisions(decision_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_status ON agent_decisions(execution_status);

COMMENT ON TABLE agent_decisions IS 'Every AI decision from consciousness, trading agents, and shield evaluation';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: system_events
-- Audit trail for everything that happens across the platform
-- The eternal record
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS system_events (
    id              BIGSERIAL PRIMARY KEY,
    event_type      VARCHAR(50) NOT NULL,           -- mcp_register, db_write, api_call, error, trade
    service         VARCHAR(50) NOT NULL,           -- chainlink-feeds, consciousness, api, frontend
    severity        VARCHAR(20) DEFAULT 'info',     -- debug, info, warning, error, critical
    message         TEXT NOT NULL,
    details         JSONB,                          -- Structured event data
    source_ip       INET,
    user_id         INTEGER,
    trace_id        VARCHAR(100),                   -- Distributed tracing ID
    duration_ms     INTEGER,                        -- How long the operation took
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events(event_type);
CREATE INDEX IF NOT EXISTS idx_system_events_service ON system_events(service);
CREATE INDEX IF NOT EXISTS idx_system_events_severity ON system_events(severity);
CREATE INDEX IF NOT EXISTS idx_system_events_created_at ON system_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_events_trace ON system_events(trace_id);

COMMENT ON TABLE system_events IS 'Audit trail — every heartbeat, every thought, every action';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: mcp_service_registry
-- Central registry of all MCP services and their health
-- The map of the kingdom
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS mcp_service_registry (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,   -- chainlink-feeds, consciousness-layer, etc.
    display_name    VARCHAR(200),
    url             VARCHAR(500),
    port            INTEGER,
    status          VARCHAR(20) DEFAULT 'unknown',  -- healthy, degraded, down, unknown
    last_heartbeat  TIMESTAMP WITH TIME ZONE,
    capabilities    TEXT[],                         -- Array of capability strings
    metadata        JSONB,
    uptime_pct      NUMERIC(5, 4) DEFAULT 100.0,
    version         VARCHAR(20) DEFAULT '1.0.0',
    registered_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mcp_registry_status ON mcp_service_registry(status);
CREATE INDEX IF NOT EXISTS idx_mcp_registry_name ON mcp_service_registry(name);

COMMENT ON TABLE mcp_service_registry IS 'Live registry of all MCP microservices — synced from mcp-registry';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: dashboard_prices_latest
-- Single source of truth for the latest prices
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW dashboard_prices_latest AS
SELECT DISTINCT ON (symbol)
    id,
    symbol,
    pair,
    network,
    price,
    price_usd,
    volume_24h,
    change_24h,
    change_pct_24h,
    source,
    reliable,
    freshness_ms,
    created_at,
    metadata
FROM market_data
ORDER BY symbol, created_at DESC;

COMMENT ON VIEW dashboard_prices_latest IS 'Latest price snapshot per symbol — what the dashboard reads';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: dashboard_agent_activity
-- Recent AI activity for the dashboard
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW dashboard_agent_activity AS
SELECT
    id,
    agent_type,
    agent_id,
    decision_type,
    symbol,
    action,
    confidence,
    reasoning,
    risk_score,
    execution_status,
    created_at,
    executed_at
FROM agent_decisions
ORDER BY created_at DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: dashboard_trades_recent
-- Recent trading activity
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW dashboard_trades_recent AS
SELECT
    th.id,
    th.user_id,
    th.token AS symbol,
    th.amount,
    th.price,
    th.side AS action,
    th.status,
    th.network,
    th.tx_hash,
    th.created_at,
    md.price_usd AS current_price,
    CASE
        WHEN th.side = 'buy' THEN th.amount * (COALESCE(md.price_usd, th.price) - th.price)
        WHEN th.side = 'sell' THEN th.amount * (th.price - COALESCE(md.price_usd, th.price))
        ELSE 0
    END AS unrealized_pnl
FROM trading_history th
LEFT JOIN dashboard_prices_latest md ON th.token = md.symbol
ORDER BY th.created_at DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: dashboard_mcp_status
-- Live MCP service status
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW dashboard_mcp_status AS
SELECT
    name,
    display_name,
    url,
    port,
    status,
    last_heartbeat,
    capabilities,
    uptime_pct,
    version,
    CASE
        WHEN last_heartbeat IS NULL THEN 'never'
        WHEN last_heartbeat < NOW() - INTERVAL '5 minutes' THEN 'stale'
        ELSE 'fresh'
    END AS heartbeat_freshness,
    registered_at,
    updated_at
FROM mcp_service_registry
ORDER BY name;

-- ═══════════════════════════════════════════════════════════════════════════
-- FUNCTION: log_system_event
-- Helper to easily log events from any service
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION log_system_event(
    p_event_type VARCHAR(50),
    p_service VARCHAR(50),
    p_severity VARCHAR(20),
    p_message TEXT,
    p_details JSONB DEFAULT NULL,
    p_user_id INTEGER DEFAULT NULL,
    p_trace_id VARCHAR(100) DEFAULT NULL
) RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_id BIGINT;
BEGIN
    INSERT INTO system_events (event_type, service, severity, message, details, user_id, trace_id)
    VALUES (p_event_type, p_service, p_severity, p_message, p_details, p_user_id, p_trace_id)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$;

-- ═══════════════════════════════════════════════════════════════════════════
-- FUNCTION: update_mcp_heartbeat
-- Called by MCP services to update their heartbeat
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_mcp_heartbeat(
    p_name VARCHAR(100),
    p_status VARCHAR(20),
    p_metadata JSONB DEFAULT NULL
) RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE mcp_service_registry
    SET status = p_status,
        last_heartbeat = CURRENT_TIMESTAMP,
        metadata = COALESCE(p_metadata, metadata),
        updated_at = CURRENT_TIMESTAMP
    WHERE name = p_name;

    IF NOT FOUND THEN
        INSERT INTO mcp_service_registry (name, status, metadata)
        VALUES (p_name, p_status, p_metadata);
    END IF;
END;
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rehoboam;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rehoboam;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO rehoboam;
GRANT SELECT ON dashboard_prices_latest TO rehoboam;
GRANT SELECT ON dashboard_agent_activity TO rehoboam;
GRANT SELECT ON dashboard_trades_recent TO rehoboam;
GRANT SELECT ON dashboard_mcp_status TO rehoboam;
