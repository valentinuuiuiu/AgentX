"""Database seeding utilities for Rehoboam trading platform.

Generates realistic trading data for development and testing.
"""
import asyncio
import json
import random
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Realistic token universe
TOKENS = [
    {"symbol": "ETH", "name": "Ethereum", "coingecko_id": "ethereum", "base_price": 3200.0, "volatility": 0.025},
    {"symbol": "BTC", "name": "Bitcoin", "coingecko_id": "bitcoin", "base_price": 87000.0, "volatility": 0.018},
    {"symbol": "LINK", "name": "Chainlink", "coingecko_id": "chainlink", "base_price": 14.5, "volatility": 0.035},
    {"symbol": "USDC", "name": "USD Coin", "coingecko_id": "usd-coin", "base_price": 1.0, "volatility": 0.002},
    {"symbol": "ARB", "name": "Arbitrum", "coingecko_id": "arbitrum", "base_price": 0.85, "volatility": 0.04},
    {"symbol": "OP", "name": "Optimism", "coingecko_id": "optimism", "base_price": 1.45, "volatility": 0.038},
    {"symbol": "MATIC", "name": "Polygon", "coingecko_id": "matic-network", "base_price": 0.42, "volatility": 0.032},
    {"symbol": "UNI", "name": "Uniswap", "coingecko_id": "uniswap", "base_price": 7.8, "volatility": 0.03},
    {"symbol": "AAVE", "name": "Aave", "coingecko_id": "aave", "base_price": 165.0, "volatility": 0.028},
    {"symbol": "SNX", "name": "Synthetix", "coingecko_id": "havven", "base_price": 2.1, "volatility": 0.045},
]

NETWORKS = ["ethereum", "arbitrum", "optimism", "polygon", "base"]

STRATEGY_NAMES = [
    "Momentum Breakout",
    "Mean Reversion",
    "Grid Accumulation",
    "Flash Arbitrage",
    "Dollar Cost Averaging",
    "Swing Trade",
    "Breakout Hunter",
    "Liquidity Snipe",
]


def _random_walk_price(base: float, volatility: float, steps: int = 1) -> float:
    """Generate a realistic price via geometric Brownian motion."""
    price = base
    for _ in range(steps):
        change = random.gauss(0, volatility)
        price *= (1 + change)
    return max(price, 0.0001)


def generate_tokens() -> List[Dict[str, Any]]:
    """Generate token seed records."""
    now = datetime.now(timezone.utc)
    records = []
    for t in TOKENS:
        records.append({
            "id": str(uuid.uuid4()),
            "symbol": t["symbol"],
            "name": t["name"],
            "decimals": 18,
            "contractAddr": None,
            "coingeckoId": t["coingecko_id"],
            "isActive": True,
            "createdAt": now,
        })
    return records


def generate_price_points(
    token_id: str,
    token_symbol: str,
    base_price: float,
    volatility: float,
    count: int = 144,  # 24h at 10-min intervals
) -> List[Dict[str, Any]]:
    """Generate historical price points for a token."""
    now = datetime.now(timezone.utc)
    records = []
    price = base_price
    for i in range(count):
        ts = now - timedelta(minutes=10 * (count - i))
        price = _random_walk_price(price, volatility / 3)  # intra-candle vol
        high = price * (1 + abs(random.gauss(0, volatility / 2)))
        low = price * (1 - abs(random.gauss(0, volatility / 2)))
        change_24h = random.gauss(0, volatility * 2)
        volume = random.uniform(1_000_000, 50_000_000)
        records.append({
            "id": str(uuid.uuid4()),
            "tokenId": token_id,
            "source": "coingecko",
            "price": Decimal(str(price)),
            "volume": Decimal(str(volume)),
            "high24h": Decimal(str(high)),
            "low24h": Decimal(str(low)),
            "change24h": Decimal(str(change_24h)),
            "signal": random.choice(["buy", "sell", "neutral", None]),
            "confidence": Decimal(str(random.uniform(0.5, 0.95))),
            "timestamp": ts,
        })
    return records


