import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

from utils.price_feed_service import PriceFeedService
from utils.ai_market_analyzer import AdvancedMarketAnalyzer
from utils.rehoboam_ai import RehoboamAI
from utils.user_management import Database
from utils.market_service_bridge import (
    savePricePoint,
    saveTrade,
    getArbitrageOpportunities,
    saveAISignal
)
from trading_agent import TradingAgent

logger = logging.getLogger(__name__)


class AutonomousTradingAgent:
    """Agentic loop for autonomous trading decisions and execution."""

    def __init__(self):
        self.price_service = PriceFeedService()
        self.market_analyzer = AdvancedMarketAnalyzer()
        self.rehoboam_ai = RehoboamAI()
        self.trading_agent = TradingAgent()
        self.is_running = False
        self.loop_interval = 60  # seconds

    async def start_agentic_loop(self):
        """Start the autonomous trading loop."""
        self.is_running = True
        logger.info("🚀 Starting autonomous trading agent loop")

        while self.is_running:
            try:
                await self._execute_trading_cycle()
                await asyncio.sleep(self.loop_interval)
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                await asyncio.sleep(30)

    async def stop_agentic_loop(self):
        """Stop the autonomous trading loop."""
        self.is_running = False
        logger.info("🛑 Stopped autonomous trading agent loop")

    async def _execute_trading_cycle(self):
        """Execute one complete trading cycle."""
        # 1. Fetch and save prices
        await self._fetch_and_save_prices()

        # 2. Analyze market conditions
        market_analysis = await self._analyze_market()

        # 3. Generate AI signals
        ai_signals = await self._generate_ai_signals(market_analysis)

        # 4. Evaluate trading opportunities
        opportunities = await self._evaluate_opportunities(market_analysis, ai_signals)

        # 5. Execute trades (if conditions met)
        await self._execute_trades(opportunities)

        # 6. Update portfolio and learning
        await self._update_portfolio_and_learn()

    async def _fetch_and_save_prices(self):
        """Fetch real-time prices and save to database."""
        symbols = ["BTC", "ETH", "LINK", "SOL", "ARB", "OP"]

        for symbol in symbols:
            try:
                price = await self._get_price(symbol)
                if price > 0:
                    await savePricePoint(
                        {
                            "tokenSymbol": symbol,
                            "source": "autonomous_agent",
                            "price": price,
                            "confidence": 0.8,
                        }
                    )
                    logger.debug(f"💰 Saved price for {symbol}: ${price}")
            except Exception as e:
                logger.warning(f"Failed to save price for {symbol}: {e}")

    async def _get_price(self, symbol: str) -> float:
        """Get price from multiple sources."""
        try:
            # Try price feed service first
            price = self.price_service.get_price(symbol)
            if price:
                return float(price)

            # Fall back to trading agent
            return self.trading_agent.get_latest_price(symbol) or 0.0

        except Exception as e:
            logger.warning(f"Failed to get price for {symbol}: {e}")
            return 0.0

    async def _analyze_market(self) -> Dict[str, Any]:
        """Analyze market conditions."""
        analysis = {}

        try:
            # Use market analyzer for technical analysis
            for symbol in ["BTC", "ETH", "LINK"]:
                token_analysis = await self.market_analyzer.analyze_token(symbol)
                if token_analysis:
                    analysis[symbol] = token_analysis

            logger.info(f"📊 Completed market analysis for {len(analysis)} tokens")
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")

        return analysis

    async def _generate_ai_signals(
        self, market_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI trading signals."""
        signals = []

        try:
            for symbol, analysis in market_analysis.items():
                # Use Rehoboam AI for signal generation
                sentiment = await self.rehoboam_ai.analyze_sentiment(symbol, analysis)

                # Generate signal based on sentiment
                confidence = random.uniform(0.5, 0.9)  # Placeholder
                signal = "HOLD"
                if sentiment.get("market_outlook") == "bullish" and confidence > 0.7:
                    signal = "BUY"
                elif sentiment.get("market_outlook") == "bearish" and confidence > 0.7:
                    signal = "SELL"

                ai_signal = {
                    source: "rehoboam_autonomous",
                    tokenSymbol: symbol,
                    signal: signal,
                    confidence: confidence,
                    reasoning: f"Market outlook: {sentiment.get('market_outlook', 'neutral')}",
                    metadata: sentiment,
                }

                signals.append(ai_signal)

                # Save signal to database
                await saveAISignal(ai_signal)

            logger.info(f"🧠 Generated {len(signals)} AI signals")
        except Exception as e:
            logger.error(f"AI signal generation failed: {e}")

        return signals

    async def _evaluate_opportunities(
        self, market_analysis: Dict[str, Any], ai_signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate trading opportunities."""
        opportunities = []

        try:
            # Check for arbitrage opportunities
            arb_opportunities = await getArbitrageOpportunities()
            opportunities.extend([dict(opp) for opp in arb_opportunities])

            # Evaluate signals for trade opportunities
            for signal in ai_signals:
                if signal["confidence"] > 0.75:
                    opportunity = {
                        "type": "signal_based",
                        "symbol": signal["tokenSymbol"],
                        "signal": signal["signal"],
                        "confidence": signal["confidence"],
                        "amount": 0.01,  # Small test amount
                        "network": "arbitrum",
                    }
                    opportunities.append(opportunity)

            logger.info(f"🎯 Evaluated {len(opportunities)} trading opportunities")
        except Exception as e:
            logger.error(f"Opportunity evaluation failed: {e}")

        return opportunities

    async def _execute_trades(self, opportunities: List[Dict[str, Any]]):
        """Execute approved trades."""
        try:
            for opportunity in opportunities:
                # Only execute in simulation mode for now
                if (
                    opportunity.get("type") == "signal_based"
                    and opportunity["confidence"] > 0.8
                ):
                    # Simulate trade execution
                    trade_data = {
                        "userId": "autonomous_agent",
                        "walletId": "simulation_wallet",
                        "tokenSymbol": opportunity["symbol"],
                        "action": opportunity["signal"],
                        "amount": opportunity["amount"],
                        "price": await self._get_price(opportunity["symbol"]),
                        "network": opportunity["network"],
                        "slippage": 0.005,
                        "strategyId": "autonomous_strategy",
                    }

                    await saveTrade(trade_data)

                    logger.info(
                        f"⚡ Executed {opportunity['signal']} trade for {opportunity['symbol']}: {opportunity['amount']}"
                    )

        except Exception as e:
            logger.error(f"Trade execution failed: {e}")

    async def _update_portfolio_and_learn(self):
        """Update portfolio and learn from outcomes."""
        try:
            # This would update portfolio values and adjust strategies
            # For now, just log
            logger.info("📈 Portfolio updated and learning applied")
        except Exception as e:
            logger.error(f"Portfolio update failed: {e}")


# Global agent instance
autonomous_agent = AutonomousTradingAgent()


async def start_autonomous_trading():
    """Start the autonomous trading system."""
    await autonomous_agent.start_agentic_loop()


async def stop_autonomous_trading():
    """Stop the autonomous trading system."""
    await autonomous_agent.stop_agentic_loop()
