-- ═══════════════════════════════════════════════════════════════════════════
-- AKHENATON — The Aten Architecture
-- Seed Data: trading_history and trading_positions
-- Realistic simulated data to bring the dashboard alive
-- ═══════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════
-- SEED: users (if empty, create a demo user)
-- ═══════════════════════════════════════════════════════════════════════════
INSERT INTO users (id, username, hashed_password, created_at)
SELECT 1, 'demo_user', '$2b$12$demo_hash_for_demo_user_only', NOW()
WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = 1);

-- ═══════════════════════════════════════════════════════════════════════════
-- SEED: trading_history — realistic simulated trades over last 30 days
-- ═══════════════════════════════════════════════════════════════════════════

-- We'll generate trades using a simple procedural approach since we need realism
-- Using generate_series and deterministic random seeded by position

DO $$
DECLARE
    v_user_id INTEGER;
    v_tokens TEXT[] := ARRAY['ETH', 'BTC', 'LINK', 'AAVE', 'UNI', 'MATIC', 'ARB', 'AVAX'];
    v_networks TEXT[] := ARRAY['ethereum', 'arbitrum', 'polygon'];
    v_sides TEXT[] := ARRAY['buy', 'sell'];
    v_statuses TEXT[] := ARRAY['filled', 'filled', 'filled', 'filled', 'filled', 'cancelled', 'pending'];
    v_base_prices NUMERIC[] := ARRAY[3200.0, 64000.0, 14.5, 95.0, 7.2, 0.65, 1.15, 35.0];
    v_token TEXT;
    v_network TEXT;
    v_side TEXT;
    v_status TEXT;
    v_price NUMERIC;
    v_amount NUMERIC;
    v_tx_hash TEXT;
    v_created_at TIMESTAMP WITH TIME ZONE;
    i INTEGER;
    j INTEGER;
    v_token_idx INTEGER;
BEGIN
    -- Get or create demo user
    SELECT id INTO v_user_id FROM users WHERE username = 'demo_user' LIMIT 1;

    IF v_user_id IS NULL THEN
        INSERT INTO users (username, hashed_password)
        VALUES ('demo_user', '$2b$12$demo')
        RETURNING id INTO v_user_id;
    END IF;

    -- Clear old seed data if re-running
    DELETE FROM trading_history WHERE user_id = v_user_id AND tx_hash LIKE '0xseed%';

    -- Generate 200 trades over the last 30 days
    FOR i IN 1..200 LOOP
        v_token_idx := 1 + (i % array_length(v_tokens, 1));
        v_token := v_tokens[v_token_idx];
        v_network := v_networks[1 + (i % array_length(v_networks, 1))];
        v_side := v_sides[1 + (i % 2)];
        v_status := v_statuses[1 + (i % array_length(v_statuses, 1))];

        -- Price varies by ±15% from base
        v_price := v_base_prices[v_token_idx] * (0.85 + (random() * 0.30));
        v_price := round(v_price, 18);

        -- Amount varies
        v_amount := CASE v_token
            WHEN 'BTC' THEN 0.01 + random() * 0.5
            WHEN 'ETH' THEN 0.1 + random() * 5.0
            ELSE 10.0 + random() * 500.0
        END;
        v_amount := round(v_amount, 18);

        -- Timestamp distributed over last 30 days
        v_created_at := NOW() - (random() * INTERVAL '30 days');

        -- Generate fake tx hash
        v_tx_hash := '0xseed' || md5(v_token || v_created_at::text || i::text);

        INSERT INTO trading_history (
            user_id, token, amount, price, side, status,
            network, tx_hash, created_at
        ) VALUES (
            v_user_id, v_token, v_amount, v_price, v_side, v_status,
            v_network, v_tx_hash, v_created_at
        );
    END LOOP;

    -- ═══════════════════════════════════════════════════════════════════════════
    -- SEED: trading_positions — current open positions
    -- ═══════════════════════════════════════════════════════════════════════════

    -- Clear old seed positions
    DELETE FROM trading_positions WHERE user_id = v_user_id AND network LIKE 'seed_%';

    FOR j IN 1..array_length(v_tokens, 1) LOOP
        v_token := v_tokens[j];
        v_network := v_networks[1 + (j % array_length(v_networks, 1))];

        -- Only create positions for ~60% of tokens
        IF random() < 0.6 THEN
            v_price := v_base_prices[j] * (0.90 + random() * 0.20);
            v_price := round(v_price, 18);

            v_amount := CASE v_token
                WHEN 'BTC' THEN 0.05 + random() * 0.2
                WHEN 'ETH' THEN 0.5 + random() * 3.0
                ELSE 50.0 + random() * 300.0
            END;
            v_amount := round(v_amount, 18);

            INSERT INTO trading_positions (
                user_id, token, amount, entry_price, network, created_at
            ) VALUES (
                v_user_id, v_token, v_amount, v_price,
                v_network, NOW() - (random() * INTERVAL '14 days')
            );
        END IF;
    END LOOP;

    -- Log the seeding event
    PERFORM log_system_event('seed', 'migration', 'info',
        'Seeded trading_history with 200 trades and trading_positions with sample positions',
        jsonb_build_object('trades_count', 200, 'user_id', v_user_id),
        v_user_id,
        'seed-' || extract(epoch from now())::text
    );

