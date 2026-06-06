"""
Chainlink Circuit Breaker Subagent
====================================
Monitors on-chain Chainlink oracle prices via Alchemy RPC.
Detects price deviations >5% from last known good price.
Detects stale data (update >1hr ago).
Integrates with Three Filters (Dhumavati Maa) -- circuit breaker
only activates protective measures when Love filter passes.

Methods:
  - monitor_price(pair)   : fetch and evaluate one price
  - check_circuit(pair)   : check breaker status without new fetch
  - get_breaker_status()   : full status of all monitored pairs
  - start_monitoring()     : begin async periodic loop
  - stop_monitoring()      : halt the loop
"""

import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum

import httpx

from .hermes_bridge import ThreeFilters

logger = logging.getLogger("CircuitBreaker")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ALCHEMY_RPC_URL = (
    "https://eth-mainnet.g.alchemy.com/v2/"
    "QfkjpUEE-OGny-o7VA7Hvo2VJ7J4ui9H"
)

CHAINLINK_FEEDS: Dict[str, str] = {
    "ETH/USD":  "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
    "BTC/USD":  "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c",
    "LINK/USD": "0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c",
    "USDC/USD": "0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6",
}

LATEST_ROUND_DATA_SELECTOR = "0xfeaf968c"
PRICE_DECIMALS = 8                       # all Chainlink USD feeds use 8
DEVIATION_THRESHOLD = 0.05              # 5 %
STALE_THRESHOLD_SECONDS = 3600          # 1 hour
DEFAULT_MONITOR_INTERVAL = 60            # seconds


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class BreakerState(Enum):
    CLOSED  = "closed"    # normal -- no alert
    OPEN    = "open"      # tripped -- price anomaly or stale data
    UNKNOWN = "unknown"   # no data yet


# ---------------------------------------------------------------------------
# Per-pair record
# ---------------------------------------------------------------------------
class _PairState:
    """Internal bookkeeping for a single price feed."""

    def __init__(self, pair: str):
        self.pair = pair
        self.state: BreakerState = BreakerState.UNKNOWN
        self.last_good_price: Optional[float] = None
        self.last_price: Optional[float] = None
        self.last_round_id: Optional[int] = None
        self.last_updated_at: Optional[int] = None          # unix seconds
        self.freshness_seconds: Optional[float] = None
        self.deviation_pct: Optional[float] = None
        self.alerts: List[str] = []
        self.fetch_count: int = 0
        self.last_fetch_time: Optional[str] = None
        self.filter_result: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
