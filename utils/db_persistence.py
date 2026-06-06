#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  AKHENATON — The Aten Architecture                                            ║
║  Unified Database Persistence Layer                                            ║
║                                                                                ║
║  Every MCP service writes its outputs here. Every API endpoint reads from    ║
║  here. The frontend never calls external APIs directly.                      ║
║                                                                                ║
║  One Sun. Many Rays.                                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict

import asyncpg
import psycopg2
import psycopg2.extras
import psycopg2.pool
from urllib.parse import urlparse

logger = logging.getLogger("db_persistence")

# ── Configuration ────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rehoboam:rehoboam123@postgres:5432/rehoboam"
)

def _parse_db_url(url: str) -> Dict[str, Any]:
    """Parse database URL into connection parameters."""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") or "rehoboam",
        "user": parsed.username or "rehoboam",
        "password": parsed.password or "rehoboam123",
    }

# ── Sync Connection Pool (for background workers) ────────────────────────────
_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

def get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    """Get or create a threaded connection pool."""
    global _pool
    if _pool is None or _pool.closed:
        cfg = _parse_db_url(DATABASE_URL)
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            **cfg
        )
        logger.info("Vetala: DB persistence pool created")
    return _pool

# ── Async Connection Pool (for FastAPI endpoints) ────────────────────────────
_async_pool: Optional[asyncpg.Pool] = None

async def get_async_pool() -> asyncpg.Pool:
    """Get or create an async connection pool."""
    global _async_pool
    if _async_pool is None or _async_pool._closed:
        cfg = _parse_db_url(DATABASE_URL)
        _async_pool = await asyncpg.create_pool(
            host=cfg["host"],
            port=cfg["port"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            min_size=2,
            max_size=20,
            command_timeout=30,
        )
        logger.info("Vetala: Async DB persistence pool created")
    return _async_pool


@asynccontextmanager
async def async_db():
    """Async context manager for database connections."""
    pool = await get_async_pool()
    async with pool.acquire() as conn:
        yield conn


def db_conn():
    """Get a connection from the sync pool. Caller must close()."""
    return get_pool().getconn()


def release_conn(conn):
    """Release a connection back to the pool."""
    get_pool().putconn(conn)


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET DATA
# ═══════════════════════════════════════════════════════════════════════════════

async def save_market_snapshot(
    symbol: str,
    pair: str,
    price: float,
    price_usd: float,
    network: str = "ethereum",
    volume_24h: Optional[float] = None,
    high_24h: Optional[float] = None,
    low_24h: Optional[float] = None,
    change_24h: Optional[float] = None,
    change_pct_24h: Optional[float] = None,
    source: str = "chainlink",
    feed_address: Optional[str] = None,
    round_id: Optional[str] = None,
    decimals: int = 8,
    reliable: bool = True,
    freshness_ms: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Save a price snapshot from Chainlink or any other price source.
    Called by: mcp-chainlink-feeds, price monitoring cron.
    """
    async with async_db() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO market_data (
                symbol, pair, network, price, price_usd, volume_24h,
                high_24h, low_24h, change_24h, change_pct_24h,
                source, feed_address, round_id, decimals, reliable,
                freshness_ms, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            RETURNING id
            """,
            symbol, pair, network, price, price_usd, volume_24h,
            high_24h, low_24h, change_24h, change_pct_24h,
            source, feed_address, round_id, decimals, reliable,
            freshness_ms, json.dumps(metadata) if metadata else None,
        )
        return row["id"]


def save_market_snapshot_sync(
    symbol: str,
    pair: str,
    price: float,
    price_usd: float,
    network: str = "ethereum",
    **kwargs
) -> int:
    """Synchronous version for use in background threads."""
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO market_data (
                    symbol, pair, network, price, price_usd, volume_24h,
                    high_24h, low_24h, change_24h, change_pct_24h,
                    source, feed_address, round_id, decimals, reliable,
                    freshness_ms, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    symbol, pair, network, price, price_usd,
                    kwargs.get("volume_24h"),
                    kwargs.get("high_24h"),
                    kwargs.get("low_24h"),
                    kwargs.get("change_24h"),
                    kwargs.get("change_pct_24h"),
                    kwargs.get("source", "chainlink"),
                    kwargs.get("feed_address"),
                    kwargs.get("round_id"),
                    kwargs.get("decimals", 8),
                    kwargs.get("reliable", True),
                    kwargs.get("freshness_ms"),
                    json.dumps(kwargs.get("metadata")) if kwargs.get("metadata") else None,
                ),
            )
            result = cur.fetchone()[0]
            conn.commit()
            return result
    finally:
        release_conn(conn)


