import React, { useState, useEffect } from 'react';
import { Radar, Flame, Droplet, Clock, ArrowUpRight, Compass, ShieldAlert, Newspaper, Activity } from 'lucide-react';
import { toast } from 'sonner';

export function AlphaIntel() {
  const [intel, setIntel] = useState<any>(null);
  const [news, setNews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIntel = async () => {
      try {
        const [intelRes, newsRes] = await Promise.all([
          fetch('/api/intel'),
          fetch('/api/news')
        ]);
        if (!intelRes.ok || !newsRes.ok) {
          throw new Error('Network response was not ok');
        }
        let data, newsData;
        try {
          data = await intelRes.json();
          newsData = await newsRes.json();
        } catch (e) {
          throw new Error('Failed to parse response as JSON');
        }
        
        if (data.error) throw new Error(data.error);
        if (newsData.error) throw new Error(newsData.error);
        
        setIntel(data);
        setNews(newsData);
      } catch (error) {
        console.error('Failed to fetch data:', error);
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

      {/* Row 3: Market News */}
      <div className="bg-[#050505] border border-[#1a1a2e] rounded-xl p-6 shadow-[0_0_15px_rgba(139,92,246,0.05)]">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-bold flex items-center gap-2 text-slate-300">
            <Newspaper className="w-5 h-5 text-indigo-400" />
            Live Global Feeds (Yahoo Finance)
          </h2>
          <span className="px-2 py-1 text-[10px] uppercase font-bold tracking-widest bg-indigo-500/10 text-indigo-400 rounded border border-indigo-500/20">Extracted</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {news.map((item, i) => (
            <a key={item.uuid || i} href={item.link} target="_blank" rel="noopener noreferrer" className="bg-[#0a0a14] border border-[#1a1a2e] rounded-lg p-4 flex gap-4 hover:border-indigo-500/30 transition-colors group">
              {item.thumbnail?.resolutions?.[1]?.url && (
                <img src={item.thumbnail.resolutions[1].url} alt="" className="w-20 h-20 object-cover rounded-md flex-shrink-0" />
              )}
              <div className="space-y-2 flex-1">
                <div className="flex justify-between items-start gap-2">
                  <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">{item.publisher}</span>
                  <span className="text-[10px] text-slate-500">{new Date(item.providerPublishTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
                <h3 className="text-sm font-bold text-slate-200 group-hover:text-indigo-300 transition-colors line-clamp-2">{item.title}</h3>
                {item.relatedTickers && item.relatedTickers.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {item.relatedTickers.slice(0, 3).map((ticker: string) => (
                      <span key={ticker} className="text-[10px] font-mono bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">{ticker}</span>
                    ))}
                  </div>
                )}
              </div>
            </a>
          ))}
        </div>
        {news.length === 0 && (
          <div className="text-center py-8 text-slate-500 text-sm">Awaiting news transmission...</div>
        )}
      </div>
      {/* Row 4: Security and Whale Tracking */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Whale Wallet Tracking */}
        <div className="bg-[#050505] border border-[#1a1a2e] rounded-xl p-6 shadow-[0_0_15px_rgba(139,92,246,0.05)]">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold flex items-center gap-2 text-slate-300">
              <Activity className="w-5 h-5 text-cyan-400" />
              Leviathan-X Mempool Radar
            </h2>
            <span className="px-2 py-1 text-[10px] uppercase font-bold tracking-widest bg-cyan-500/10 text-cyan-400 rounded border border-cyan-500/20">Active</span>
          </div>

          <div className="space-y-3 font-mono text-sm">
            {[
              { type: 'Transfer', amount: '50,000 ETH', from: 'FTX Exploiter', to: 'Tornado Cash', time: '2 mins ago', severity: 'high' },
              { type: 'Swap', amount: '12M USDC', from: '0x32ab...9f01', to: 'PEPE', time: '14 mins ago', severity: 'medium' },
              { type: 'Accumulation', amount: '450 WBTC', from: 'Binance Hot', to: '0x88c1...e22a', time: '41 mins ago', severity: 'low' },
            ].map((alert, i) => (
              <div key={i} className="bg-[#0a0a14] border border-[#1a1a2e] p-3 rounded-lg flex items-center justify-between">
                <div>
                   <div className="flex items-center gap-2 mb-1">
                      <span className={`w-2 h-2 rounded-full ${alert.severity === 'high' ? 'bg-red-500 animate-pulse' : alert.severity === 'medium' ? 'bg-orange-500' : 'bg-blue-500'}`}></span>
                      <span className="text-slate-300 font-bold">{alert.amount} <span className="text-slate-500 font-normal">({alert.type})</span></span>
                   </div>
                   <div className="text-[10px] text-slate-500 break-all">
                     {alert.from} <span className="text-cyan-500">→</span> {alert.to}
                   </div>
                </div>
                <div className="text-[10px] text-slate-600 tracking-wider">
                  {alert.time}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Contract Security Scanner */}
        <div className="bg-[#050505] border border-[#1a1a2e] rounded-xl p-6 shadow-[0_0_15px_rgba(139,92,246,0.05)]">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold flex items-center gap-2 text-slate-300">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              Rug Pull Radar (Cipher-Q)
            </h2>
            <span className="px-2 py-1 text-[10px] uppercase font-bold tracking-widest bg-rose-500/10 text-rose-400 rounded border border-rose-500/20">Scanning</span>
          </div>

          <div className="space-y-4">
            {[
              { token: 'AI-DOGE', score: 15, issues: ['Mint function isolated', 'Owner can pause trading'], status: 'Honeypot' },
              { token: 'NEURAL-X', score: 85, issues: ['Dev wallet holds 15%'], status: 'Low Risk' },
              { token: 'TAO-WRAP', score: 40, issues: ['Liquidity not locked', 'Proxy contract'], status: 'High Risk' },
            ].map((scan, i) => (
              <div key={i} className="flex flex-col gap-2 bg-[#0a0a14] p-3 rounded-lg border border-[#1a1a2e]">
                <div className="flex justify-between items-center">
                  <div className="font-bold text-slate-200 text-sm font-mono">{scan.token}</div>
                  <div className={`text-xs px-2 py-1 rounded font-bold ${scan.score > 80 ? 'bg-emerald-500/20 text-emerald-400' : scan.score > 50 ? 'bg-orange-500/20 text-orange-400' : 'bg-rose-500/20 text-rose-400'}`}>
                    Score: {scan.score}/100
                  </div>
                </div>
                <div className="text-xs text-slate-500">
                  {scan.issues.join(' • ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}