def generate_trades(
    user_id: str,
    wallet_id: str,
    token_map: Dict[str, str],  # symbol -> token_id
    count: int = 50,
) -> List[Dict[str, Any]]:
    """Generate realistic trade history for a user."""
    now = datetime.now(timezone.utc)
    records = []
    for i in range(count):
        token = random.choice(TOKENS)
        token_id = token_map[token["symbol"]]
        side = random.choice(["buy", "sell"])
        network = random.choice(NETWORKS)
        # Amount scales with token price
        if token["symbol"] in ("BTC", "ETH"):
            amount = random.uniform(0.01, 2.0)
        else:
            amount = random.uniform(10, 5000)
        price = _random_walk_price(token["base_price"], token["volatility"])
        gas_fee = Decimal(str(random.uniform(0.0001, 0.05)))
        gas_fee_usd = Decimal(str(float(gas_fee) * 3200))
        status = random.choices(
            ["filled", "pending", "failed", "cancelled"],
            weights=[70, 10, 5, 5],
            k=1,
        )[0]
        ts = now - timedelta(hours=random.uniform(0, 720))  # up to 30 days back
        records.append({
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "walletId": wallet_id,
            "strategyId": None,
            "tokenId": token_id,
            "action": side,
            "amount": Decimal(str(amount)),
            "price": Decimal(str(price)),
            "priceUsd": Decimal(str(price)),
            "network": network,
            "slippage": Decimal(str(random.uniform(0.001, 0.05))),
            "gasFee": gas_fee,
            "gasFeeUsd": gas_fee_usd,
            "status": status,
            "txHash": f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:24]}" if status == "filled" else None,
            "errorMessage": None,
            "executedAt": ts if status == "filled" else None,
            "createdAt": ts,
            "updatedAt": ts,
        })
    records.sort(key=lambda x: x["createdAt"])
    return records


def generate_positions(
    portfolio_id: str,
    token_map: Dict[str, str],
    count: int = 6,
) -> List[Dict[str, Any]]:
    """Generate open positions for a portfolio."""
    now = datetime.now(timezone.utc)
    records = []
    selected = random.sample(TOKENS, min(count, len(TOKENS)))
    for token in selected:
        token_id = token_map[token["symbol"]]
        amount = random.uniform(50, 2000) if token["symbol"] not in ("BTC", "ETH") else random.uniform(0.1, 5)
        avg_buy = _random_walk_price(token["base_price"] * 0.95, token["volatility"])
        current = _random_walk_price(token["base_price"], token["volatility"])
        value_usd = Decimal(str(amount * current))
        unrealized = Decimal(str(amount * (current - avg_buy)))
        records.append({
            "id": str(uuid.uuid4()),
            "portfolioId": portfolio_id,
            "tokenSymbol": token["symbol"],
            "amount": Decimal(str(amount)),
            "avgBuyPrice": Decimal(str(avg_buy)),
            "currentPrice": Decimal(str(current)),
            "valueUsd": value_usd,
            "unrealizedPnL": unrealized,
            "network": random.choice(NETWORKS),
            "createdAt": now - timedelta(days=random.uniform(1, 30)),
            "updatedAt": now,
        })
    return records


def generate_strategies(user_id: str, count: int = 4) -> List[Dict[str, Any]]:
    """Generate strategy records."""
    now = datetime.now(timezone.utc)
    records = []
    for i in range(count):
        risk = random.choice(["low", "moderate", "high", "aggressive"])
        records.append({
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "name": random.choice(STRATEGY_NAMES),
            "description": f"Auto-generated strategy #{i+1} for {risk} risk profile.",
            "riskLevel": risk,
            "confidence": Decimal(str(random.uniform(0.55, 0.92))),
            "expectedReturn": Decimal(str(random.uniform(0.05, 0.45))),
            "timeframe": random.choice(["1h", "4h", "1d", "1w"]),
            "networks": random.sample(NETWORKS, k=random.randint(1, 3)),
            "parameters": {},
            "isActive": True,
            "executions": random.randint(0, 50),
            "successRate": Decimal(str(random.uniform(0.4, 0.85))),
            "reasoning": None,
            "createdAt": now,
            "updatedAt": now,
        })
    return records


