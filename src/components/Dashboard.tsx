import React, { useEffect, useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, ReferenceLine, Brush } from 'recharts';
import { TrendingUp, TrendingDown, Activity, RefreshCw, Globe, Zap, Maximize2, MousePointer2 } from 'lucide-react';

export function Dashboard() {
  const [marketData, setMarketData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');
  const [showTrendlines, setShowTrendlines] = useState(false);

  const fetchData = async (range = timeRange) => {
    try {
      const res = await fetch(`/api/market-data?range=${range}`);
      const json = await res.json();
      setMarketData(json);
    } catch (error) {
      console.error("Failed to fetch real market data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchData(timeRange);
    const interval = setInterval(() => fetchData(timeRange), 60000); // Refresh every 1m
    return () => clearInterval(interval);
  }, [timeRange]);

  const handleRangeChange = (range: string) => {
    setTimeRange(range);
  };

  const chartData = marketData?.chart || [];
  
  const stats = useMemo(() => {
    if (!chartData || chartData.length === 0) return null;
    const prices = chartData.map((d: any) => d.price);
    const max = Math.max(...prices);
    const min = Math.min(...prices);
    const avg = prices.reduce((a: number, b: number) => a + b, 0) / prices.length;
    return { max, min, avg };
  }, [chartData]);

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

  const ranges = [
    { label: '1D', value: '1d' },
    { label: '5D', value: '7d' }, // yahoo finance '7d' roughly gives 5 trading days
    { label: '1M', value: '1m' },
    { label: '3M', value: '3m' },
    { label: '1Y', value: '1y' },
  ];

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
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Globe className="w-5 h-5 text-blue-400" />
              S&P 500 Live Chart
            </h2>
            
            <div className="flex items-center gap-4">
              <div className="bg-slate-800 rounded-lg p-1 flex mt-px">
                {ranges.map((r) => (
                  <button
                    key={r.value}
                    onClick={() => handleRangeChange(r.value)}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      timeRange === r.value 
                        ? 'bg-blue-600 text-white' 
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
              
              <button 
                onClick={() => setShowTrendlines(!showTrendlines)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                  showTrendlines 
                    ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' 
                    : 'border-slate-700 bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700/80'
                }`}
                title="Toggle annotations (Avg, Min, Max)"
              >
                <MousePointer2 className="w-3.5 h-3.5" />
                Annotations
              </button>
            </div>
          </div>
          <div className="flex-1 min-h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis 
                  dataKey="time" 
                  stroke="#94a3b8" 
                  fontSize={11} 
                  tickLine={false} 
                  axisLine={false}
                  minTickGap={30}
                  tickFormatter={(val) => {
                    const d = new Date(val);
                    if (timeRange === '1d') return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
                  }}
                />
                <YAxis 
                  domain={['auto', 'auto']} 
                  stroke="#94a3b8" 
                  fontSize={11} 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(val) => `$${val.toFixed(0)}`}
                  width={60}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc', borderRadius: '0.5rem' }} 
                  itemStyle={{ color: '#3b82f6', fontWeight: 600 }} 
                  labelStyle={{ color: '#94a3b8', marginBottom: '0.25rem' }}
                />
                
                {showTrendlines && stats && (
                  <>
                    <ReferenceLine y={stats.avg} stroke="#10b981" strokeDasharray="5 5" label={{ position: 'insideTopLeft', value: 'Avg', fill: '#10b981', fontSize: 10 }} />
                    <ReferenceLine y={stats.max} stroke="#fbbf24" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'High', fill: '#fbbf24', fontSize: 10 }} />
                    <ReferenceLine y={stats.min} stroke="#f43f5e" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'Low', fill: '#f43f5e', fontSize: 10 }} />
                  </>
                )}

                <Area type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
                <Brush dataKey="time" height={30} stroke="#475569" fill="#0f172a" travellerWidth={10} tickFormatter={() => ''} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-400" />
              S&P 500 Live Actions
            </h2>
            <span className="text-xs font-medium bg-purple-500/10 text-purple-400 px-2.5 py-1 rounded-full">
              Live Equities
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-3">
            {['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'TSLA'].map(sym => {
              const stock = getQuote(sym);
              if (!stock || stock.price === 0) return null;
              const isPos = stock.change >= 0;
              return (
                <div key={sym} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-bold text-slate-200">{sym}</span>
                      <div className="text-xs text-slate-400 max-w-[150px] truncate">{stock.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-slate-200">${stock.price?.toFixed(2)}</div>
                      <div className={`text-xs font-medium ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isPos ? '+' : ''}{stock.change?.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
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


