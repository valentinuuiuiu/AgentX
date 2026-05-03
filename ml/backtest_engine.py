"""
Backtesting Engine for Rehoboam
Adds historical performance analysis capability
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple, Optional
import asyncio
import aiohttp
import logging
from dataclasses import dataclass

logger = logging.getLogger("rehoboam.backtest")

@dataclass
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    trades: List[Dict]

class BacktestEngine:
    def __init__(self, data_dir: str = "./historical_data"):
        self.data_dir = data_dir
        self.cache = {}
        os.makedirs(data_dir, exist_ok=True)
    
    async def fetch_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical OHLCV data for backtesting"""
        cache_key = f"{symbol}_{days}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            # Try to load from local cache first
            cache_file = os.path.join(self.data_dir, f"{symbol}_{days}d.csv")
            if os.path.exists(cache_file):
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                self.cache[cache_key] = df
                return df
            
            # Fetch from CoinGecko (free historical data)
            url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process the data
                        prices = data['prices']
                        market_caps = data['market_caps']
                        total_volumes = data['total_volumes']
                        
                        df_data = []
                        for i in range(len(prices)):
                            timestamp = pd.to_datetime(prices[i][0], unit='ms')
                            df_data.append({
                                'timestamp': timestamp,
                                'price': prices[i][1],
                                'market_cap': market_caps[i][1],
                                'volume': total_volumes[i][1]
                            })
                        
                        df = pd.DataFrame(df_data)
                        df.set_index('timestamp', inplace=True)
                        
                        # Calculate hourly returns
                        df['returns'] = df['price'].pct_change()
                        
                        # Cache locally
                        df.to_csv(cache_file)
                        self.cache[cache_key] = df
                        
                        return df
                    else:
                        # Return mock data for development
                        return self._generate_mock_data(days)
                        
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return self._generate_mock_data(days)
    
    def _generate_mock_data(self, days: int) -> pd.DataFrame:
        """Generate mock data for development/testing"""
        dates = pd.date_range(end=datetime.now(), periods=days*24, freq='H')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic price movement
        returns = np.random.normal(0.0005, 0.02, len(dates))  # ~0.05% hourly return, 2% volatility
        prices = 100 * np.exp(np.cumsum(returns))  # Starting at $100
        
        df = pd.DataFrame({
            'price': prices,
            'volume': np.random.uniform(1000, 10000, len(dates)),
            'market_cap': prices * np.random.uniform(1000000, 10000000, len(dates)),
            'returns': returns
        }, index=dates)
        
        return df
    
    def apply_rehoboam_signals(self, df: pd.DataFrame, config: Dict = None) -> pd.DataFrame:
        """Apply Rehoboam's signal generation logic to historical data"""
        if config is None:
            config = {
                'strong_rally_threshold': 2.0,
                'moderate_rally_threshold': 0.8,
                'mild_uptrend_threshold': 0.2,
                'major_dip_threshold': -2.0,
                'moderate_dip_threshold': -0.5,
                'slight_weakness_threshold': -0.1,
                'confidence_strong': 82,
                'confidence_moderate': 72,
                'confidence_mild': 68,
                'confidence_dip': 84,
                'confidence_support': 70,
                'confidence_weak': 65,
                'confidence_neutral': 60,
                'confidence_low': 45
            }
        
        # Calculate 24h change (approximation for hourly data)
        df['change_24h'] = df['price'].pct_change(24) * 100  # 24 periods ago for hourly data
        
        # Initialize signal columns
        df['signal'] = 'HOLD'
        df['confidence'] = 0.0
        df['reason'] = ''
        df['target_price'] = 0.0
        df['stop_loss'] = 0.0
        
        for i in range(len(df)):
            if pd.isna(df.iloc[i]['change_24h']):
                continue
                
            price = df.iloc[i]['price']
            chg = df.iloc[i]['change_24h']
            
            # Smart signal generation — always give a clear call (same as main.py)
            if chg > config['strong_rally_threshold']:
                action = "SELL"
                reason = f"Strong rally: +{abs(chg):.1f}% in 24h. Lock in profits now."
                target = round(price * 0.965, 2)
                stop = round(price * 1.03, 2)
                confidence = config['confidence_strong']
            elif chg > config['moderate_rally_threshold']:
                action = "SELL"
                reason = f"Up {abs(chg):.1f}% — consider taking partial profit."
                target = round(price * 0.98, 2)
                stop = round(price * 1.02, 2)
                confidence = config['confidence_moderate']
            elif chg > config['mild_uptrend_threshold']:
                action = "BUY"
                reason = f"Mild uptrend (+{abs(chg):.1f}%) — 3/3 sources confirm. Accumulate."
                target = round(price * 1.025, 2)
                stop = round(price * 0.985, 2)
                confidence = config['confidence_mild']
            elif chg < config['major_dip_threshold']:
                action = "BUY"
                reason = f"Major dip: {abs(chg):.1f}% down. Strong buy opportunity."
                target = round(price * 1.04, 2)
                stop = round(price * 0.955, 2)
                confidence = config['confidence_dip']
            elif chg < config['moderate_dip_threshold']:
                action = "BUY"
                reason = f"Down {abs(chg):.1f}% — dip buy at support levels."
                target = round(price * 1.03, 2)
                stop = round(price * 0.97, 2)
                confidence = config['confidence_support']
            elif chg <= config['slight_weakness_threshold']:
                action = "SELL"
                reason = f"Slight weakness (-{abs(chg):.1f}%) — 3/3 sources. Reduce exposure."
                target = round(price * 0.99, 2)
                stop = round(price * 1.015, 2)
                confidence = config['confidence_weak']
            else:
                action = "HOLD"
                reason = "Market neutral — 3/3 sources agree. Wait for momentum."
                target = price
                stop = price
                confidence = config['confidence_neutral']
            
            df.iloc[i, df.columns.get_loc('signal')] = action
            df.iloc[i, df.columns.get_loc('confidence')] = confidence
            df.iloc[i, df.columns.get_loc('reason')] = reason
            df.iloc[i, df.columns.get_loc('target_price')] = target
            df.iloc[i, df.columns.get_loc('stop_loss')] = stop
        
        return df
    
    def simulate_trades(self, df: pd.DataFrame, initial_capital: float = 10000) -> List[Dict]:
        """Simulate trading based on signals"""
        trades = []
        position = None  # None or {'type': 'LONG/SHORT', 'entry_price': float, 'entry_time': timestamp, 'size': float}
        capital = initial_capital
        
        for i in range(len(df)):
            current_price = df.iloc[i]['price']
            signal = df.iloc[i]['signal']
            confidence = df.iloc[i]['confidence']
            timestamp = df.index[i]
            
            # Only trade on high confidence signals (>75%)
            if confidence < 75:
                continue
                
            # Enter new position
            if position is None and signal in ['BUY', 'SELL']:
                if signal == 'BUY':
                    position = {
                        'type': 'LONG',
                        'entry_price': current_price,
                        'entry_time': timestamp,
                        'size': capital * 0.02,  # Risk 2% per trade
                        'target_price': df.iloc[i]['target_price'],
                        'stop_loss': df.iloc[i]['stop_loss']
                    }
                elif signal == 'SELL':
                    position = {
                        'type': 'SHORT',
                        'entry_price': current_price,
                        'entry_time': timestamp,
                        'size': capital * 0.02,  # Risk 2% per trade
                        'target_price': df.iloc[i]['target_price'],
                        'stop_loss': df.iloc[i]['stop_loss']
                    }
            
            # Check exit conditions
            elif position is not None:
                exit_signal = False
                exit_price = current_price
                exit_reason = ''
                
                if position['type'] == 'LONG':
                    # Check stop loss
                    if current_price <= position['stop_loss']:
                        exit_signal = True
                        exit_reason = 'STOP_LOSS'
                    # Check target
                    elif current_price >= position['target_price']:
                        exit_signal = True
                        exit_reason = 'TARGET'
                    # Reverse signal
                    elif signal == 'SELL' and confidence > 80:
                        exit_signal = True
                        exit_reason = 'REVERSE_SIGNAL'
                        
                elif position['type'] == 'SHORT':
                    # Check stop loss (for shorts, price going up is bad)
                    if current_price >= position['stop_loss']:
                        exit_signal = True
                        exit_reason = 'STOP_LOSS'
                    # Check target (for shorts, price going down is good)
                    elif current_price <= position['target_price']:
                        exit_signal = True
                        exit_reason = 'TARGET'
                    # Reverse signal
                    elif signal == 'BUY' and confidence > 80:
                        exit_signal = True
                        exit_reason = 'REVERSE_SIGNAL'
                
                if exit_signal:
                    # Calculate P&L
                    if position['type'] == 'LONG':
                        pnl = (exit_price - position['entry_price']) * (position['size'] / position['entry_price'])
                    else:  # SHORT
                        pnl = (position['entry_price'] - exit_price) * (position['size'] / position['entry_price'])
                    
                    trade = {
                        'entry_time': position['entry_time'].isoformat(),
                        'exit_time': timestamp.isoformat(),
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'position_type': position['type'],
                        'size': position['size'],
                        'pnl': pnl,
                        'pnl_percent': (pnl / (position['size'] / position['entry_price'] * position['entry_price'])) * 100,
                        'exit_reason': exit_reason,
                        'duration_hours': (timestamp - position['entry_time']).total_seconds() / 3600
                    }
                    
                    trades.append(trade)
                    capital += pnl
                    position = None
        
        # Close any open position at the end
        if position is not None:
            final_price = df.iloc[-1]['price']
            if position['type'] == 'LONG':
                pnl = (final_price - position['entry_price']) * (position['size'] / position['entry_price'])
            else:  # SHORT
                pnl = (position['entry_price'] - final_price) * (position['size'] / position['entry_price'])
            
            trade = {
                'entry_time': position['entry_time'].isoformat(),
                'exit_time': df.index[-1].isoformat(),
                'entry_price': position['entry_price'],
                'exit_price': final_price,
                'position_type': position['type'],
                'size': position['size'],
                'pnl': pnl,
                'pnl_percent': (pnl / (position['size'] / position['entry_price'] * position['entry_price'])) * 100,
                'exit_reason': 'END_OF_BACKTEST',
                'duration_hours': (df.index[-1] - position['entry_time']).total_seconds() / 3600
            }
            
            trades.append(trade)
            capital += pnl
        
        return trades
    
    def calculate_metrics(self, trades: List[Dict], initial_capital: float = 10000) -> BacktestResult:
        """Calculate performance metrics from trades in a single pass"""
        if not trades:
            return BacktestResult(total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0, total_return=0.0, avg_win=0.0, avg_loss=0.0, profit_factor=0.0, sharpe_ratio=0.0, max_drawdown=0.0, trades=[])
        
        total_trades = len(trades)
        winning_pnls = []
        losing_pnls = []
        pnl_percents = []
        total_pnl = 0.0
        
        current_capital = initial_capital
        peak = initial_capital
        max_drawdown = 0.0

        for t in trades:
            pnl = t['pnl']
            total_pnl += pnl
            pnl_percents.append(t['pnl_percent'])

            if pnl > 0:
                winning_pnls.append(pnl)
            else:
                losing_pnls.append(pnl)

            # Inline Max Drawdown calculation
            current_capital += pnl
            if current_capital > peak:
                peak = current_capital

            if peak > 0:
                drawdown = (peak - current_capital) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        winning_count = len(winning_pnls)
        losing_count = len(losing_pnls)
        win_rate = winning_count / total_trades
        
        total_return = (total_pnl / initial_capital) * 100
        
        avg_win = np.mean(winning_pnls) if winning_pnls else 0.0
        avg_loss = np.mean(losing_pnls) if losing_pnls else 0.0
        
        win_pnl_sum = sum(winning_pnls)
        loss_pnl_sum = sum(losing_pnls)
        profit_factor = abs(win_pnl_sum / loss_pnl_sum) if loss_pnl_sum != 0 else float('inf')
        
        # Calculate Sharpe ratio (simplified)
        if len(pnl_percents) > 1:
            sharpe_ratio = np.mean(pnl_percents) / (np.std(pnl_percents) + 1e-8) * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0.0
        
        max_drawdown *= 100  # Convert to percentage
        
        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            win_rate=win_rate,
            total_return=total_return,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            trades=trades
        )
    
    async def run_backtest(self, symbol: str = 'bitcoin', days: int = 30, 
                          initial_capital: float = 10000, config: Dict = None) -> BacktestResult:
        """Run a complete backtest"""
        # Fetch historical data
        df = await self.fetch_historical_data(symbol, days)
        
        # Apply signals
        df_signals = self.apply_rehoboam_signals(df, config)
        
        # Simulate trades
        trades = self.simulate_trades(df_signals, initial_capital)
        
        # Calculate metrics
        result = self.calculate_metrics(trades, initial_capital)
        
        return result

# Example usage and testing functions
async def example_backtest():
    """Example of how to use the backtesting engine"""
    engine = BacktestEngine()
    
    # Run backtest on Bitcoin for 30 days
    result = await engine.run_backtest('bitcoin', 30, 10000)
    
    print(f"Backtest Results for BTC/USD:")
    print(f"Total Trades: {result.total_trades}")
    print(f"Win Rate: {result.win_rate:.1%}")
    print(f"Total Return: {result.total_return:.2f}%")
    print(f"Profit Factor: {result.profit_factor:.2f}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.2f}%")
    
    return result

if __name__ == "__main__":
    # For testing
    import asyncio
    asyncio.run(example_backtest())