async def seed_database(pool, user_id: Optional[str] = None, wallet_id: Optional[str] = None, portfolio_id: Optional[str] = None):
    """Seed the database with realistic trading data.

    Creates tokens, price points, trades, positions, and strategies.
    Requires existing user/wallet/portfolio or generates placeholders.
    """
    from asyncpg import Pool
    if pool is None:
        logger.error("Database pool is None, cannot seed.")
        return {"status": "error", "detail": "No DB pool"}

    now = datetime.now(timezone.utc)
    user_id = user_id or f"user_{uuid.uuid4().hex[:8]}"
    wallet_id = wallet_id or f"wallet_{uuid.uuid4().hex[:8]}"
    portfolio_id = portfolio_id or f"portfolio_{uuid.uuid4().hex[:8]}"

    # 1. Insert tokens
    tokens = generate_tokens()
    token_map = {t["symbol"]: t["id"] for t in tokens}
    token_symbols = {t["id"]: t for t in tokens}

    async with pool.acquire() as conn:
        # Upsert tokens
        for t in tokens:
            await conn.execute(
                """
                INSERT INTO tokens (id, symbol, name, decimals, "contractAddr", "coingeckoId", "isActive", "createdAt")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (symbol) DO UPDATE SET
                    name = EXCLUDED.name,
                    "coingeckoId" = EXCLUDED."coingeckoId",
                    "isActive" = EXCLUDED."isActive"
                """,
                t["id"], t["symbol"], t["name"], t["decimals"],
                t["contractAddr"], t["coingeckoId"], t["isActive"], t["createdAt"],
            )

        # 2. Insert price points
        price_records = []
        for t in tokens:
            price_records.extend(generate_price_points(t["id"], t["symbol"], t["base_price"], t["volatility"]))
        # Batch insert price points
        if price_records:
            await conn.copy_records_to_table(
                "price_points",
                records=[(
                    r["id"], r["tokenId"], r["source"], r["price"], r["volume"],
                    r["high24h"], r["low24h"], r["change24h"], r["signal"],
                    r["confidence"], r["timestamp"],
                ) for r in price_records],
                columns=["id", "tokenId", "source", "price", "volume", "high24h", "low24h", "change24h", "signal", "confidence", "timestamp"],
            )

        # 3. Insert trades
        trades = generate_trades(user_id, wallet_id, token_map, count=50)
        if trades:
            await conn.copy_records_to_table(
                "trades",
                records=[(
                    r["id"], r["userId"], r["walletId"], r["strategyId"], r["tokenId"],
                    r["action"], r["amount"], r["price"], r["priceUsd"], r["network"],
                    r["slippage"], r["gasFee"], r["gasFeeUsd"], r["status"], r["txHash"],
                    r["errorMessage"], r["executedAt"], r["createdAt"], r["updatedAt"],
                ) for r in trades],
                columns=[
                    "id", "userId", "walletId", "strategyId", "tokenId", "action", "amount",
                    "price", "priceUsd", "network", "slippage", "gasFee", "gasFeeUsd",
                    "status", "txHash", "errorMessage", "executedAt", "createdAt", "updatedAt",
                ],
            )

        # 4. Insert positions
        positions = generate_positions(portfolio_id, token_map, count=6)
        if positions:
            await conn.copy_records_to_table(
                "positions",
                records=[(
                    r["id"], r["portfolioId"], r["tokenSymbol"], r["amount"],
                    r["avgBuyPrice"], r["currentPrice"], r["valueUsd"], r["unrealizedPnL"],
                    r["network"], r["createdAt"], r["updatedAt"],
                ) for r in positions],
                columns=[
                    "id", "portfolioId", "tokenSymbol", "amount", "avgBuyPrice",
                    "currentPrice", "valueUsd", "unrealizedPnL", "network", "createdAt", "updatedAt",
                ],
            )

        # 5. Insert strategies
        strategies = generate_strategies(user_id, count=4)
        if strategies:
            await conn.executemany(
                """
                INSERT INTO strategies (id, "userId", name, description, "riskLevel", confidence,
                    "expectedReturn", timeframe, networks, parameters, "isActive", executions,
                    "successRate", reasoning, "createdAt", "updatedAt")
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT DO NOTHING
                """,
                [(
                    s["id"], s["userId"], s["name"], s["description"], s["riskLevel"],
                    s["confidence"], s["expectedReturn"], s["timeframe"], s["networks"],
                    json.dumps(s["parameters"]), s["isActive"], s["executions"], s["successRate"],
                    s["reasoning"], s["createdAt"], s["updatedAt"]
                ) for s in strategies]
            )

    logger.info(f"Seeded DB: {len(tokens)} tokens, {len(price_records)} prices, {len(trades)} trades, {len(positions)} positions, {len(strategies)} strategies.")
    return {
        "status": "success",
        "tokens": len(tokens),
        "price_points": len(price_records),
        "trades": len(trades),
        "positions": len(positions),
        "strategies": len(strategies),
    }