END $$;

-- ═══════════════════════════════════════════════════════════════════════════
-- SEED: mcp_service_registry — register all known services
-- ═══════════════════════════════════════════════════════════════════════════

INSERT INTO mcp_service_registry (name, display_name, url, port, status, capabilities, version)
VALUES
    ('chainlink-feeds', 'Chainlink Price Feeds', 'http://mcp-chainlink-feeds:3000', 3102, 'unknown',
     ARRAY['get_latest_price', 'get_multiple_prices', 'get_historical_data', 'detect_arbitrage'], '1.0.0'),
    ('consciousness-layer', 'AI Consciousness Layer', 'http://mcp-consciousness-layer:3000', 3600, 'unknown',
     ARRAY['analyze_market', 'emotional_state', 'consciousness_report'], '1.0.0'),
    ('trading-agents', 'Multi-Agent Trading', 'http://mcp-trading-agents:3000', 3700, 'unknown',
     ARRAY['trade_signal', 'risk_assessment', 'portfolio_optimization'], '1.0.0'),
    ('etherscan-analyzer', 'On-Chain Analytics', 'http://mcp-etherscan-analyzer:3000', 3101, 'unknown',
     ARRAY['get_transactions', 'analyze_wallet', 'detect_patterns'], '1.0.0'),
    ('function-gemma', 'Function Calling LLM', 'http://mcp-function-gemma:3000', 3111, 'unknown',
     ARRAY['function_call', 'code_generation', 'analysis'], '1.0.0'),
    ('crypto-tracker', 'Crypto Price Tracker', 'http://mcp-crypto-tracker:3000', 3100, 'unknown',
     ARRAY['get_prices', 'get_trends', 'get_market_data'], '1.0.0'),
    ('defi-analyzer', 'DeFi Protocol Analyzer', 'http://mcp-defi-analyzer:3000', 3101, 'unknown',
     ARRAY['analyze_protocol', 'get_tvl', 'get_apr'], '1.0.0'),
    ('hive-mind-layer', 'Hive Mind Collective', 'http://mcp-hive-mind-layer:3000', 3800, 'unknown',
     ARRAY['collective_intelligence', 'consensus', 'swarm_analysis'], '1.0.0'),
    ('vetal-foundry-forge', 'Vetala Foundry Forge', 'http://mcp-vetal-foundry-forge:3000', 3900, 'unknown',
     ARRAY['contract_deploy', 'security_audit', 'gas_optimization'], '1.0.0')
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    url = EXCLUDED.url,
    port = EXCLUDED.port,
    capabilities = EXCLUDED.capabilities,
    version = EXCLUDED.version,
    updated_at = CURRENT_TIMESTAMP;

-- Log completion
SELECT log_system_event('migration', 'akhenaton', 'info',
    'Unified data layer migration completed — market_data, agent_decisions, system_events, mcp_service_registry',
    jsonb_build_object('migration', '002_seed_trading_data', 'timestamp', NOW())
);
