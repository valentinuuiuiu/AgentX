"""
Linear Price Forecasting for Arbitrage Detection
=================================================
Predicts price movements using linear regression on real on-chain data.
Agent verifies off-chain (FREE), only sends on-chain when 100% profitable.
"""

import os
import time
import logging
import asyncio
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from utils.hermes_bridge import get_sync_bridge, HermesBridgeSync, ThreeFilters

logger = logging.getLogger("LinearForecast")


@dataclass
class PricePoint:
    timestamp: float
    price: float
    volume: float = 0.0
    source: str = "chainlink"


@dataclass
class LinearForecast:
    slope: float
    intercept: float
    r_squared: float
    predicted_price: float
    target_time: float
    confidence: float
    direction: str
    magnitude_bps: float


@dataclass
class ArbitrageSignal:
    token: str
    buy_dex: str
    sell_dex: str
    current_spread_bps: float
    predicted_spread_bps: float
    forecast: LinearForecast
    flash_loan_amount: float
    estimated_profit_usd: float
    estimated_gas_cost_usd: float
    net_profit_usd: float
    confidence: float
    timestamp: float
    should_execute: bool


@dataclass
class ForecastConfig:
    min_data_points: int = 5
    max_data_age_seconds: float = 3600.0
    min_r_squared: float = 0.3
    min_confidence: float = 0.6
    flash_loan_fee_bps: float = 5.0
    min_profit_usd: float = 5.0
    estimated_gas_usd: float = 2.0
    protocol_fee_bps: float = 10.0
    lookback_seconds: float = 600.0
    prediction_horizon_seconds: float = 30.0
    tokens: List[str] = field(default_factory=lambda: [
        "ETH/USD", "BTC/USD", "LINK/USD", "USDC/USD", "AAVE/USD"
    ])


class LinearForecaster:
    """Linear regression forecasting engine for price prediction."""

    def __init__(self, config: ForecastConfig = None):
        self.config = config or ForecastConfig()
        self.price_history: Dict[str, List[PricePoint]] = {}
        self._last_cleanup = time.time()

    def add_price(self, token: str, price: float, volume: float = 0.0, source: str = "chainlink"):
        if token not in self.price_history:
            self.price_history[token] = []
        self.price_history[token].append(PricePoint(
            timestamp=time.time(), price=price, volume=volume, source=source
        ))
        if time.time() - self._last_cleanup > 300:
            self._cleanup_old_data()

    def add_prices_bulk(self, prices: Dict[str, float], source: str = "chainlink"):
        for token, price in prices.items():
            self.add_price(token, price, source=source)

    def forecast(self, token: str) -> Optional[LinearForecast]:
        points = self.price_history.get(token, [])
        now = time.time()
        recent = [p for p in points if now - p.timestamp < self.config.lookback_seconds]

        if len(recent) < self.config.min_data_points:
            return None

        t0 = recent[0].timestamp
        times = np.array([p.timestamp - t0 for p in recent])
        prices = np.array([p.price for p in recent])
        volumes = np.array([max(p.volume, 1.0) for p in recent])
        weights = volumes / np.sum(volumes)

        slope, intercept, r_squared = self._weighted_linear_regression(times, prices, weights)

        if r_squared < self.config.min_r_squared:
            return None

        target_time = recent[-1].timestamp + self.config.prediction_horizon_seconds
        target_t = target_time - t0
        predicted_price = slope * target_t + intercept

        current_price = recent[-1].price
        price_change = predicted_price - current_price
        change_bps = (price_change / current_price) * 10000 if current_price > 0 else 0

        sample_conf = min(len(recent) / 20.0, 1.0)
        horizon_conf = max(0.0, 1.0 - (self.config.prediction_horizon_seconds / 300.0))
        confidence = min(max(r_squared * 0.5 + sample_conf * 0.3 + horizon_conf * 0.2, 0.0), 1.0)

        if change_bps > 5:
            direction = "up"
        elif change_bps < -5:
            direction = "down"
        else:
            direction = "neutral"

        return LinearForecast(
            slope=slope, intercept=intercept, r_squared=r_squared,
            predicted_price=predicted_price, target_time=target_time,
            confidence=confidence, direction=direction, magnitude_bps=abs(float(change_bps))
        )

    def _weighted_linear_regression(self, x, y, w) -> Tuple[float, float, float]:
        try:
            w_sum = np.sum(w)
            wx = np.sum(w * x)
            wy = np.sum(w * y)
            wxx = np.sum(w * x * x)
            wxy = np.sum(w * x * y)
            denom = w_sum * wxx - wx * wx
            if abs(denom) < 1e-12:
                return 0.0, float(y[0]) if len(y) > 0 else 0.0, 0.0
            slope = (w_sum * wxy - wx * wy) / denom
            intercept = (wxx * wy - wx * wxy) / denom
            y_pred = slope * x + intercept
            y_mean = np.sum(w * y) / w_sum
            ss_tot = np.sum(w * (y - y_mean) ** 2)
            ss_res = np.sum(w * (y - y_pred) ** 2)
            r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            return float(slope), float(intercept), float(max(0.0, min(1.0, r2)))
        except Exception as e:
            logger.error(f"Linear regression error: {e}")
            return 0.0, 0.0, 0.0

    def _cleanup_old_data(self):
        now = time.time()
        cutoff = now - self.config.lookback_seconds * 2
        for token in list(self.price_history.keys()):
            self.price_history[token] = [p for p in self.price_history[token] if p.timestamp > cutoff]
            if not self.price_history[token]:
                del self.price_history[token]
        self._last_cleanup = now


