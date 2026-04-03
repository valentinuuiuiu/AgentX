import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, TrendingDown, Activity, RefreshCw, Globe, Zap } from 'lucide-react';

export function Dashboard() {
  const [marketData, setMarketData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const res = await fetch('/api/market-data');
      const json = await res.json();
      setMarketData(json);
    } catch (error) {
      console.error("Failed to fetch real market data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000); // Refresh every 15s
    return () => clearInterval(interval);
  }, []);

  if (loading || !marketData) {
    return <div className="flex items-center justify-center h-64 text-slate-400">
      <RefreshCw className="w-6 h-6 animate-spin mr-2" />
      Connecting to Live Market Feeds...
    </div>;
  }

  if (marketData.error) {
    return <div className="flex items-center justify-center h-64 text-rose-400">
      Error: {marketData.error}
    </div>;
  }

  const getQuote = (symbol: string) => marketData.quotes?.find((q: any) => q.symbol === symbol) || { price: 0, change: 0 };
  
  const sp500 = getQuote('^GSPC');
  const btc = getQuote('BTC-USD');
  const gold = getQuote('GC=F');
  const silver = getQuote('SI=F');
  const eurUsd = getQuote('EURUSD=X');

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <StatCard 
          title="S&P 500" 
          value={sp500.price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} 
          change={`${sp500.change > 0 ? '+' : ''}${sp500.change.toFixed(2)}%`} 
          isPositive={sp500.change >= 0} 
        />
        <StatCard 
          title="BTC/USD" 
          value={btc.price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} 
          change={`${btc.change > 0 ? '+' : ''}${btc.change.toFixed(2)}%`} 
          isPositive={btc.change >= 0} 
        />
        <StatCard 
          title="Gold Futures" 
          value={gold.price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} 
          change={`${gold.change > 0 ? '+' : ''}${gold.change.toFixed(2)}%`} 
          isPositive={gold.change >= 0} 
        />
        <StatCard 
          title="Silver Futures" 
          value={silver.price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} 
          change={`${silver.change > 0 ? '+' : ''}${silver.change.toFixed(2)}%`} 
          isPositive={silver.change >= 0} 
        />
        <StatCard 
          title="EUR/USD" 
          value={`$${eurUsd.price.toFixed(4)}`} 
          change={`${eurUsd.change > 0 ? '+' : ''}${eurUsd.change.toFixed(2)}%`} 
          isPositive={eurUsd.change >= 0} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Globe className="w-5 h-5 text-blue-400" />
              S&P 500 Live Chart (7 Days)
            </h2>
            <span className="text-xs font-medium bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-full flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Market Data
            </span>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={marketData.chart || []}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis domain={['auto', 'auto']} stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val.toFixed(0)}`} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} itemStyle={{ color: '#3b82f6' }} />
                <Area type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              Minimax-m2.7 Arbitrage
            </h2>
            <span className="text-xs font-medium bg-amber-500/10 text-amber-400 px-2.5 py-1 rounded-full">
              Scanning...
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-3">
            {marketData.arbitrage?.map((opp: any) => (
              <div key={opp.id} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-bold text-slate-200">{opp.asset}</span>
                  <span className="text-xs text-slate-400">{opp.time}</span>
                </div>
                <div className="text-sm text-slate-300 mb-2">
                  {opp.route}
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-400">Spread: <span className="text-emerald-400 font-medium">{opp.spread}</span></span>
                  <span className="font-semibold text-emerald-400">{opp.profit}</span>
                </div>
              </div>
            ))}
            {(!marketData.arbitrage || marketData.arbitrage.length === 0) && (
              <div className="text-center text-slate-500 py-8">
                No arbitrage opportunities detected.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, change, isPositive }: { title: string, value: string, change: string, isPositive: boolean }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col">
      <span className="text-slate-400 text-sm font-medium mb-2">{title}</span>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-bold">{value}</span>
        <div className={`flex items-center text-sm font-medium ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isPositive ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
          {change}
        </div>
      </div>
    </div>
  );
}


