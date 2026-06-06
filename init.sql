-- Initialize the database for Rehoboam project with pgvector support

-- Create the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a basic users table (example)
-- Create a basic users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table to store trading history
CREATE TABLE IF NOT EXISTS trading_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(20) NOT NULL,
    amount NUMERIC(30, 18) NOT NULL,
    price NUMERIC(30, 18) NOT NULL,
    side VARCHAR(4) NOT NULL, -- 'buy' or 'sell'
    status VARCHAR(20) NOT NULL, -- 'filled', 'cancelled', 'pending'
    network VARCHAR(50),
    tx_hash VARCHAR(256),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table to store current open positions
CREATE TABLE IF NOT EXISTS trading_positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(20) NOT NULL,
    amount NUMERIC(30, 18) NOT NULL,
    entry_price NUMERIC(30, 18) NOT NULL,
    network VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table to store supported tokens
CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    coingecko_id VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table to store historical price points
CREATE TABLE IF NOT EXISTS price_points (
    id SERIAL PRIMARY KEY,
    token_id INTEGER NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,
    price NUMERIC(30, 18) NOT NULL,
    source VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table to store market sentiment analysis
CREATE TABLE IF NOT EXISTS market_sentiments (
    id SERIAL PRIMARY KEY,
    token_symbol VARCHAR(20) NOT NULL,
    sentiment NUMERIC,
    trend VARCHAR(50),
    volatility VARCHAR(50),
    rsi NUMERIC,
    macd NUMERIC,
    reasoning TEXT,
    source VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_symbol, timestamp)
);

-- Example table with vector column for AI embeddings
-- CREATE TABLE IF NOT EXISTS embeddings (
--     id SERIAL PRIMARY KEY,
--     content TEXT NOT NULL,
--     embedding vector(1536), -- OpenAI embeddings are 1536 dimensions
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- Create index for faster vector similarity searches
-- CREATE INDEX IF NOT EXISTS embeddings_embedding_idx ON embeddings 
-- USING ivfflat (embedding vector_cosine_ops);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE rehoboam TO rehoboam;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rehoboam;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rehoboam;

-- Enable row level security if needed
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- You can add more initialization scripts here
-- This file runs when the PostgreSQL container starts for the first time
