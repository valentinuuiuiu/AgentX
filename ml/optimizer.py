"""
Parameter Optimization Engine for Rehoboam
Adds hyperparameter optimization capability similar to Freqtrade's Hyperopt
"""

import pandas as pd
import numpy as np
import json
import itertools
from typing import Dict, List, Tuple, Any, Optional
import asyncio
from ml.backtest_engine import BacktestEngine, BacktestResult

class ParameterOptimizer:
    def __init__(self, backtest_engine: BacktestEngine = None):
        self.backtest_engine = backtest_engine or BacktestEngine()
        self.optimization_history = []
    
    def get_parameter_space(self) -> Dict[str, List[Any]]:
        """Define the parameter space for optimization"""
        return {
            # Signal thresholds (percentage changes)
            'strong_rally_threshold': [1.0, 1.5, 2.0, 2.5, 3.0],
            'moderate_rally_threshold': [0.5, 0.8, 1.0, 1.2],
            'mild_uptrend_threshold': [0.1, 0.2, 0.3, 0.5],
            'major_dip_threshold': [-1.0, -1.5, -2.0, -2.5, -3.0],
            'moderate_dip_threshold': [-0.3, -0.5, -0.7, -1.0],
            'slight_weakness_threshold': [-0.05, -0.1, -0.15, -0.2],
            
            # Confidence levels
            'confidence_strong': [75, 80, 82, 85, 90],
            'confidence_moderate': [65, 70, 72, 75, 80],
            'confidence_mild': [60, 65, 68, 70, 75],
            'confidence_dip': [75, 80, 82, 85, 90],
            'confidence_support': [65, 68, 70, 75, 80],
            'confidence_weak': [60, 63, 65, 68, 70],
            'confidence_neutral': [50, 55, 60, 65, 70],
            'confidence_low': [35, 40, 45, 50, 55]
        }
    
    def generate_parameter_combinations(self, max_combinations: int = 50) -> List[Dict]:
        """Generate parameter combinations for testing"""
        param_space = self.get_parameter_space()
        
        # Get all parameter names and their possible values
        param_names = list(param_space.keys())
        param_values = list(param_space.values())
        
        # Generate all combinations (cartesian product)
        all_combinations = list(itertools.product(*param_values))
        
        # Limit to max_combinations if there are too many
        if len(all_combinations) > max_combinations:
            # Sample evenly across the space
            indices = np.linspace(0, len(all_combinations)-1, max_combinations, dtype=int)
            selected_combinations = [all_combinations[i] for i in indices]
        else:
            selected_combinations = all_combinations
        
        # Convert to list of dictionaries
        parameter_sets = []
        for combination in selected_combinations:
            param_dict = dict(zip(param_names, combination))
            parameter_sets.append(param_dict)
        
        return parameter_sets
    
    async def optimize_parameters(self, symbol: str = 'bitcoin', days: int = 30,
                                initial_capital: float = 10000,
                                max_combinations: int = 30,
                                optimize_for: str = 'profit_factor') -> Dict:
        """Run parameter optimization"""
        print(f"Starting parameter optimization for {symbol} over {days} days...")
        print(f"Testing {max_combinations} parameter combinations, optimizing for {optimize_for}")
        
        # Generate parameter combinations
        param_combinations = self.generate_parameter_combinations(max_combinations)
        
        results = []
        best_result = None
        best_params = None
        best_score = float('-inf')
        
        # Test each parameter combination
        for i, params in enumerate(param_combinations):
            print(f"Testing combination {i+1}/{len(param_combinations)}: {params}")
            
            try:
                # Run backtest with current parameters
                backtest_result = await self.backtest_engine.run_backtest(
                    symbol=symbol,
                    days=days,
                    initial_capital=initial_capital,
                    config=params
                )
                
                # Calculate score based on optimization metric
                score = self._calculate_score(backtest_result, optimize_for)
                
                # Store result
                result_record = {
                    'parameters': params.copy(),
                    'backtest_result': {
                        'total_trades': backtest_result.total_trades,
                        'win_rate': backtest_result.win_rate,
                        'total_return': backtest_result.total_return,
                        'profit_factor': backtest_result.profit_factor,
                        'sharpe_ratio': backtest_result.sharpe_ratio,
                        'max_drawdown': backtest_result.max_drawdown
                    },
                    'score': score
                }
                
                results.append(result_record)
                
                # Update best result
                if score > best_score:
                    best_score = score
                    best_result = backtest_result
                    best_params = params.copy()
                    print(f"  New best score: {best_score:.4f}")
                
            except Exception as e:
                print(f"  Error testing parameters: {e}")
                continue
        
        # Sort results by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Prepare final result
        optimization_result = {
            'symbol': symbol,
            'days': days,
            'initial_capital': initial_capital,
            'optimize_for': optimize_for,
            'total_combinations_tested': len(results),
            'best_parameters': best_params,
            'best_result': {
                'total_trades': best_result.total_trades if best_result else 0,
                'win_rate': best_result.win_rate if best_result else 0,
                'total_return': best_result.total_return if best_result else 0,
                'profit_factor': best_result.profit_factor if best_result else 0,
                'sharpe_ratio': best_result.sharpe_ratio if best_result else 0,
                'max_drawdown': best_result.max_drawdown if best_result else 0
            } if best_result else None,
            'top_5_results': results[:5],
            'optimization_history': results
        }
        
        return optimization_result
    
    def _calculate_score(self, backtest_result: BacktestResult, metric: str) -> float:
        """Calculate optimization score based on selected metric"""
        if metric == 'profit_factor':
            # Profit factor, but penalize too few trades
            pf = backtest_result.profit_factor if backtest_result.profit_factor != float('inf') else 10.0
            trade_penalty = max(0, 1 - (backtest_result.total_trades / 20))  # Penalty if < 20 trades
            return pf * (1 - trade_penalty * 0.5)
        
        elif metric == 'sharpe_ratio':
            # Sharpe ratio, but require minimum win rate
            sr = backtest_result.sharpe_ratio
            wr_bonus = min(0.2, backtest_result.win_rate * 0.3)  # Bonus for good win rate
            trade_penalty = max(0, 1 - (backtest_result.total_trades / 15))  # Penalty if too few trades
            return (sr + wr_bonus) * (1 - trade_penalty * 0.3)
        
        elif metric == 'total_return':
            # Total return, but penalize high drawdown
            tr = backtest_result.total_return
            dd_penalty = min(0.5, backtest_result.max_drawdown / 100)  # Penalty for drawdown
            trade_penalty = max(0, 1 - (backtest_result.total_trades / 10))  # Penalty if too few trades
            return tr * (1 - dd_penalty) * (1 - trade_penalty * 0.5)
        
        elif metric == 'win_rate':
            # Win rate, but require minimum profit factor
            wr = backtest_result.win_rate
            pf_bonus = min(0.3, (backtest_result.profit_factor - 1) * 0.2) if backtest_result.profit_factor > 1 else 0
            trade_penalty = max(0, 1 - (backtest_result.total_trades / 10))  # Penalty if too few trades
            return (wr + pf_bonus) * (1 - trade_penalty * 0.5)
        
        elif metric == 'calmar_ratio':
            # Calmar ratio (return / max drawdown)
            if backtest_result.max_drawdown > 0:
                calmar = backtest_result.total_return / backtest_result.max_drawdown
            else:
                calmar = backtest_result.total_return * 10  # High reward if no drawdown
            
            trade_penalty = max(0, 1 - (backtest_result.total_trades / 15))  # Penalty if too few trades
            return calmar * (1 - trade_penalty * 0.3)
        
        else:
            # Default to profit factor
            return self._calculate_score(backtest_result, 'profit_factor')
    
    def save_optimization_results(self, results: Dict, filename: str = "optimization_results.json"):
        """Save optimization results to file"""
        # Convert numpy types to JSON-serializable types
        def convert_for_json(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_for_json(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_for_json(results)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Optimization results saved to {filename}")
    
    def load_optimization_results(self, filename: str = "optimization_results.json") -> Dict:
        """Load optimization results from file"""
        try:
            with open(filename, 'r') as f:
                results = json.load(f)
            print(f"Optimization results loaded from {filename}")
            return results
        except FileNotFoundError:
            print(f"No optimization results file found at {filename}")
            return {}
        except Exception as e:
            print(f"Error loading optimization results: {e}")
            return {}

# Example usage
async def example_optimization():
    """Example of how to use the parameter optimizer"""
    optimizer = ParameterOptimizer()
    
    # Run optimization
    results = await optimizer.optimize_parameters(
        symbol='bitcoin',
        days=14,  # Shorter period for faster testing
        initial_capital=10000,
        max_combinations=20,
        optimize_for='profit_factor'
    )
    
    # Save results
    optimizer.save_optimization_results(results, "btc_optimization.json")
    
    # Print summary
    if results['best_parameters']:
        print("\n=== OPTIMIZATION RESULTS ===")
        print(f"Best Parameters: {results['best_parameters']}")
        print(f"Best Profit Factor: {results['best_result']['profit_factor']:.2f}")
        print(f"Best Win Rate: {results['best_result']['win_rate']:.1%}")
        print(f"Best Total Return: {results['best_result']['total_return']:.2f}%")
        print(f"Best Sharpe Ratio: {results['best_result']['sharpe_ratio']:.2f}")
        print(f"Best Max Drawdown: {results['best_result']['max_drawdown']:.2f}%")
    
    return results

if __name__ == "__main__":
    # For testing
    import asyncio
    asyncio.run(example_optimization())