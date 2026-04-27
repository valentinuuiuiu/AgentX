import React, { useState, useEffect } from 'react';
import { Radar, Flame, Droplet, Clock, ArrowUpRight, Compass, ShieldAlert } from 'lucide-react';
import { toast } from 'sonner';

export function AlphaIntel() {
  const [intel, setIntel] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIntel = async () => {
      try {
        const response = await fetch('/api/intel');
        const data = await response.json();
        setIntel(data);
      } catch (error) {
        console.error('Failed to fetch intel:', error);
        toast.error('Data stream interrupted. Retrying connection...');
      } finally {
        setLoading(false);
      }
    };
    
    fetchIntel();
    const interval = setInterval(fetchIntel, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !intel) {
    return (
      <div className="flex items-center justify-center h-full text-purple-400 font-mono text-sm">
        <Radar className="w-5 h-5 animate-spin mr-3" />
        INITIALIZING DEEP SCANS...
      </div>
    );
  }

  const fgValue = parseInt(intel.fg.value);
  const fgColor = fgValue > 70 ? 'text-emerald-400' : fgValue > 55 ? 'text-emerald-500' : fgValue < 30 ? 'text-red-500' : fgValue < 45 ? 'text-orange-400' : 'text-blue-400';
  const fgBgColor = fgValue > 70 ? 'bg-emerald-500' : fgValue > 55 ? 'bg-emerald-500' : fgValue < 30 ? 'bg-red-500' : fgValue < 45 ? 'bg-orange-400' : 'bg-blue-400';

  return (
    <div className="space-y-6 max-w-6xl text-slate-200">
      <div className="flex flex-col md:flex-row justify-between gap-4 border-b border-purple-900/30 pb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 mb-2 text-purple-400">
            <Radar className="w-6 h-6 text-purple-500" />
            Alpha Intel & Plugins
          </h1>
          <p className="text-slate-400 text-sm">
            Live unadulterated web data integrating alternative metrics, on-chain yields, and shifting global sentience. Powered by DefiLlama, Alternative.me, & CoinGecko.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Panel 1: Multi-Agent Sentiment & Fear & Greed */}
        <div className="bg-[#050505] border border-[#1a1a2e] rounded-xl p-6 relative overflow-hidden shadow-[0_0_15px_rgba(139,92,246,0.05)]">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Compass className="w-24 h-24 text-purple-600" />
          </div>
          <h2 className="text-lg font-bold flex items-center gap-2 text-slate-300 mb-6">
            <ShieldAlert className="w-5 h-5 text-purple-400" />
            Global Fear & Greed
          </h2>
          
          <div className="flex flex-col items-center justify-center py-6">
            <div className="relative flex items-center justify-center w-40 h-40 rounded-full border-[4px] border-slate-900 shadow-inner mb-4">
              <svg className="w-full h-full rotate-180 absolute" viewBox="0 0 36 36">
                <path
                  className="text-slate-800"
                  strokeWidth="3"
                  stroke="currentColor"
                  fill="none"
                  strokeDasharray="50, 100"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={fgColor}
                  strokeWidth="3"
                  strokeDasharray={`${fgValue / 2}, 100`}
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute flex flex-col items-center pb-2">
                <span className={`text-5xl font-black ${fgColor}`}>{fgValue}</span>
                <span className="text-xs tracking-widest text-slate-500 uppercase mt-1">{intel.fg.value_classification}</span>
              </div>
            </div>
          </div>
          <div className="text-center text-xs text-slate-500">Live sentiment extraction from API endpoints.</div>
        </div>

        {/* Panel 2: On-Chain Yield Radar */}
        <div className="lg:col-span-2 bg-[#050505] border border-[#1a1a2e] rounded-xl p-6 shadow-[0_0_15px_rgba(139,92,246,0.05)]">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold flex items-center gap-2 text-slate-300">
              <Droplet className="w-5 h-5 text-blue-400" />
              Dark Pool Yields (DefiLlama)
            </h2>
            <span className="px-2 py-1 text-[10px] uppercase font-bold tracking-widest bg-blue-500/10 text-blue-400 rounded border border-blue-500/20">Live</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#0a0a14] text-slate-400 text-xs uppercase tracking-wider border-b border-[#1a1a2e]">
                <tr>
                  <th className="px-4 py-3 font-medium">Protocol / Pool</th>
                  <th className="px-4 py-3 font-medium">Chain</th>
                  <th className="px-4 py-3 font-medium text-right">TVL</th>
                  <th className="px-4 py-3 font-medium text-right">Base APY</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a2e]">
                {intel.yields.map((pool: any, i: number) => (
                  <tr key={i} className="hover:bg-blue-900/5 transition-colors group">
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-200">{pool.project}</div>
                      <div className="text-xs text-slate-500 font-mono mt-0.5">{pool.symbol}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                        {pool.chain}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-400">
                      ${(pool.tvlUsd / 1000000).toFixed(1)}M
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1 font-bold text-emerald-400">
                        {pool.apy.toFixed(2)}%
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {/* Row 2: CoinGecko Trending */}
      <div className="bg-[#050505] border border-[#1a1a2e] rounded-xl p-6 shadow-[0_0_15px_rgba(139,92,246,0.05)]">
         <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold flex items-center gap-2 text-slate-300">
              <Flame className="w-5 h-5 text-orange-500" />
              Trending Targets (CoinGecko)
            </h2>
            <span className="text-xs text-slate-500 flex items-center gap-1"><Clock className="w-3 h-3" /> Updated 10s ago</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {intel.trending.map((coin: any, i: number) => (
              <div key={i} className="bg-[#0a0a14] rounded-lg p-4 border border-[#1a1a2e] flex flex-col items-center text-center hover:border-orange-500/30 transition-colors cursor-pointer group">
                <img src={coin.thumb} alt={coin.symbol} className="w-10 h-10 rounded-full mb-3 shadow-[0_0_15px_rgba(249,115,22,0.1)] group-hover:shadow-[0_0_15px_rgba(249,115,22,0.4)] transition-all" />
                <div className="font-bold text-slate-200 max-w-full truncate">{coin.name}</div>
                <div className="text-xs font-mono text-slate-500 mt-1 uppercase">{coin.symbol}</div>
              </div>
            ))}
          </div>
      </div>
    </div>
  );
}
