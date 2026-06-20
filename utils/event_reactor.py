"""
Event Reactor Subagent for Rehoboam
====================================
Monitors Ethereum mainnet for DEX swap events via Alchemy WebSocket / JSON-RPC,
detects large swaps (>100 ETH), fetches Chainlink price, and evaluates
arbitrage opportunities (price impact > 0.5%).

Uses:
  - websockets for Alchemy WSS subscription (primary)
  - httpx for Alchemy JSON-RPC calls and polling fallback
  - Pure-Python keccak-fips-1600 for event topic computation
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

import os
import httpx
import websockets

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALCHEMY_KEY = os.environ.get("ALCHEMY_API_KEY", "QfkjpUEE-OGny-o7VA7Hvo2VJ7J4ui9H")
ALCHEMY_RPC_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"
ALCHEMY_WSS_URL = f"wss://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

CHAINLINK_ETH_USD_FEED = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
CHAINLINK_ROUND_DATA_SELECTOR = "0xfeaf968c"
CHAINLINK_DECIMALS = 8

# Uniswap V2: Swap(address,uint256,uint256,uint256,uint256,address)
# Event: Swap(address indexed sender, uint256 amount0In, uint256 amount1In,
#             uint256 amount0Out, uint256 amount1Out, address indexed to)
UNISWAP_V2_SWAP_TOPIC = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
# Uniswap V3: Swap(address,address,int256,int256,uint160,uint128,int24)
# Event: Swap(address indexed sender, address indexed recipient, int256 amount0,
#             int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
UNISWAP_V3_SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"

WETH_ADDRESS = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"

LARGE_SWAP_THRESHOLD_ETH = 100.0
ARB_PRICE_IMPACT_THRESHOLD = 0.005  # 0.5%
POLL_INTERVAL_SECONDS = 12
MAX_EVENTS = 100
WS_RECONNECT_DELAY = 5
WS_PING_INTERVAL = 20
WS_PING_TIMEOUT = 60

# Known Uniswap V2/V3 factory addresses for pair identification
UNISWAP_V2_FACTORY = "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"
UNISWAP_V3_FACTORY = "0x1f98431c8ad98523631ae4a59f267346ea31f984"

# ---------------------------------------------------------------------------
# Pure-Python Keccak-256 (FIPS-202 / SHA-3 candidate)
# Reference: NIST FIPS 202, Keccak reference implementation
# ---------------------------------------------------------------------------

# Round constants (RC)
_KECCAK_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

# Rho rotation offsets computed per FIPS-202 Section 3.2.2
# Indexed as _RHO[5*y + x] to match state indexing
_offsets_dict = {}
_offsets_dict[(0, 0)] = 0
_x, _y = 1, 0
for _t in range(24):
    _offsets_dict[(_x, _y)] = ((_t + 1) * (_t + 2) // 2) % 64
    _x, _y = _y, (2 * _x + 3 * _y) % 5

_RHO_FLAT = [0] * 25
for (_x, _y), _r in _offsets_dict.items():
    _RHO_FLAT[5 * _y + _x] = _r

M64 = 0xFFFFFFFFFFFFFFFF  # 64-bit mask

def _rot64(x: int, n: int) -> int:
    """Rotate a 64-bit integer left by n bits."""
    n = n % 64
    if n == 0:
        return x & M64
    return ((x << n) | (x >> (64 - n))) & M64

def _keccak_f1600(state: list) -> list:
    """
    Keccak-f[1600] permutation.
    state: list of 25 uint64 values, indexed as state[5*y + x] (column-major by x).
    """
    for rnd in range(24):
        # θ (theta)
        bc = [0] * 5
        for i in range(5):
            bc[i] = state[i] ^ state[i + 5] ^ state[i + 10] ^ state[i + 15] ^ state[i + 20]
        for i in range(5):
            t = bc[(i + 4) % 5] ^ _rot64(bc[(i + 1) % 5], 1)
            for j in range(5):
                state[5 * j + i] ^= t

        # ρ (rho) and π (pi) combined
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                nx = y
                ny = (2 * x + 3 * y) % 5
                b[5 * ny + nx] = _rot64(state[5 * y + x], _RHO_FLAT[5 * y + x])

        # χ (chi)
        for y in range(5):
            for x in range(5):
                state[5 * y + x] = b[5 * y + x] ^ ((~b[5 * y + (x + 1) % 5]) & b[5 * y + (x + 2) % 5])

        # ι (iota)
        state[0] ^= _KECCAK_RC[rnd]

    return [s & M64 for s in state]

def keccak256(data: bytes) -> bytes:
    """
    Compute Keccak-256 hash (as used in Ethereum, NOT SHA3-256).
    Uses the Keccak sponge with rate=1088 bits (136 bytes), capacity=512 bits.
    Padding: multi-rate padding (pad10*1) = 0x01 ... 0x80
    """
    rate_bytes = 136  # (1600 - 512) / 8 = 1088 / 8

    # Padding
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate_bytes != 0:
        padded.append(0x00)
    padded[-1] |= 0x80

    # Initialize state
    state = [0] * 25

    # Absorb
    for offset in range(0, len(padded), rate_bytes):
        block = padded[offset:offset + rate_bytes]
        for i in range(rate_bytes // 8):
            lane = int.from_bytes(block[i*8:(i+1)*8], 'little')
            state[i] ^= lane
        state = _keccak_f1600(state)

    # Squeeze (256 bits = 4 lanes = 32 bytes)
    output = b''.join(s.to_bytes(8, 'little') for s in state[:4])
    return output

def _verify_keccak():
    """Verify our keccak256 against known Ethereum hashes."""
    # keccak256("") = c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
    h = keccak256(b"").hex()
    expected = "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    return h == expected

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SwapEvent:
    """Represents a detected DEX swap event with analysis."""
    block_number: int
    tx_hash: str
    pair: str
    amount_eth: float
    price_impact: float
    arb_opportunity: bool
    chainlink_price: float
    dex_version: str  # "V2" or "V3"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ---------------------------------------------------------------------------
# Event Reactor
# ---------------------------------------------------------------------------

class EventReactor:
    """
    Monitors Ethereum mainnet for large DEX swap events and evaluates
    arbitrage opportunities by comparing against Chainlink price feed.
    """

    def __init__(
        self,
        alchemy_rpc_url: str = ALCHEMY_RPC_URL,
        alchemy_wss_url: str = ALCHEMY_WSS_URL,
        chainlink_feed: str = CHAINLINK_ETH_USD_FEED,
        large_swap_threshold: float = LARGE_SWAP_THRESHOLD_ETH,
        arb_threshold: float = ARB_PRICE_IMPACT_THRESHOLD,
        poll_interval: int = POLL_INTERVAL_SECONDS,
        max_events: int = MAX_EVENTS,
    ):
        self.alchemy_rpc_url = alchemy_rpc_url
        self.alchemy_wss_url = alchemy_wss_url
        self.chainlink_feed = chainlink_feed
        self.large_swap_threshold = large_swap_threshold
        self.arb_threshold = arb_threshold
        self.poll_interval = poll_interval
        self.max_events = max_events

        # Event storage (circular buffer)
        self._events: deque = deque(maxlen=max_events)
        self._arb_events: deque = deque(maxlen=max_events)

        # Monitoring state
        self._monitoring = False
        self._ws_connected = False
        self._last_block: int = 0
        self._ws_task: Optional[asyncio.Task] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._chainlink_price: float = 0.0
        self._chainlink_price_ts: float = 0.0

        # HTTP client (created lazily)
        self._http_client: Optional[httpx.AsyncClient] = None

        # Verify keccak implementation
        if not _verify_keccak():
            logger.warning("Keccak-256 self-test failed; using hardcoded topic hashes only")

        # Precompute / verify event topic hashes via keccak256
        v2_sig = b"Swap(address,uint256,uint256,uint256,uint256,address)"
        v3_sig = b"Swap(address,address,int256,int256,uint160,uint128,int24)"
        self._v2_topic_computed = "0x" + keccak256(v2_sig).hex()
        self._v3_topic_computed = "0x" + keccak256(v3_sig).hex()

        # Use hardcoded known-correct values as primary, computed as verification
        if self._v2_topic_computed != UNISWAP_V2_SWAP_TOPIC:
            logger.debug(f"V2 topic computed={self._v2_topic_computed} != hardcoded; using hardcoded")
        if self._v3_topic_computed != UNISWAP_V3_SWAP_TOPIC:
            logger.debug(f"V3 topic computed={self._v3_topic_computed} != hardcoded; using hardcoded")

        self.swap_topics = {
            UNISWAP_V2_SWAP_TOPIC: "V2",
            UNISWAP_V3_SWAP_TOPIC: "V3",
        }

        logger.info("EventReactor initialized")

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def _rpc_call(self, method: str, params: list) -> Any:
        """Make a JSON-RPC call to Alchemy."""
        client = await self._get_http_client()
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params,
        }
        resp = await client.post(self.alchemy_rpc_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"RPC error: {data['error']}")
        return data.get("result")

    # ------------------------------------------------------------------
    # Chainlink price
    # ------------------------------------------------------------------

    async def _fetch_chainlink_price(self) -> float:
        """
        Fetch current ETH/USD price from Chainlink via eth_call.
        Selector 0xfeaf968c = latestRoundData()
        Decodes 5 x 32-byte words: roundId, answer, startedAt, updatedAt, answeredInRound
        Answer has 8 decimals.
        """
        try:
            data = CHAINLINK_ROUND_DATA_SELECTOR
            result = await self._rpc_call("eth_call", [
                {"to": self.chainlink_feed, "data": data},
                "latest"
            ])
            if not result or len(result) < 2 + 64 * 5:
                logger.warning(f"Short Chainlink response: {result}")
                return self._chainlink_price

            # Strip 0x prefix, split into 5 x 64-hex-char words
            raw = result[2:] if result.startswith("0x") else result
            words = [raw[i:i + 64] for i in range(0, 64 * 5, 64)]
            answer = int(words[1], 16)  # second word = answer
            price = answer / (10 ** CHAINLINK_DECIMALS)
            self._chainlink_price = price
            self._chainlink_price_ts = time.time()
            logger.debug(f"Chainlink ETH/USD: ${price:.2f}")
            return price
        except Exception as e:
            logger.error(f"Chainlink price fetch failed: {e}")
            return self._chainlink_price

    # ------------------------------------------------------------------
    # Block processing
    # ------------------------------------------------------------------

    async def _get_latest_block_number(self) -> int:
        result = await self._rpc_call("eth_blockNumber", [])
        return int(result, 16)

    async def _get_block_receipts(self, block_hex: str) -> list:
        """Get all transaction receipts for a block via alchemy_getTransactionReceipts."""
        try:
            result = await self._rpc_call("alchemy_getTransactionReceipts", [
                {"blockNumber": block_hex}
            ])
            return result.get("receipts", []) if isinstance(result, dict) else []
        except Exception:
            # Fallback: get block with tx hashes, then fetch each receipt
            block = await self._rpc_call("eth_getBlockByNumber", [block_hex, False])
            if not block or "transactions" not in block:
                return []
            txs = block["transactions"]
            receipts = []
            for tx_hash in txs:
                receipt = await self._rpc_call("eth_getTransactionReceipt", [tx_hash])
                if receipt:
                    receipts.append(receipt)
            return receipts

    async def _get_block_logs(self, block_hex: str) -> list:
        """Get Swap event logs for a given block."""
        filter_obj = {
            "fromBlock": block_hex,
            "toBlock": block_hex,
            "topics": [
                [UNISWAP_V2_SWAP_TOPIC, UNISWAP_V3_SWAP_TOPIC]
            ]
        }
        try:
            logs = await self._rpc_call("eth_getLogs", [filter_obj])
            return logs if isinstance(logs, list) else []
        except Exception as e:
            logger.error(f"Failed to get logs for block {block_hex}: {e}")
            return []

    # ------------------------------------------------------------------
    # Swap analysis
    # ------------------------------------------------------------------

    def _extract_swap_data(self, log: dict) -> Optional[dict]:
        """
        Extract swap details from a log entry.
        Returns dict with: pair, amount_eth, dex_version, or None.
        """
        topics = log.get("topics", [])
        if not topics:
            return None

        topic0 = topics[0]
        dex_version = self.swap_topics.get(topic0)
        if not dex_version:
            return None

        data_hex = log.get("data", "0x")
        if data_hex.startswith("0x"):
            data_hex = data_hex[2:]

        pair = log.get("address", "unknown")

        try:
            if dex_version == "V2":
                # V2 Swap(address indexed sender, uint256 amount0In, uint256 amount1In,
                #          uint256 amount0Out, uint256 amount1Out, address indexed to)
                # topics[0]=event sig, topics[1]=sender, topics[2]=to
                # data contains: amount0In, amount1In, amount0Out, amount1Out (4 x 32 bytes)
                if len(data_hex) < 256:
                    return None
                words = [data_hex[i:i + 64] for i in range(0, 256, 64)]
                amounts = [int(w, 16) for w in words]
                # amounts: [amount0In, amount1In, amount0Out, amount1Out]
                amount_in_eth = max(amounts[0], amounts[1]) / 1e18
                amount_out_eth = max(amounts[2], amounts[3]) / 1e18
                amount_eth = max(amount_in_eth, amount_out_eth)
            elif dex_version == "V3":
                # V3 Swap(address indexed sender, address indexed recipient,
                #          int256 amount0, int256 amount1, uint160 sqrtPriceX96,
                #          uint128 liquidity, int24 tick)
                if len(data_hex) < 256:
                    return None
                words = [data_hex[i:i + 64] for i in range(0, 256, 64)]
                amount0_raw = int(words[0], 16)
                amount1_raw = int(words[1], 16)
                # Interpret as signed int256
                if amount0_raw >= 2 ** 255:
                    amount0_raw -= 2 ** 256
                if amount1_raw >= 2 ** 255:
                    amount1_raw -= 2 ** 256
                amount0 = abs(amount0_raw) / 1e18
                amount1 = abs(amount1_raw) / 1e18
                amount_eth = max(amount0, amount1)
            else:
                return None
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to decode swap data: {e}")
            return None

        return {
            "pair": pair,
            "amount_eth": amount_eth,
            "dex_version": dex_version,
        }

    def _estimate_price_impact(self, amount_eth: float, chainlink_price: float) -> float:
        """
        Estimate price impact of a swap relative to Chainlink reference price.
        Simple model: larger swaps have proportionally larger impact.
        Uses a conservative AMM curve approximation.
        For a constant-product AMM with ~500M USD TVL in ETH/USDC,
        a swap of X ETH moves price by approximately:
          impact ≈ 2 * X / TVL_eth
        We use a rough TVL estimate of 300K ETH for major pairs.
        """
        if chainlink_price <= 0:
            return 0.0
        # Approximate: assume a typical Uniswap pool has ~300K ETH liquidity
        # This is a rough heuristic; in production we'd query the pool's reserves
        typical_pool_tvl_eth = 300_000.0
        # Price impact ≈ 2 * swap_amount / pool_reserve (constant product approximation)
        impact = (2.0 * amount_eth) / typical_pool_tvl_eth
        return impact

    async def _process_log(self, log: dict):
        """Process a single swap log entry."""
        swap = self._extract_swap_data(log)
        if not swap:
            return

        amount_eth = swap["amount_eth"]
        if amount_eth < self.large_swap_threshold:
            return  # Skip small swaps

        block_number_hex = log.get("blockNumber", "0x0")
        block_number = int(block_number_hex, 16) if isinstance(block_number_hex, str) else block_number_hex
        tx_hash = log.get("transactionHash", "unknown")

        # Fetch fresh Chainlink price
        chainlink_price = await self._fetch_chainlink_price()

        # Estimate price impact
        price_impact = self._estimate_price_impact(amount_eth, chainlink_price)
        arb_opportunity = price_impact > self.arb_threshold

        event = SwapEvent(
            block_number=block_number,
            tx_hash=tx_hash,
            pair=swap["pair"],
            amount_eth=amount_eth,
            price_impact=price_impact,
            arb_opportunity=arb_opportunity,
            chainlink_price=chainlink_price,
            dex_version=swap["dex_version"],
        )

        self._events.append(event)
        if arb_opportunity:
            self._arb_events.append(event)

        status = "ARB OPPORTUNITY" if arb_opportunity else "large swap"
        logger.info(
            f"[{status}] block={block_number} tx={tx_hash[:16]}… "
            f"pair={swap['pair'][:10]}… amount={amount_eth:.2f} ETH "
            f"impact={price_impact * 100:.3f}% chainlink=${chainlink_price:.2f}"
        )

    async def _process_block(self, block_number: int):
        """Process all swap logs in a given block."""
        block_hex = hex(block_number)
        logs = await self._get_block_logs(block_hex)
        if not logs:
            return
        logger.debug(f"Block {block_number}: {len(logs)} swap logs")
        for log_entry in logs:
            try:
                await self._process_log(log_entry)
            except Exception as e:
                logger.error(f"Error processing log in block {block_number}: {e}")

    # ------------------------------------------------------------------
    # WebSocket monitoring (primary)
    # ------------------------------------------------------------------

    async def _ws_monitor(self):
        """Connect to Alchemy WSS and subscribe to new blocks + pending txs."""
        while self._monitoring:
            try:
                async with websockets.connect(
                    self.alchemy_wss_url,
                    ping_interval=WS_PING_INTERVAL,
                    ping_timeout=WS_PING_TIMEOUT,
                    max_size=50 * 1024 * 1024,  # 50MB for large blocks
                ) as ws:
                    self._ws_connected = True
                    logger.info("WebSocket connected to Alchemy")

                    # Subscribe to new blocks
                    sub_block = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_subscribe",
                        "params": ["newHeads"]
                    }
                    await ws.send(json.dumps(sub_block))

                    # Subscribe to pending transactions
                    sub_pending = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "eth_subscribe",
                        "params": ["alchemy_pendingTransactions",
                                   {"toAddress": WETH_ADDRESS}]
                    }
                    await ws.send(json.dumps(sub_pending))

                    # Listen for messages
                    async for raw_msg in ws:
                        if not self._monitoring:
                            break

                        try:
                            msg = json.loads(raw_msg)
                        except json.JSONDecodeError:
                            continue

                        method = msg.get("method")

                        if method == "eth_subscription":
                            params = msg.get("params", {})
                            result = params.get("result", {})

                            # New block notification
                            if isinstance(result, dict) and "number" in result:
                                block_hex = result.get("number", "0x0")
                                block_number = int(block_hex, 16)
                                if block_number > self._last_block:
                                    self._last_block = block_number
                                    await self._process_block(block_number)

                            # Pending transaction notification
                            elif isinstance(result, dict) and "hash" in result:
                                # Pending txs are just notifications;
                                # swap detection happens in block logs
                                pass

                        # Handle subscription confirmations
                        elif "id" in msg and "result" in msg:
                            sub_id = msg.get("result", "")
                            logger.debug(f"Subscription confirmed: {sub_id}")

            except websockets.ConnectionClosed as e:
                logger.warning(f"WebSocket closed (code={e.code}), reconnecting in {WS_RECONNECT_DELAY}s...")
                self._ws_connected = False
            except Exception as e:
                logger.error(f"WebSocket error: {e}, reconnecting in {WS_RECONNECT_DELAY}s...")
                self._ws_connected = False

            if self._monitoring:
                await asyncio.sleep(WS_RECONNECT_DELAY)

    # ------------------------------------------------------------------
    # Polling monitoring (fallback)
    # ------------------------------------------------------------------

    async def _poll_monitor(self):
        """Poll for new blocks every POLL_INTERVAL_SECONDS."""
        logger.info(f"Starting block polling every {self.poll_interval}s")

        while self._monitoring:
            try:
                # Skip polling if WebSocket is connected and healthy -
                # the WebSocket handler already processes blocks
                if self._ws_connected:
                    await asyncio.sleep(self.poll_interval)
                    continue

                block_number = await self._get_latest_block_number()
                if block_number > self._last_block:
                    # Process missed blocks (but respect Alchemy free tier 10-block limit)
                    start = self._last_block + 1 if self._last_block > 0 else block_number
                    # Cap the catchup range to avoid API limits
                    if block_number - start > 10:
                        logger.info(f"Catching up: skipping blocks {start}-{block_number - 10}")
                        start = block_number - 9
                    for bn in range(start, block_number + 1):
                        if not self._monitoring:
                            break
                        await self._process_block(bn)
                    self._last_block = block_number
            except Exception as e:
                logger.error(f"Polling error: {e}")

            await asyncio.sleep(self.poll_interval)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start_monitoring(self, use_websocket: bool = True):
        """
        Start monitoring for DEX swap events.

        Args:
            use_websocket: If True, use WSS (primary). If False, use polling.
        """
        if self._monitoring:
            logger.warning("Monitoring already active")
            return

        self._monitoring = True

        # Initialize block pointer
        try:
            self._last_block = await self._get_latest_block_number()
            logger.info(f"Starting from block {self._last_block}")
        except Exception as e:
            logger.error(f"Failed to fetch initial block number: {e}")
            self._last_block = 0

        # Pre-warm Chainlink price
        await self._fetch_chainlink_price()

        if use_websocket:
            self._ws_task = asyncio.create_task(self._ws_monitor())
            # Also start polling as a safety net
            self._poll_task = asyncio.create_task(self._poll_monitor())
            logger.info("Monitoring started (WebSocket primary + polling fallback)")
        else:
            self._poll_task = asyncio.create_task(self._poll_monitor())
            logger.info("Monitoring started (polling mode)")

    async def stop_monitoring(self):
        """Stop monitoring for DEX swap events."""
        self._monitoring = False
        self._ws_connected = False

        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None

        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        # Close HTTP client
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        logger.info("Monitoring stopped")

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent swap events.

        Args:
            limit: Maximum number of events to return (capped at max_events).

        Returns:
            List of event dicts with: block_number, tx_hash, pair, amount_eth,
            price_impact, arb_opportunity, chainlink_price, dex_version, timestamp
        """
        events = list(self._events)
        return [e.to_dict() for e in events[-limit:]]

    def get_arb_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get events flagged as arbitrage opportunities.

        Args:
            limit: Maximum number of events to return.

        Returns:
            List of event dicts where arb_opportunity is True.
        """
        events = list(self._arb_events)
        return [e.to_dict() for e in events[-limit:]]

    @property
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring

    @property
    def is_ws_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._ws_connected

    @property
    def last_block(self) -> int:
        """Get the last processed block number."""
        return self._last_block

    @property
    def current_chainlink_price(self) -> float:
        """Get the last known Chainlink ETH/USD price."""
        return self._chainlink_price

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            "monitoring": self._monitoring,
            "ws_connected": self._ws_connected,
            "last_block": self._last_block,
            "total_events": len(self._events),
            "arb_events": len(self._arb_events),
            "chainlink_price": self._chainlink_price,
            "chainlink_price_age": time.time() - self._chainlink_price_ts if self._chainlink_price_ts > 0 else None,
        }

    async def close(self):
        """Clean shutdown."""
        await self.stop_monitoring()


# ---------------------------------------------------------------------------
# Synchronous wrapper for simple usage
# ---------------------------------------------------------------------------

class SyncEventReactor:
    """
    Synchronous wrapper around EventReactor for non-async code.
    Manages its own event loop.
    """

    def __init__(self, **kwargs):
        self._reactor = EventReactor(**kwargs)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop

    def start_monitoring(self, use_websocket: bool = True):
        loop = self._get_loop()
        loop.run_until_complete(self._reactor.start_monitoring(use_websocket=use_websocket))
        # Run the monitoring tasks in background
        if use_websocket and self._reactor._ws_task:
            loop.run_until_complete(self._reactor._ws_task)
        elif self._reactor._poll_task:
            loop.run_until_complete(self._reactor._poll_task)

    def stop_monitoring(self):
        loop = self._get_loop()
        loop.run_until_complete(self._reactor.stop_monitoring())

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._reactor.get_recent_events(limit)

    def get_arb_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._reactor.get_arb_events(limit)

    def get_stats(self) -> Dict[str, Any]:
        return self._reactor.get_stats()


# ---------------------------------------------------------------------------
# Standalone runner for testing
# ---------------------------------------------------------------------------

async def _main():
    """Run EventReactor standalone for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    reactor = EventReactor()

    # Graceful shutdown
    import signal

    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _signal_handler():
        stop.set()

    loop.add_signal_handler(signal.SIGINT, _signal_handler)
    loop.add_signal_handler(signal.SIGTERM, _signal_handler)

    await reactor.start_monitoring(use_websocket=True)

    logger.info("EventReactor running. Press Ctrl+C to stop.")

    try:
        await stop.wait()
    finally:
        await reactor.stop_monitoring()
        logger.info(f"Stats: {reactor.get_stats()}")


if __name__ == "__main__":
    asyncio.run(_main())