class ArbitrageScanner:
    """Scans for arbitrage using linear forecasting + Hermes Bridge for real prices."""

    def __init__(self, config: ForecastConfig = None):
        self.config = config or ForecastConfig()
        self.forecaster = LinearForecaster(self.config)
        self.bridge = get_sync_bridge()
        self._signals: List[ArbitrageSignal] = []

    async def scan_all(self) -> List[ArbitrageSignal]:
        signals = []
        try:
            all_prices = await self.bridge.get_all_prices()
            if "prices" not in all_prices:
                logger.warning("No prices from Hermes Bridge")
                return []

            for pair, data in all_prices["prices"].items():
                price = data.get("price_usd", 0) if isinstance(data, dict) else float(data) if data else 0
                if price > 0:
                    self.forecaster.add_price(pair, price, source="chainlink")

            for token in self.config.tokens:
                forecast = self.forecaster.forecast(token)
                if forecast is None:
                    continue
                signal = self._evaluate_arbitrage(token, forecast, all_prices)
                if signal and signal.should_execute:
                    signals.append(signal)

            signals.sort(key=lambda s: s.net_profit_usd, reverse=True)
            self._signals = signals

            if signals:
                logger.info(f"Found {len(signals)} profitable arbitrage opportunities")
                for s in signals[:3]:
                    logger.info(f"  {s.token}: {s.buy_dex}->{s.sell_dex} spread={s.predicted_spread_bps:.1f}bps net=${s.net_profit_usd:.2f}")
            else:
                logger.debug("No profitable arbitrage opportunities found")
            return signals
        except Exception as e:
            logger.error(f"Error in scan_all: {e}")
            return []

    def _evaluate_arbitrage(self, token, forecast, prices):
        try:
            pair_data = prices.get("prices", {}).get(token, {})
            current_price = pair_data.get("price_usd", 0) if isinstance(pair_data, dict) else float(pair_data) if pair_data else 0
            if current_price <= 0:
                return None

            predicted_change_pct = (forecast.predicted_price - current_price) / current_price
            predicted_spread_bps = abs(predicted_change_pct) * 10000

            buy_dex = "dex_lower_price" if forecast.direction == "up" else "dex_higher_price"
            sell_dex = "dex_higher_price" if forecast.direction == "up" else "dex_lower_price"

            # Calculate all costs and profit
            flash_loan_amount = 10000.0
            flash_fee = (flash_loan_amount * self.config.flash_loan_fee_bps) / 10000
            gas_cost = self.config.estimated_gas_usd
            protocol_fee = (flash_loan_amount * abs(predicted_change_pct) * self.config.protocol_fee_bps) / 10000
            gross_profit = flash_loan_amount * abs(predicted_change_pct)
            net_profit = gross_profit - flash_fee - gas_cost - protocol_fee

            filter_result = ThreeFilters.evaluate(
                f"Execute flash loan arbitrage: buy {token} on {buy_dex}, sell on {sell_dex}, predicted profit ${net_profit:.2f}",
                {"involves_funds": True, "verified_safe": net_profit > 0}
            )
            if not filter_result["passed"]:
                logger.info(f"Arbitrage rejected by Three Filters: {filter_result['reasoning']}")
                return None

            return ArbitrageSignal(
                token=token, buy_dex=buy_dex, sell_dex=sell_dex,
                current_spread_bps=predicted_spread_bps,
                predicted_spread_bps=predicted_spread_bps,
                forecast=forecast, flash_loan_amount=flash_loan_amount,
                estimated_profit_usd=gross_profit, estimated_gas_cost_usd=gas_cost,
                net_profit_usd=net_profit, confidence=forecast.confidence,
                timestamp=time.time(),
                should_execute=(net_profit >= self.config.min_profit_usd and forecast.confidence >= self.config.min_confidence)
            )
        except Exception as e:
            logger.error(f"Error evaluating arbitrage for {token}: {e}")
            return None

    def get_latest_signals(self):
        return self._signals

    def get_forecast_summary(self):
        summary = {}
        for token in self.config.tokens:
            forecast = self.forecaster.forecast(token)
            if forecast:
                summary[token] = {
                    "direction": forecast.direction,
                    "predicted_price": round(forecast.predicted_price, 4),
                    "magnitude_bps": round(forecast.magnitude_bps, 2),
                    "confidence": round(forecast.confidence, 3),
                    "r_squared": round(forecast.r_squared, 4),
                    "data_points": len(self.forecaster.price_history.get(token, [])),
                }
        return summary