async def get_latest_prices(symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Get latest prices from our DB (not CoinGecko)."""
    async with async_db() as conn:
        if symbols:
            rows = await conn.fetch(
                "SELECT * FROM dashboard_prices_latest WHERE symbol = ANY($1)",
                symbols,
            )
        else:
            rows = await conn.fetch("SELECT * FROM dashboard_prices_latest")
        return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT DECISIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def log_agent_decision(
    agent_type: str,
    agent_id: str,
    decision_type: str,
    symbol: Optional[str] = None,
    action: Optional[str] = None,
    confidence: float = 0.5,
    reasoning: Optional[str] = None,
    raw_input: Optional[Dict[str, Any]] = None,
    raw_output: Optional[Dict[str, Any]] = None,
    risk_score: Optional[float] = None,
    expected_return: Optional[float] = None,
    execution_status: str = "pending",
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Log every AI decision to the database.
    Called by: consciousness-layer, trading-agents, shield evaluation.
    """
    async with async_db() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO agent_decisions (
                agent_type, agent_id, decision_type, symbol, action,
                confidence, reasoning, raw_input, raw_output,
                risk_score, expected_return, execution_status, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
            """,
            agent_type, agent_id, decision_type, symbol, action,
            confidence, reasoning,
            json.dumps(raw_input) if raw_input else None,
            json.dumps(raw_output) if raw_output else None,
            risk_score, expected_return, execution_status,
            json.dumps(metadata) if metadata else None,
        )
        logger.info(f"Agent decision logged: {agent_type}/{agent_id} → {decision_type}")
        return row["id"]


def log_agent_decision_sync(
    agent_type: str,
    agent_id: str,
    decision_type: str,
    **kwargs
) -> int:
    """Synchronous version for background workers."""
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_decisions (
                    agent_type, agent_id, decision_type, symbol, action,
                    confidence, reasoning, raw_input, raw_output,
                    risk_score, expected_return, execution_status, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    agent_type, agent_id, decision_type,
                    kwargs.get("symbol"),
                    kwargs.get("action"),
                    kwargs.get("confidence", 0.5),
                    kwargs.get("reasoning"),
                    json.dumps(kwargs.get("raw_input")) if kwargs.get("raw_input") else None,
                    json.dumps(kwargs.get("raw_output")) if kwargs.get("raw_output") else None,
                    kwargs.get("risk_score"),
                    kwargs.get("expected_return"),
                    kwargs.get("execution_status", "pending"),
                    json.dumps(kwargs.get("metadata")) if kwargs.get("metadata") else None,
                ),
            )
            result = cur.fetchone()[0]
            conn.commit()
            return result
    finally:
        release_conn(conn)


async def get_recent_agent_activity(
    limit: int = 50,
    agent_type: Optional[str] = None,
    symbol: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get recent AI agent activity for the dashboard."""
    async with async_db() as conn:
        conditions = []
        params = []
        if agent_type:
            conditions.append("agent_type = $" + str(len(params) + 1))
            params.append(agent_type)
        if symbol:
            conditions.append("symbol = $" + str(len(params) + 1))
            params.append(symbol)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT * FROM dashboard_agent_activity
            {where_clause}
            LIMIT {limit}
        """
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def log_event(
    event_type: str,
    service: str,
    message: str,
    severity: str = "info",
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    trace_id: Optional[str] = None,
) -> int:
    """Log a system event."""
    async with async_db() as conn:
        row = await conn.fetchrow(
            "SELECT log_system_event($1, $2, $3, $4, $5, $6, $7)",
            event_type, service, severity, message,
            json.dumps(details) if details else None,
            user_id, trace_id,
        )
        return row[0]


def log_event_sync(
    event_type: str,
    service: str,
    message: str,
    severity: str = "info",
    **kwargs
) -> int:
    """Synchronous version."""
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT log_system_event(%s, %s, %s, %s, %s, %s, %s)",
                (
                    event_type, service, severity, message,
                    json.dumps(kwargs.get("details")) if kwargs.get("details") else None,
                    kwargs.get("user_id"),
                    kwargs.get("trace_id"),
                ),
            )
            result = cur.fetchone()[0]
            conn.commit()
            return result
    finally:
        release_conn(conn)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP SERVICE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

async def update_mcp_heartbeat(
    name: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Update MCP service heartbeat in the database."""
    async with async_db() as conn:
        await conn.execute(
            "SELECT update_mcp_heartbeat($1, $2, $3)",
            name, status, json.dumps(metadata) if metadata else None,
        )


def update_mcp_heartbeat_sync(
    name: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Synchronous version."""
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT update_mcp_heartbeat(%s, %s, %s)",
                (name, status, json.dumps(metadata) if metadata else None),
            )
            conn.commit()
    finally:
        release_conn(conn)


async def get_mcp_services_status() -> List[Dict[str, Any]]:
    """Get all MCP service statuses for the dashboard."""
    async with async_db() as conn:
        rows = await conn.fetch("SELECT * FROM dashboard_mcp_status")
        return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# TRADING DATA (wrappers for existing tables)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_recent_trades(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent trading history with current price context."""
    async with async_db() as conn:
        rows = await conn.fetch(
            "SELECT * FROM dashboard_trades_recent LIMIT $1", limit
        )
        return [dict(r) for r in rows]


async def get_user_portfolio(user_id: int) -> Dict[str, Any]:
    """Get user portfolio with current prices."""
    async with async_db() as conn:
        # Get positions
        positions = await conn.fetch(
            """
            SELECT
                tp.token AS symbol,
                tp.amount,
                tp.entry_price,
                tp.network,
                tp.created_at,
                md.price_usd AS current_price,
                (tp.amount * md.price_usd) AS value_usd,
                (tp.amount * (md.price_usd - tp.entry_price)) AS unrealized_pnl,
                CASE WHEN tp.entry_price > 0
                    THEN ((md.price_usd - tp.entry_price) / tp.entry_price * 100)
                    ELSE 0
                END AS pnl_percent
            FROM trading_positions tp
            LEFT JOIN dashboard_prices_latest md ON tp.token = md.symbol
            WHERE tp.user_id = $1
            ORDER BY value_usd DESC NULLS LAST
            """,
            user_id,
        )

        # Calculate totals
        total_value = sum(p["value_usd"] or 0 for p in positions)
        total_pnl = sum(p["unrealized_pnl"] or 0 for p in positions)

        return {
            "user_id": user_id,
            "total_value_usd": round(total_value, 2),
            "total_unrealized_pnl": round(total_pnl, 2),
            "positions": [dict(p) for p in positions],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

async def health_check() -> Dict[str, Any]:
    """Check database connectivity and return stats."""
    try:
        async with async_db() as conn:
            # Table counts
            tables = ["market_data", "agent_decisions", "system_events", "trading_history", "trading_positions"]
            counts = {}
            for table in tables:
                row = await conn.fetchrow(
                    f"SELECT COUNT(*) FROM {table}"
                )
                counts[table] = row[0]

            # Latest market data timestamp
            latest = await conn.fetchrow(
                "SELECT MAX(created_at) as latest FROM market_data"
            )

            # Agent activity count (last hour)
            agent_count = await conn.fetchrow(
                "SELECT COUNT(*) FROM agent_decisions WHERE created_at > NOW() - INTERVAL '1 hour'"
            )

            return {
                "status": "healthy",
                "table_counts": counts,
                "latest_market_data": latest["latest"].isoformat() if latest["latest"] else None,
                "agent_decisions_last_hour": agent_count[0],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
