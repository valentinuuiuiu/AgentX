"""
Flash Loan Arbitrage Scanner
============================
Zero capital. Flash loans from Aave/Uniswap V2.
FunctionGemma analyzes. Three Filters validate.
Does NOT auto-execute without explicit consent.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from utils.hermes_bridge import HermesBridge, ThreeFilters, get_bridge

logger = logging.getLogger("FlashLoanScanner")

FLASH_TOKENS = ["ETH", "USDC", "USDT", "DAI", "WBTC", "LINK"]
AVERAGE_GAS_COST_USD = 5.0


class FlashLoanScanner:
    """
    Scans for flash loan arbitrage opportunities.
    Uses FunctionGemma for AI-powered evaluation.
    Uses Three Filters for safety.
    """

    def __init__(self, bridge: HermesBridge = None):
        self.bridge = bridge or get_bridge()
        self.client = httpx.AsyncClient(timeout=30.0) if HTTPX_AVAILABLE else None
        self.opportunities_found = 0
        self.scans_completed = 0
        logger.info("Flash Loan Scanner initialized")

    async def get_token_prices(self, token: str = "ETH") -> Dict[str, Any]:
        if not self.client:
            return {"error": "httpx not available"}
        url = f"https://api.dexscreener.com/latest/dex/search?q={token}"
        try:
            resp = await self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                pairs = data.get("pairs", [])[:20]
                dex_prices = {}
                for pair in pairs:
                    dex = pair.get("dexId", "unknown")
                    price = pair.get("priceUsd", "0")
                    if dex not in dex_prices:
                        dex_prices[dex] = []
                    dex_prices[dex].append({
                        "price_usd": float(price) if price else 0,
                        "pair": f"{pair.get('baseToken',{}).get('symbol','?')}/{pair.get('quoteToken',{}).get('symbol','?')}",
                        "liquidity": pair.get("liquidity", {}).get("usd", 0),
                        "volume_24h": pair.get("volume", {}).get("h24", 0),
                        "dex": dex,
                    })
                return {"token": token, "dex_prices": dex_prices, "pairs_count": len(pairs)}
            return {"error": f"DexScreener returned {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def find_arbitrage(self, token: str = "ETH") -> Dict[str, Any]:
        price_data = await self.get_token_prices(token)
        if "error" in price_data:
            return price_data
        dex_prices = price_data.get("dex_prices", {})
        opportunities = []
        for dex_a, pairs_a in dex_prices.items():
            for dex_b, pairs_b in dex_prices.items():
                if dex_a == dex_b:
                    continue
                for pair_a in pairs_a:
                    for pair_b in pairs_b:
                        if pair_a["pair"] != pair_b["pair"]:
                            continue
                        price_a, price_b = pair_a["price_usd"], pair_b["price_usd"]
                        if price_a <= 0 or price_b <= 0:
                            continue
                        if price_a < price_b:
                            buy_dex, sell_dex, buy_price, sell_price = dex_a, dex_b, price_a, price_b
                        else:
                            buy_dex, sell_dex, buy_price, sell_price = dex_b, dex_a, price_b, price_a
                        spread_pct = ((sell_price - buy_price) / buy_price) * 100
                        estimated_profit = spread_pct - (AVERAGE_GAS_COST_USD / buy_price * 100)
                        if spread_pct > 0.1:
                            opportunities.append({
                                "token_pair": pair_a["pair"], "buy_dex": buy_dex, "sell_dex": sell_dex,
                                "buy_price": buy_price, "sell_price": sell_price,
                                "spread_pct": round(spread_pct, 4),
                                "estimated_profit_pct": round(estimated_profit, 4),
                                "min_liquidity": min(pair_a.get("liquidity", 0), pair_b.get("liquidity", 0)),
                                "gas_cost_est": AVERAGE_GAS_COST_USD,
                            })
        opportunities.sort(key=lambda x: x["estimated_profit_pct"], reverse=True)
        self.opportunities_found += len(opportunities)
        self.scans_completed += 1
        return {"token": token, "opportunities": opportunities[:10],
                "total_found": len(opportunities), "scan_timestamp": datetime.now().isoformat()}

    async def evaluate_with_ai(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.bridge.mcp.function_gemma_execute(
            function_name="llm:arbitrage_evaluator",
            parameters={"opportunity": opportunity,
                "considerations": ["gas costs", "slippage", "MEV risk", "flash loan fee", "time sensitivity"]},
        )
        return {"opportunity": opportunity, "ai_evaluation": result, "timestamp": datetime.now().isoformat()}

    def validate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        filter_result = self.bridge.filters.evaluate(
            f"Arbitrage: buy {opportunity.get('token_pair')} on {opportunity.get('buy_dex')} "
            f"sell on {opportunity.get('sell_dex')} spread {opportunity.get('spread_pct')}%",
            context={"involves_funds": True, "verified_safe": False})
        spread = opportunity.get("spread_pct", 0)
        if spread > 5.0:
            filter_result["filters"]["sincerity"] = False
            filter_result["reasoning"] += "; Spread >5% likely wash trading or stale data"
            filter_result["passed"] = False
        liquidity = opportunity.get("min_liquidity", 0)
        if liquidity > 0 and liquidity < 1000:
            filter_result["filters"]["love"] = False
            filter_result["reasoning"] += "; Very low liquidity could harm traders"
            filter_result["passed"] = False
        return filter_result

    async def full_scan(self, token: str = "ETH") -> Dict[str, Any]:
        scan_result = await self.find_arbitrage(token)
        opportunities = scan_result.get("opportunities", [])
        if not opportunities:
            return {"token": token, "status": "no_opportunities", "scan": scan_result, "timestamp": datetime.now().isoformat()}
        top_opp = opportunities[0]
        ai_eval = await self.evaluate_with_ai(top_opp)
        filter_result = self.validate_opportunity(top_opp)
        return {"token": token, "status": "opportunities_found", "top_opportunity": top_opp,
                "all_opportunities": opportunities, "ai_evaluation": ai_eval.get("ai_evaluation"),
                "three_filters": filter_result, "actionable": filter_result.get("passed", False),
                "scan_stats": {"total_found": len(opportunities), "scans_completed": self.scans_completed},
                "timestamp": datetime.now().isoformat()}

    async def scan_all_tokens(self) -> Dict[str, Any]:
        results = {}
        for token in FLASH_TOKENS:
            results[token] = await self.find_arbitrage(token)
            await asyncio.sleep(1)
        return {"tokens_scanned": len(results), "results": results, "timestamp": datetime.now().isoformat()}

    async def close(self):
        if self.client:
            await self.client.aclose()
        logger.info("Flash Loan Scanner closed")


async def _test():
    print("=" * 50)
    print("FLASH LOAN SCANNER TEST")
    print("=" * 50)
    scanner = FlashLoanScanner()
    print("\n1. Getting ETH prices from DexScreener...")
    prices = await scanner.get_token_prices("ETH")
    if "error" in prices:
        print(f"   Error: {prices['error']}")
    else:
        print(f"   Found prices across {len(prices.get('dex_prices', {}))} DEXes")
    print("\n2. Finding arbitrage...")
    arbs = await scanner.find_arbitrage("ETH")
    print(f"   Found {arbs.get('total_found', 0)} opportunities")
    if arbs.get("opportunities"):
        top = arbs["opportunities"][0]
        v = scanner.validate_opportunity(top)
        tag = "PASS" if v["passed"] else "REJECT"
        print(f"   Top: {top['token_pair']} spread={top['spread_pct']}% [{tag}]")
    await scanner.close()
    print("\nSCAN TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(_test())