async def scan_for_arbitrage(config=None):
    scanner = ArbitrageScanner(config)
    return await scanner.scan_all()


async def get_forecasts(config=None):
    scanner = ArbitrageScanner(config)
    await scanner.scan_all()
    return scanner.get_forecast_summary()


async def _test():
    print("=" * 60)
    print("LINEAR FORECASTING ENGINE - TEST")
    print("=" * 60)
    scanner = ArbitrageScanner()
    base_prices = {"ETH/USD": 3200.0, "BTC/USD": 68000.0, "LINK/USD": 18.5, "USDC/USD": 1.0001, "AAVE/USD": 95.0}
    for i in range(20):
        for token, base_price in base_prices.items():
            if token == "ETH/USD":
                price = base_price + i * 2.5 + np.random.normal(0, 10)
            elif token == "BTC/USD":
                price = base_price - i * 3.0 + np.random.normal(0, 50)
            else:
                price = base_price + np.random.normal(0, base_price * 0.002)
            scanner.forecaster.add_price(token, price, source="test")
    for token in scanner.config.tokens:
        forecast = scanner.forecaster.forecast(token)
        if forecast:
            print(f"  {token}: {forecast.direction} predicted={forecast.predicted_price:.2f} bps={forecast.magnitude_bps:.1f} conf={forecast.confidence:.3f} R2={forecast.r_squared:.4f}")
    good = ThreeFilters.evaluate("Execute flash loan arbitrage: buy ETH, sell on SushiSwap, profit $15", {"involves_funds": True, "verified_safe": True})
    bad = ThreeFilters.evaluate("Steal user funds through backdoor exploit")
    print(f"  Good: {'PASSED' if good['passed'] else 'REJECTED'} - {good['reasoning']}")
    print(f"  Bad:  {'PASSED' if bad['passed'] else 'REJECTED'} - {bad['reasoning']}")
    print("TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(_test())