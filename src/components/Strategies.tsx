import React, { useState, useEffect } from 'react';
import { Target, Users, Zap, Shield, Plus, TrendingUp, Settings, Activity, ArrowRightLeft, ArrowUpRight } from 'lucide-react';
import { toast } from 'sonner';

export function Strategies() {
  const [copyList, setCopyList] = useState([
    { id: 1, name: 'GCR.eth', address: '0x1A2b...4x9C', pnl: '+412.5%', active: true, winRate: '78%' },
    { id: 2, name: 'Smart Money 12', address: '0x992B...A12f', pnl: '+89.2%', active: true, winRate: '65%' },
    { id: 3, name: 'Wintermute OTC', address: '0xdbF...902a', pnl: '+124.8%', active: false, winRate: '92%' },
  ]);

  const [liveTrades, setLiveTrades] = useState([
    { id: 1, wallet: 'Smart Money 12', token: 'PEPE', action: 'BUY', amountUSD: 50000, ourAmountUSD: 50, status: 'Completed', time: Date.now() - 60000, txHash: '0x94...f1a2' },
    { id: 2, wallet: 'GCR.eth', token: 'WIF', action: 'SELL', amountUSD: 120000, ourAmountUSD: 120, status: 'Completed', time: Date.now() - 120000, txHash: '0x32...e81b' },
  ]);

  useEffect(() => {
    // Simulate incoming on-chain transactions from tracked wallets
    const interval = setInterval(() => {
      const activeWallets = copyList.filter(w => w.active);
      if (activeWallets.length === 0) return;

      const randomWallet = activeWallets[Math.floor(Math.random() * activeWallets.length)];
      const tokens = ['DOGE', 'SHIB', 'RNDR', 'FET', 'TAO', 'PENDLE'];
      const randomToken = tokens[Math.floor(Math.random() * tokens.length)];
      const isBuy = Math.random() > 0.5;
      const whaleAmount = Math.floor(Math.random() * 200000) + 10000;
      
      // We replicate with a fraction (e.g., 0.1%)
      const copyMultiplier = 0.001; 
      const ourAmount = parseFloat((whaleAmount * copyMultiplier).toFixed(2));

      const newTrade = {
        id: Date.now(),
        wallet: randomWallet.name,
        token: randomToken,
        action: isBuy ? 'BUY' : 'SELL',
        amountUSD: whaleAmount,
        ourAmountUSD: ourAmount,
        status: 'Completed',
        time: Date.now(),
        txHash: `0x${Math.random().toString(16).slice(2, 10)}...${Math.random().toString(16).slice(2, 6)}`
      };

      setLiveTrades(prev => [newTrade, ...prev].slice(0, 10)); // Keep last 10
      toast(`[Copy Trade] Replicated ${newTrade.action} ${newTrade.token} from ${newTrade.wallet} ($${newTrade.ourAmountUSD})`, {
        icon: <ArrowRightLeft className="w-4 h-4 text-indigo-400" />
      });
    }, 15000); // New trade every 15 seconds

    return () => clearInterval(interval);
  }, [copyList]);

  const toggleCopy = (id: number) => {
    setCopyList(list => list.map(item => {
      if (item.id === id) {
        toast.success(`Copy trading for ${item.name} ${!item.active ? 'enabled' : 'disabled'}`);
        return { ...item, active: !item.active };
      }
      return item;
    }));
  };

  const formatTime = (ts: number) => {
    const diff = Math.floor((Date.now() - ts) / 1000);
    if (diff < 60) return `${diff}s ago`;
    return `${Math.floor(diff / 60)}m ago`;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Target className="w-6 h-6 text-emerald-400" />
          Trade Strategies & Risk
        </h2>
        <p className="text-slate-400">Configure On-Chain Sniping, Copy Trading, and Global Risk Parameters.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Copy Trading Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold flex items-center gap-2 text-slate-200">
              <Users className="w-5 h-5 text-indigo-400" />
              Copy Trading Router
            </h3>
            <button className="bg-indigo-500/20 text-indigo-400 px-3 py-1 rounded text-sm font-semibold flex items-center gap-1 hover:bg-indigo-500/30 transition-colors">
              <Plus className="w-4 h-4" /> Add Wallet
            </button>
          </div>

          <div className="space-y-3">
            {copyList.map(wallet => (
              <div key={wallet.id} className="bg-slate-950 border border-slate-800 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <div className="font-bold text-slate-200">{wallet.name}</div>
                  <div className="text-xs text-slate-500 font-mono mt-1">{wallet.address}</div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-emerald-400 font-bold font-mono text-sm">{wallet.pnl}</div>
                    <div className="text-slate-500 text-[10px] uppercase tracking-wider">WR: {wallet.winRate}</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" checked={wallet.active} onChange={() => toggleCopy(wallet.id)} />
                    <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-500"></div>
                  </label>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 text-xs text-slate-500 border-t border-slate-800 pt-3">
            <Zap className="w-3 h-3 inline mr-1 text-amber-400"/>
            Replicating trades with a 0.1% scaling factor.
          </div>
        </div>

        {/* Live Replications Feed */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg row-span-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold flex items-center gap-2 text-slate-200">
              <Activity className="w-5 h-5 text-cyan-400" />
              Live Copy Execution
            </h3>
            <span className="px-2 py-1 text-[10px] uppercase font-bold tracking-widest bg-cyan-500/10 text-cyan-400 rounded border border-cyan-500/20 shadow-[0_0_10px_rgba(34,211,238,0.2)]">Monitoring</span>
          </div>

          <div className="space-y-3 font-mono">
            {liveTrades.map(trade => (
              <div key={trade.id} className="relative bg-[#0a0a14] border border-[#1a1a2e] p-4 rounded-xl overflow-hidden group">
                <div className={`absolute top-0 left-0 w-1 h-full ${trade.action === 'BUY' ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded textxs font-bold ${trade.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                      {trade.action}
                    </span>
                    <span className="text-slate-200 font-bold">{trade.token}</span>
                  </div>
                  <span className="text-xs text-slate-500">{formatTime(trade.time)}</span>
                </div>
                
                <div className="text-xs text-slate-400 mb-2">
                  Target <span className="text-indigo-400">{trade.wallet}</span> executed ${trade.amountUSD.toLocaleString()}
                </div>
                
                <div className="flex justify-between items-end border-t border-slate-800/50 pt-2 mt-2">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-0.5">Our Replicated Trade</div>
                    <div className="text-slate-200 font-bold text-sm text-cyan-400">${trade.ourAmountUSD.toLocaleString()}</div>
                  </div>
                  <div className="text-[10px] text-slate-500 hover:text-cyan-400 flex items-center gap-1 cursor-pointer transition-colors">
                    Tx: {trade.txHash} <ArrowUpRight className="w-3 h-3" />
                  </div>
                </div>
              </div>
            ))}
            {liveTrades.length === 0 && (
              <div className="text-center py-10 text-slate-500 text-sm animate-pulse">
                Awaiting targets to execute trades...
              </div>
            )}
          </div>
        </div>

        {/* Global Risk Management */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold flex items-center gap-2 text-slate-200">
              <Shield className="w-5 h-5 text-rose-400" />
              Global Risk Architecture
            </h3>
            <Settings className="w-5 h-5 text-slate-500 cursor-pointer hover:text-slate-300" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Max Daily Drawdown</div>
              <div className="text-2xl font-bold text-rose-400 font-mono">-5.00%</div>
              <div className="mt-2 w-full bg-slate-800 rounded-full h-1">
                 <div className="bg-rose-500 h-1 rounded-full w-[25%] relative">
                    <span className="absolute -right-1 -top-1 w-3 h-3 bg-rose-400 rounded-full shadow-[0_0_10px_rgba(244,63,94,0.8)]"></span>
                 </div>
              </div>
              <div className="text-[10px] font-mono text-slate-500 mt-2">Current DD: -1.25%</div>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Take Profit Tiers</div>
              <div className="text-2xl font-bold text-emerald-400 font-mono flex items-center gap-2">
                 <TrendingUp className="w-5 h-5" /> 50/30/20
              </div>
              <div className="mt-2 text-[10px] font-mono text-slate-400">
                 Sells 50% at 2x, 30% at 5x, leaves 20% moonbag.
              </div>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Honeypot Filter</div>
              <div className="flex items-center gap-2 mt-2">
                 <Shield className="w-8 h-8 text-indigo-400" />
                 <div>
                   <div className="font-bold text-indigo-400 text-sm">Cipher-Q Auditing</div>
                   <div className="text-[10px] text-slate-500">Requires score &gt; 70 to trade</div>
                 </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