class ChainlinkCircuitBreaker:
    """
    Chainlink Circuit Breaker -- safety subagent for Rehoboam.

    * Reads real on-chain prices via eth_call to Alchemy.
    * Tracks deviation from last-known-good price.
    * Detects stale oracle data.
    * Only activates protective measures when Three Filters Love passes.
    """

    def __init__(
        self,
        rpc_url: str = ALCHEMY_RPC_URL,
        deviation_threshold: float = DEVIATION_THRESHOLD,
        stale_threshold: int = STALE_THRESHOLD_SECONDS,
        monitor_interval: int = DEFAULT_MONITOR_INTERVAL,
    ):
        self.rpc_url = rpc_url
        self.deviation_threshold = deviation_threshold
        self.stale_threshold = stale_threshold
        self.monitor_interval = monitor_interval

        self._client: Optional[httpx.AsyncClient] = None
        self._pairs: Dict[str, _PairState] = {
            pair: _PairState(pair) for pair in CHAINLINK_FEEDS
        }
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        self._global_alerts: List[str] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def _ensure_client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        await self.stop_monitoring()

    # ------------------------------------------------------------------
    # Low-level Chainlink eth_call
    # ------------------------------------------------------------------
    async def _fetch_latest_round_data(self, pair: str) -> Dict[str, Any]:
        """
        Perform a real eth_call to the Chainlink feed contract.
        Returns decoded round data or an error dict.
        """
        feed_address = CHAINLINK_FEEDS.get(pair)
        if not feed_address:
            return {"error": f"No Chainlink feed configured for {pair}"}

        await self._ensure_client()

        try:
            resp = await self._client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [
                        {"to": feed_address, "data": LATEST_ROUND_DATA_SELECTOR},
                        "latest",
                    ],
                    "id": 1,
                },
                timeout=15.0,
            )
            if resp.status_code != 200:
                return {"error": f"Alchemy HTTP {resp.status_code}: {resp.text[:200]}"}

            data = resp.json()
            if "error" in data:
                return {"error": f"RPC error: {data['error']}"}

            result = data.get("result", "")
            if not result or result == "0x" or len(result) < 2 + 320:
                return {"error": f"Invalid/empty Chainlink response: {result[:40]}"}

            # Decode 5 x 32-byte words (160 bytes = 320 hex chars after 0x)
            raw = bytes.fromhex(result[2:])
            if len(raw) < 160:
                return {"error": f"Response too short ({len(raw)} bytes), expected 160"}

            round_id       = int.from_bytes(raw[0:32],   "big")
            answer          = int.from_bytes(raw[32:64],  "big")
            started_at     = int.from_bytes(raw[64:96],  "big")
            updated_at     = int.from_bytes(raw[96:128],  "big")
            answered_in     = int.from_bytes(raw[128:160], "big")

            price = answer / (10 ** PRICE_DECIMALS)
            now_ts = datetime.now(timezone.utc).timestamp()
            freshness = now_ts - updated_at if updated_at > 0 else None

            return {
                "pair": pair,
                "price": price,
                "round_id": round_id,
                "answer_raw": answer,
                "started_at": started_at,
                "updated_at": updated_at,
                "answered_in_round": answered_in,
                "freshness_seconds": freshness,
                "feed_address": feed_address,
            }

        except httpx.HTTPError as exc:
            return {"error": f"HTTP error: {exc}"}
        except Exception as exc:
            return {"error": f"Decode error: {exc}"}

    # ------------------------------------------------------------------
    # Three Filters integration
    # ------------------------------------------------------------------
    def _check_love_filter(self, action: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate via Three Filters but only return the Love filter result.
        The circuit breaker protects funds -- it only activates protective
        measures (halting trades, alerting) when the Love filter passes,
        meaning the action genuinely serves welfare.
        """
        result = ThreeFilters.evaluate(action, context)
        return result["filters"]["love"], result

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------
    def _analyze_pair(self, state: _PairState, fetched: Dict[str, Any]) -> None:
        """
        Given fresh fetched data, update state and determine alerts.
        """
        state.alerts.clear()

        price = fetched.get("price")
        freshness = fetched.get("freshness_seconds")
        updated_at = fetched.get("updated_at")

        if price is None or price <= 0:
            state.state = BreakerState.OPEN
            state.alerts.append(f"Invalid price received: {price}")
            return

        # --- deviation check ---
        if state.last_good_price is not None and state.last_good_price > 0:
            deviation = (price - state.last_good_price) / state.last_good_price
            deviation_pct = abs(deviation)
            state.deviation_pct = round(deviation_pct * 100, 4)

            if deviation_pct > self.deviation_threshold:
                direction = "up" if deviation > 0 else "down"
                state.alerts.append(
                    f"PRICE DEVIATION: {state.pair} moved {state.deviation_pct:.2f}% {direction} "
                    f"(last good: {state.last_good_price:.2f}, now: {price:.2f})"
                )
                # Before tripping the breaker, check Love filter
                love_passes, filt = self._check_love_filter(
                    f"Activate circuit breaker for {state.pair} price deviation {state.deviation_pct:.2f}%",
                    {"involves_funds": True, "deviation_pct": state.deviation_pct},
                )
                state.filter_result = filt
                if love_passes:
                    state.state = BreakerState.OPEN
                    state.alerts.append("Circuit breaker ACTIVATED (Love filter passed -- protective action sanctioned)")
                else:
                    # Love filter failed -- do NOT activate breaker, only warn
                    state.state = BreakerState.CLOSED
                    state.alerts.append(
                        "Circuit breaker NOT activated (Love filter failed -- "
                        "action does not serve welfare, breaker stays closed)"
                    )
            else:
                # Price within tolerance -- update good price
                state.last_good_price = price
                state.state = BreakerState.CLOSED
        else:
            # First-ever reading -- establish baseline
            state.last_good_price = price
            state.state = BreakerState.CLOSED
            state.deviation_pct = 0.0

        # --- staleness check ---
        if freshness is not None:
            state.freshness_seconds = round(freshness)
            if freshness > self.stale_threshold:
                stale_hours = freshness / 3600
                state.alerts.append(
                    f"STALE DATA: {state.pair} oracle last updated {stale_hours:.1f}h ago "
                    f"(threshold: {self.stale_threshold/3600:.0f}h)"
                )
                # Stale data alone doesn't trip the breaker to OPEN,
                # but it does downgrade to a warning state
                if state.state == BreakerState.CLOSED:
                    state.alerts.append("Stale data warning -- breaker remains closed but data unreliable")
        else:
            state.freshness_seconds = None

        # --- update bookkeeping ---
        state.last_price = price
        state.last_round_id = fetched.get("round_id")
        state.last_updated_at = updated_at
        state.last_fetch_time = datetime.now(timezone.utc).isoformat()
        state.fetch_count += 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def monitor_price(self, pair: str) -> Dict[str, Any]:
        """
        Fetch the latest Chainlink price for *pair*, run deviation and
        staleness checks, and return a status dict.

        Example:  await breaker.monitor_price("ETH/USD")
        """
        if pair not in self._pairs:
            return {"error": f"Unknown pair {pair}. Available: {list(self._pairs.keys())}"}

        # Ensure the pair state object exists even if added dynamically
        state = self._pairs[pair]

        fetched = await self._fetch_latest_round_data(pair)
        if "error" in fetched:
            state.alerts.append(f"Fetch failed: {fetched['error']}")
            state.state = BreakerState.UNKNOWN
            return {
                "pair": pair,
                "state": state.state.value,
                "alerts": state.alerts.copy(),
                "error": fetched["error"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        self._analyze_pair(state, fetched)

        # Propagate global alerts
        for a in state.alerts:
            if a not in self._global_alerts:
                self._global_alerts.append(a)

        if state.alerts:
            logger.warning(f"[CircuitBreaker] {pair}: {'; '.join(state.alerts)}")
        else:
            logger.debug(f"[CircuitBreaker] {pair}: OK price={state.last_price}")

        return {
            "pair": pair,
            "state": state.state.value,
            "price": state.last_price,
            "last_good_price": state.last_good_price,
            "deviation_pct": state.deviation_pct,
            "freshness_seconds": state.freshness_seconds,
            "round_id": state.last_round_id,
            "updated_at_utc": (
                datetime.fromtimestamp(state.last_updated_at, tz=timezone.utc).isoformat()
                if state.last_updated_at else None
            ),
            "alerts": state.alerts.copy(),
            "filter_result": state.filter_result,
            "fetch_count": state.fetch_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def check_circuit(self, pair: str) -> Dict[str, Any]:
        """
        Return the current breaker status for *pair* without performing
        a new on-chain fetch.

        Example:  breaker.check_circuit("ETH/USD")
        """
        if pair not in self._pairs:
            return {"error": f"Unknown pair {pair}. Available: {list(self._pairs.keys())}"}

        state = self._pairs[pair]
        return {
            "pair": pair,
            "state": state.state.value,
            "price": state.last_price,
            "last_good_price": state.last_good_price,
            "deviation_pct": state.deviation_pct,
            "freshness_seconds": state.freshness_seconds,
            "round_id": state.last_round_id,
            "updated_at_utc": (
                datetime.fromtimestamp(state.last_updated_at, tz=timezone.utc).isoformat()
                if state.last_updated_at else None
            ),
            "alerts": state.alerts.copy(),
            "fetch_count": state.fetch_count,
            "last_fetch_time": state.last_fetch_time,
        }

    def get_breaker_status(self) -> Dict[str, Any]:
        """
        Return the full status of all monitored pairs plus global alerts.

        Example:  breaker.get_breaker_status()
        """
        pairs = {}
        any_open = False
        any_unknown = False

        for pair, state in self._pairs.items():
            is_open = state.state == BreakerState.OPEN
            is_unknown = state.state == BreakerState.UNKNOWN
            if is_open:
                any_open = True
            if is_unknown:
                any_unknown = True

            pairs[pair] = {
                "state": state.state.value,
                "price": state.last_price,
                "last_good_price": state.last_good_price,
                "deviation_pct": state.deviation_pct,
                "freshness_seconds": state.freshness_seconds,
                "round_id": state.last_round_id,
                "updated_at_utc": (
                    datetime.fromtimestamp(state.last_updated_at, tz=timezone.utc).isoformat()
                    if state.last_updated_at else None
                ),
                "alerts": state.alerts.copy(),
                "fetch_count": state.fetch_count,
                "last_fetch_time": state.last_fetch_time,
            }

        if any_open:
            overall = "OPEN"
        elif any_unknown:
            overall = "DEGRADED"
        else:
            overall = "CLOSED"

        # Trim global alerts to last 50
        recent_alerts = self._global_alerts[-50:]

        return {
            "overall_state": overall,
            "deviation_threshold_pct": self.deviation_threshold * 100,
            "stale_threshold_seconds": self.stale_threshold,
            "monitor_interval_seconds": self.monitor_interval,
            "monitoring": self._running,
            "pairs": pairs,
            "global_alerts": recent_alerts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Periodic monitoring loop
    # ------------------------------------------------------------------
    async def _monitor_loop(self):
        """Internal: continuously poll all feeds."""
        logger.info(
            f"[CircuitBreaker] Monitor loop started "
            f"(interval={self.monitor_interval}s, "
            f"pairs={list(self._pairs.keys())})"
        )
        while self._running:
            # Fetch all pairs sequentially with small delay to avoid
            # hitting rate limits
            for pair in list(self._pairs.keys()):
                if not self._running:
                    break
                try:
                    await self.monitor_price(pair)
                except Exception as exc:
                    logger.error(f"[CircuitBreaker] Error monitoring {pair}: {exc}")
                await asyncio.sleep(0.15)

            # Wait for next cycle
            try:
                await asyncio.sleep(self.monitor_interval)
            except asyncio.CancelledError:
                break

        logger.info("[CircuitBreaker] Monitor loop stopped")

    async def start_monitoring(self, interval: int = None):
        """
        Start the periodic monitoring loop.

        Args:
            interval: Override the default monitor interval (seconds).
        """
        if self._running:
            logger.warning("[CircuitBreaker] Already monitoring")
            return

        if interval is not None:
            self.monitor_interval = interval

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"[CircuitBreaker] Monitoring started (interval={self.monitor_interval}s)")

    async def stop_monitoring(self):
        """Stop the periodic monitoring loop."""
        self._running = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self._monitor_task = None
        logger.info("[CircuitBreaker] Monitoring stopped")

    # ------------------------------------------------------------------
    # Convenience: fetch all prices once
    # ------------------------------------------------------------------
    async def fetch_all_prices(self) -> Dict[str, Any]:
        """
        One-shot fetch of all configured Chainlink feeds.
        Does NOT start the periodic loop.
        """
        results = {}
        for pair in list(self._pairs.keys()):
            results[pair] = await self.monitor_price(pair)
            await asyncio.sleep(0.15)
        return {
            "prices": results,
            "status": self.get_breaker_status(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Module-level singleton (lazy)
# ---------------------------------------------------------------------------
_breaker: Optional[ChainlinkCircuitBreaker] = None

def get_circuit_breaker(**kwargs) -> ChainlinkCircuitBreaker:
    global _breaker
    if _breaker is None:
        _breaker = ChainlinkCircuitBreaker(**kwargs)
    return _breaker


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
async def _test():
    import json as _json

    print("=" * 60)
    print("CHAINLINK CIRCUIT BREAKER TEST")
    print("=" * 60)

    breaker = ChainlinkCircuitBreaker()
    try:
        # -- single pair fetch --
        print("\n[1] Fetching ETH/USD price...")
        result = await breaker.monitor_price("ETH/USD")
        print(f"    State: {result.get('state')}")
        print(f"    Price: ${result.get('price')}")
        print(f"    Deviation: {result.get('deviation_pct')}%")
        print(f"    Freshness: {result.get('freshness_seconds')}s")
        if result.get("alerts"):
            for a in result["alerts"]:
                print(f"    ALERT: {a}")
        else:
            print("    No alerts")

        # -- all pairs --
        print("\n[2] Fetching all prices...")
        all_prices = await breaker.fetch_all_prices()
        for pair, info in all_prices["prices"].items():
            price_str = f"${info.get('price', 'N/A')}" if info.get("price") else "N/A"
            state_str = info.get("state", "unknown")
            dev_str = f"{info.get('deviation_pct', 0)}%"
            fresh_str = f"{info.get('freshness_seconds', '?')}s"
            alerts_n = len(info.get("alerts", []))
            print(f"    {pair:10s}  price={price_str:>10s}  state={state_str:<8s}  "
                  f"dev={dev_str:>8s}  fresh={fresh_str:>8s}  alerts={alerts_n}")

        # -- breaker status --
        print("\n[3] Breaker status:")
        status = breaker.get_breaker_status()
        print(f"    Overall: {status['overall_state']}")
        print(f"    Monitoring: {status['monitoring']}")
        print(f"    Pairs: {len(status['pairs'])}")

        # -- check_circuit without fetch --
        print("\n[4] check_circuit (no fetch) for BTC/USD:")
        circ = breaker.check_circuit("BTC/USD")
        print(f"    state={circ.get('state')}  price={circ.get('price')}  "
              f"deviation={circ.get('deviation_pct')}%")

        # -- short monitoring test (2 cycles at 10s) --
        print("\n[5] Starting monitoring loop for ~25s (2 cycles @ 10s)...")
        await breaker.start_monitoring(interval=10)
        await asyncio.sleep(25)
        await breaker.stop_monitoring()
        print("    Monitoring stopped.")

        final = breaker.get_breaker_status()
        print(f"    Final state: {final['overall_state']}")
        for pair, info in final["pairs"].items():
            print(f"      {pair}: state={info['state']} fetches={info['fetch_count']} "
                  f"alerts={len(info['alerts'])}")

    finally:
        await breaker.close()

    print("\n" + "=" * 60)
    print("CIRCUIT BREAKER TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(_test())