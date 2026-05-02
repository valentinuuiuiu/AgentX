"""
Signal Database — Track every signal, measure accuracy, learn.
This is how we beat Freqtrade: by learning from our own history.
"""

import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DB_FILE = Path('/root/rehoboam-terminal/mandos_halls/signal_history.json')

class SignalDatabase:
    """Persistent signal tracking with accuracy measurement."""
    
    def __init__(self):
        self.signals: List[Dict] = []
        self._load()
    
    def _load(self):
        if DB_FILE.exists():
            try:
                with open(DB_FILE) as f:
                    data = json.load(f)
                    self.signals = data.get('signals', [])
            except:
                self.signals = []
    
    def _save(self):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DB_FILE, 'w') as f:
            json.dump({
                'signals': self.signals[-1000:],  # Keep last 1000
                'updated': datetime.now(timezone.utc).isoformat(),
                'total_recorded': len(self.signals)
            }, f, indent=2)
    
    def record(self, coin: str, action: str, confidence: float, price: float, 
               reason: str = "", sources: int = 0):
        """Record a new signal."""
        signal = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'coin': coin,
            'action': action,
            'confidence': confidence,
            'entry_price': price,
            'reason': reason,
            'sources': sources,
            'status': 'open',  # open / closed
            'exit_price': None,
            'pnl_pct': None,
            'hit_target': False,
            'hit_stop': False,
            'validated': False
        }
        self.signals.append(signal)
        self._save()
        return signal
    
    def validate_signal(self, coin: str, current_price: float):
        """Validate open signals against current price."""
        for sig in self.signals:
            if sig['coin'] == coin and sig['status'] == 'open':
                self._check_exit(sig, current_price)
        self._save()
    
    def _check_exit(self, sig: Dict, current_price: float):
        """Check if signal hit target or stop loss."""
        entry = sig['entry_price']
        if entry <= 0:
            return
        
        # Simple 3% target / 2% stop for demo
        target = entry * 1.03
        stop = entry * 0.98
        
        change_pct = (current_price - entry) / entry * 100
        
        if current_price >= target:
            sig['status'] = 'closed'
            sig['exit_price'] = current_price
            sig['pnl_pct'] = change_pct
            sig['hit_target'] = True
            sig['validated'] = True
        elif current_price <= stop:
            sig['status'] = 'closed'
            sig['exit_price'] = current_price
            sig['pnl_pct'] = change_pct
            sig['hit_stop'] = True
            sig['validated'] = True
    
    def get_stats(self) -> Dict:
        """Get signal accuracy statistics."""
        validated = [s for s in self.signals if s.get('validated')]
        if not validated:
            return {'total': len(self.signals), 'validated': 0, 'win_rate': 0}
        
        wins = len([s for s in validated if s.get('pnl_pct', 0) > 0])
        total_pnl = sum(s.get('pnl_pct', 0) for s in validated)
        
        by_coin = {}
        for s in validated:
            c = s['coin']
            if c not in by_coin:
                by_coin[c] = {'total': 0, 'wins': 0, 'pnl': 0}
            by_coin[c]['total'] += 1
            if s.get('pnl_pct', 0) > 0:
                by_coin[c]['wins'] += 1
            by_coin[c]['pnl'] += s.get('pnl_pct', 0)
        
        return {
            'total_signals': len(self.signals),
            'validated': len(validated),
            'win_rate': round(wins / len(validated) * 100, 1),
            'avg_pnl': round(total_pnl / len(validated), 2),
            'by_coin': {c: {
                'win_rate': round(v['wins']/v['total']*100, 1),
                'avg_pnl': round(v['pnl']/v['total'], 2)
            } for c, v in by_coin.items()}
        }
