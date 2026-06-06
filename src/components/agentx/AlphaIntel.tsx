import React, { useState, useEffect } from 'react';
import { Newspaper, TrendingUp, TrendingDown, AlertTriangle, RefreshCw, ExternalLink, Zap, Clock } from 'lucide-react';

interface NewsItem {
  title: string;
  link: string;
  publisher: string;
  publishedAt: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  relatedTickers: string[];
  summary: string;
}

interface MarketFear {
  value: string;
  classification: string;
  timestamp: string;
}

export function AlphaIntel() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [fearGreed, setFearGreed] = useState<MarketFear | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'bullish' | 'bearish'>('all');

  const fetchNews = async () => {
    setLoading(true);
    try {
      const apiUrl = (window.location.protocol === 'https:' ? 'https://' : 'http://') + window.location.host.replace(':5001', ':5002') + '/api/alpha-intel';
      const res = await fetch(apiUrl);
      const data = await res.json();
      setNews(data.news || []);
      setFearGreed(data.fearGreed || null);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Alpha Intel fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
    const interval = setInterval(fetchNews, 300000); // 5 min refresh
    return () => clearInterval(interval);
  }, []);

  const filtered = activeFilter === 'all' ? news : news.filter(n => n.sentiment === activeFilter);

  const getSentimentColor = (s: string) => {
    if (s === 'bullish') return 'text-emerald-400 bg-emerald-500/10';
    if (s === 'bearish') return 'text-rose-400 bg-rose-500/10';
    return 'text-slate-400 bg-slate-700/50';
  };

  const getSentimentIcon = (s: string) => {
    if (s === 'bullish') return <TrendingUp className="w-3.5 h-3.5" />;
    if (s === 'bearish') return <TrendingDown className="w-3.5 h-3.5" />;
    return <AlertTriangle className="w-3.5 h-3.5" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <Newspaper className="w-7 h-7 text-blue-400" />
            Alpha Intel
          </h2>
          <p className="text-slate-400 text-sm mt-1">Real-time market news from Yahoo Finance. Sentiment-analyzed and ticker-tagged.</p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && (
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchNews}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Fear & Greed Index */}
      {fearGreed && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Zap className="w-5 h-5 text-amber-400" />
              <span className="font-medium">Crypto Fear & Greed Index</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-3xl font-bold text-amber-400">{fearGreed.value}</span>
              <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                fearGreed.classification === 'Extreme Fear' ? 'bg-rose-500/10 text-rose-400' :
                fearGreed.classification === 'Fear' ? 'bg-orange-500/10 text-orange-400' :
                fearGreed.classification === 'Greed' ? 'bg-emerald-500/10 text-emerald-400' :
                fearGreed.classification === 'Extreme Greed' ? 'bg-emerald-400/10 text-emerald-300' :
                'bg-slate-700 text-slate-300'
              }`}>
                {fearGreed.classification}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {(['all', 'bullish', 'bearish'] as const).map(f => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              activeFilter === f
                ? f === 'bullish' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : f === 'bearish' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700'
            }`}
          >
            {f === 'all' ? 'All Intel' : f === 'bullish' ? 'Bullish' : 'Bearish'}
            <span className="ml-2 text-xs opacity-60">
              ({f === 'all' ? news.length : news.filter(n => n.sentiment === f).length})
            </span>
          </button>
        ))}
      </div>

      {/* News Feed */}
      {loading && news.length === 0 ? (
        <div className="flex items-center justify-center h-48 text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" />
          Fetching market intelligence...
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((item, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors group">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1 ${getSentimentColor(item.sentiment)}`}>
                      {getSentimentIcon(item.sentiment)}
                      {item.sentiment.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-500">{item.publisher}</span>
                    <span className="text-xs text-slate-600">{item.publishedAt}</span>
                  </div>
                  <h3 className="font-semibold text-slate-200 group-hover:text-white transition-colors">{item.title}</h3>
                  {item.summary && (
                    <p className="text-sm text-slate-400 mt-2 line-clamp-2">{item.summary}</p>
                  )}
                  <div className="flex items-center gap-2 mt-3">
                    {item.relatedTickers.map((ticker, j) => (
                      <span key={j} className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs font-mono text-slate-300">
                        ${ticker}
                      </span>
                    ))}
                  </div>
                </div>
                <a
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 p-2 text-slate-500 hover:text-blue-400 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              No {activeFilter} intel at the moment.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
