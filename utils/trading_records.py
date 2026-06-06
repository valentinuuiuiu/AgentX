from typing import List, Dict, Any
from .user_management import Database
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def get_positions_by_user(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve open positions for a user."""
    query = """
        SELECT id, token, amount, entry_price, network, created_at
        FROM trading_positions
        WHERE user_id = $1
        ORDER BY created_at DESC
    """
    try:
        rows = await Database.fetch(query, user_id)
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error fetching positions for user {user_id}: {e}", exc_info=True)
        return []


async def get_history_by_user(user_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Retrieve trading history for a user."""
    query = """
        SELECT id, token, amount, price, side, status,
               network, tx_hash, created_at
        FROM trading_history
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """
    try:
        rows = await Database.fetch(query, user_id, limit, offset)
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error fetching history for user {user_id}: {e}", exc_info=True)
        return []


async def add_trade_to_history(
    user_id: int,
    token: str,
    amount: float,
    price: float,
    side: str,
    status: str = "filled",
    network: str = None,
    tx_hash: str = None,
) -> Dict[str, Any]:
    """Adds a new trade record to the trading_history table."""
    query = """
        INSERT INTO trading_history (user_id, token, amount, price, side, status, network, tx_hash)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """
    try:
        new_trade = await Database.fetch(
            query, user_id, token, amount, price, side, status, network, tx_hash
        )
        if new_trade:
            return dict(new_trade[0])
    except Exception as e:
        logger.error(f"Error adding trade history for user {user_id}: {e}", exc_info=True)
    return None
