import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  TrendingUp, TrendingDown, Activity, Zap, Brain, Shield,
  RefreshCw, ChevronRight, Sparkles, Coins,
  Wallet, BarChart3, Terminal,
  ArrowRightLeft, CheckCircle, AlertTriangle,
  Target, Cpu, Database, Layers, Eye, Hexagon, Users, MessageSquare, Newspaper
} from 'lucide-react';
import AICompanionCreator from './components/AICompanionCreator';
import MCPFunctionVisualizer from './components/MCPFunctionVisualizer';
import ProfitableFlashArbitrage from './components/ProfitableFlashArbitrage';
import HiveMindDisplay from './components/HiveMindDisplay';
import { RehoboamCore } from './components/agentx/RehoboamCore';
import { BittensorNode } from './components/agentx/BittensorNode';
import { Team as AgentTeam } from './components/agentx/Team';
import { Chat as AgentTerminal } from './components/agentx/Chat';
import { AlphaIntel } from './components/agentx/AlphaIntel';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingSpinner from './components/ui/LoadingSpinner';
import { useWeb3 } from './contexts/Web3Context';
import { useNotification } from './contexts/NotificationContext';
import { Button } from './components/ui/button';
import {
  fetchRealPrices,
  fetchSepoliaBalances,
  executeFlashArbitrage,
  buildUniV2SwapStep,
  switchToSepolia,
  SEPOLIA,
} from './services/sepoliaService';

// Pure SVG sparkline — no Recharts dependency
function Sparkline({ data, width = 300, height = 80, stroke = '#6366f1', fill = '#6366f1' }) {
  if (!data || data.length < 2) return null;
  const prices = data.map(d => d.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const pts = prices.map((p, i) => {
    const x = (i / (prices.length - 1)) * width;
    const y = height - ((p - min) / range) * (height * 0.9) - height * 0.05;
    return `${x},${y}`;
  });
  const areaPath = `M0,${height} L${pts.join(' L')} L${width},${height} Z`;
  const linePath = `M${pts.join(' L')}`;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="none">
      <defs>
        <linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="5%" stopColor={fill} stopOpacity={0.25} />
          <stop offset="95%" stopColor={fill} stopOpacity={0} />
        </linearGradient>
      </defs>
      <path d={areaPath} fill="url(#sparkFill)" />
      <path d={linePath} fill="none" stroke={stroke} strokeWidth={2} />
    </svg>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [priceData, setPriceData] = useState(new Map());
  const [priceLoading, setPriceLoading] = useState(true);
  const [priceError, setPriceError] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [tokenBalances, setTokenBalances] = useState([]);
  const [balancesLoading, setBalancesLoading] = useState(false);
  const [arbForm, setArbForm] = useState({ asset: 'WETH', amount: '0.01', minProfit: '0' });
  const [arbExecuting, setArbExecuting] = useState(false);
  const [arbResult, setArbResult] = useState(null);
  const [arbError, setArbError] = useState(null);
  const [txHistory, setTxHistory] = useState([]);
  const [isSepolia, setIsSepolia] = useState(false);
  const [switching, setSwitching] = useState(false);

  const { account, connectWallet, isConnected, balance, provider, chainId } = useWeb3();
  const { addNotification } = useNotification();

  const trackedSymbols = useMemo(() => ['BTC', 'ETH', 'LINK', 'SOL', 'ARB', 'OP'], []);

  useEffect(() => {
    setIsSepolia(chainId === SEPOLIA.chainId);
  }, [chainId]);

  const loadPrices = useCallback(async () => {
    try {
      setPriceLoading(true);
      setPriceError(null);
      const result = await fetchRealPrices();
      if (result) {
        setPriceData(result);
        const ethData = result.get('ETH');
        if (ethData) {
          setChartData(prev => [...prev.slice(-60), {
            time: new Date().toLocaleTimeString(),
            price: ethData.price,
          }]);
        }
      } else {
        setPriceError('CoinGecko unreachable');
      }
    } catch (err) {
      setPriceError(err.message);
    } finally {
      setPriceLoading(false);
    }
  }, []);

  const loadBalances = useCallback(async () => {
    if (!provider || !account || !isSepolia) return;
    try {
      setBalancesLoading(true);
      const balances = await fetchSepoliaBalances(provider, account);
      setTokenBalances(balances);
    } catch (err) {
      console.error('Balance fetch failed:', err);
    } finally {
      setBalancesLoading(false);
    }
  }, [provider, account, isSepolia]);

  useEffect(() => {
    loadPrices();
    const interval = setInterval(loadPrices, 30000);
    return () => clearInterval(interval);
  }, [loadPrices]);

  useEffect(() => {
    if (isConnected && isSepolia) {
      loadBalances();
      const interval = setInterval(loadBalances, 15000);
      return () => clearInterval(interval);
    }
  }, [isConnected, isSepolia, loadBalances]);

  const handleSwitchToSepolia = async () => {
    try {
      setSwitching(true);
      await switchToSepolia();
      addNotification('success', 'Switched to Sepolia testnet');
    } catch (err) {
      addNotification('error', `Failed to switch: ${err.message}`);
    } finally {
      setSwitching(false);
    }
  };

  const handleExecuteArbitrage = async () => {
    if (!isConnected) { addNotification('warning', 'Connect your wallet first'); return; }
    if (!isSepolia) { addNotification('warning', 'Switch to Sepolia testnet first'); await handleSwitchToSepolia(); return; }
    setArbExecuting(true); setArbResult(null); setArbError(null);
    try {
      const signer = await provider.getSigner();
      const tokenInfo = SEPOLIA.tokens[arbForm.asset];
      if (!tokenInfo) throw new Error(`Unknown token: ${arbForm.asset}`);
      const amount = arbForm.asset === 'USDC' ? ethers.parseUnits(arbForm.amount, 6) : ethers.parseUnits(arbForm.amount, 18);
      const minProfit = ethers.parseUnits(arbForm.minProfit, 18);
      const outputToken = arbForm.asset === 'WETH' ? SEPOLIA.tokens.DAI : SEPOLIA.tokens.WETH;
      const swapStep = buildUniV2SwapStep(SEPOLIA.uniswapV2Router, tokenInfo, outputToken, amount, 0);
      const result = await executeFlashArbitrage(signer, tokenInfo, amount, minProfit, [swapStep]);
      setArbResult(result);
      setTxHistory(prev => [{ ...result, asset: arbForm.asset, amount: arbForm.amount, timestamp: Date.now() }, ...prev]);
      addNotification('success', `Arbitrage executed! TX: ${result.hash.slice(0, 10)}...`);
      loadBalances();
    } catch (err) {
      const msg = err?.reason || err?.message || 'Unknown error';
      setArbError(msg);
      addNotification('error', `Arbitrage failed: ${msg.slice(0, 80)}`);
    } finally {
      setArbExecuting(false);
    }
  };

  const portfolioValue = useMemo(() => {
    if (!tokenBalances.length || !priceData.size) return null;
    let total = 0;
    for (const b of tokenBalances) {
      const p = priceData.get(b.symbol === 'WETH' ? 'ETH' : b.symbol);
      if (p) {
        const bal = parseFloat(b.balance);
        if (!isNaN(bal)) {
          total += bal * p.price;
        }
      }
    }
    return total;
  }, [tokenBalances, priceData]);

  const formatCurrency = (v) => {
    if (v == null) return '---';
    if (v >= 1) return '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return '$' + v.toFixed(6);
  };
  const formatPercent = (v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

  const getTokenGradient = (s) => ({
    BTC: 'from-amber-500 to-orange-500',
    ETH: 'from-blue-500 to-indigo-500',
    LINK: 'from-cyan-500 to-blue-500',
    SOL: 'from-purple-500 to-violet-500',
    ARB: 'from-blue-600 to-cyan-500',
    OP: 'from-red-500 to-orange-500',
  }[s] || 'from-gray-500 to-gray-600');

  const NAV_ITEMS = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'arbitrage', label: 'Flash Arb', icon: Zap },
    { id: 'portfolio', label: 'Portfolio', icon: Wallet },
    { id: 'ai-companions', label: 'AI', icon: Brain },
    { id: 'consciousness', label: 'Consciousness', icon: Cpu },
    { id: 'mcp', label: 'MCP Tools', icon: Terminal },
    { id: 'agent-team', label: 'Agent Team', icon: Users },
    { id: 'alpha-intel', label: 'Alpha Intel', icon: Newspaper },
    { id: 'terminal', label: 'Terminal', icon: MessageSquare },
    { id: 'bittensor', label: 'TAO Network', icon: Hexagon },
    { id: 'rehoboam-core', label: 'Rehoboam Core', icon: Eye },
  ];

  const isRehoboam = activeTab === 'rehoboam-core';

  return (
    <div className={`min-h-screen font-sans transition-colors duration-500 ${isRehoboam ? 'bg-[#050505] text-slate-100' : 'bg-[#050510] text-white'}`}>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <aside className={`w-56 border-r flex flex-col shrink-0 transition-colors duration-500 ${isRehoboam ? 'bg-black border-red-900/30' : 'bg-[#0a0a15] border-[#1a1a2e]'}`}>
          <div className="p-5 border-b border-[#1a1a2e]">
            <div className="flex items-center gap-2.5">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-500 ${isRehoboam ? 'bg-red-900/30 text-red-500 border border-red-500/30 animate-pulse' : 'bg-gradient-to-br from-indigo-500 to-purple-500'}`}>
                  {isRehoboam ? <Eye className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
              </div>
              <div>
                  <h1 className={`text-base font-bold transition-colors duration-500 ${isRehoboam ? 'text-red-500 uppercase tracking-widest' : 'text-white'}`}>
                    {isRehoboam ? 'REHOBOAM' : 'Rehoboam'}
                  </h1>
                  <p className="text-[10px] text-slate-500">{isRehoboam ? 'System Override' : 'Sepolia Trading'}</p>
              </div>
            </div>
          </div>
          <nav className="flex-1 p-3">
            {NAV_ITEMS.map(item => {
              const Icon = item.icon;
              const active = activeTab === item.id;
              let activeClass = 'bg-indigo-600/20 text-white border border-indigo-500/30';
              let hoverClass = 'text-slate-400 hover:text-white hover:bg-[#1a1a2e]';

              if (isRehoboam) {
                activeClass = 'bg-red-900/20 text-red-500 border border-red-900/50 shadow-[0_0_15px_rgba(239,68,68,0.1)]';
                hoverClass = 'text-red-500/50 hover:bg-red-900/10 hover:text-red-400';
              }

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left text-sm mb-1 transition-all duration-200 ${
                    active ? activeClass : hoverClass
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>
          <div className="p-3 border-t border-[#1a1a2e]">
            <div className="flex items-center gap-2 text-xs">
              <div className={`w-2 h-2 rounded-full ${isSepolia ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span className="text-slate-400">{isSepolia ? 'Sepolia' : chainId ? `Chain ${chainId}` : 'No chain'}</span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto relative">
          {/* Header */}
          <header className={`sticky top-0 z-50 backdrop-blur border-b px-5 py-3 transition-colors duration-500 ${isRehoboam ? 'border-red-900/30 bg-black/50' : 'bg-[#050510]/90 border-[#1a1a2e]'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h2 className={`text-lg font-semibold ${isRehoboam ? 'text-red-500 tracking-wider' : ''}`}>
                  {NAV_ITEMS.find(i => i.id === activeTab)?.label}
                </h2>
                {priceLoading && <span className="text-xs text-slate-500 animate-pulse">Loading prices...</span>}
                {priceError && <span className="text-xs text-red-400">{priceError}</span>}
              </div>
              <div className="flex items-center gap-3">
                {!isSepolia && isConnected && (
                  <Button onClick={handleSwitchToSepolia} disabled={switching} className="bg-amber-600 hover:bg-amber-500 text-white px-3 py-1.5 rounded-lg text-xs font-medium">
                    {switching ? 'Switching...' : 'Switch to Sepolia'}
                  </Button>
                )}
                {isConnected ? (
                  <div className="flex items-center gap-2 bg-[#1a1a2e] rounded-lg px-3 py-1.5 border border-[#2a2a3e]">
                    <div className={`w-2 h-2 rounded-full ${isSepolia ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                    <span className="text-xs font-mono text-slate-300">{account?.slice(0, 6)}...{account?.slice(-4)}</span>
                  </div>
                ) : (
                  <Button onClick={connectWallet} className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1.5">
                    <Wallet className="w-3.5 h-3.5" />
                    Connect
                  </Button>
                )}
              </div>
            </div>
          </header>

          <div className="p-5">
            {/* DASHBOARD */}
            {activeTab === 'dashboard' && (
              <div className="space-y-5">
                {/* Price Cards */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {trackedSymbols.map(symbol => {
                    const data = priceData.get(symbol);
                    const up = data && data.changePercent >= 0;
                    return (
                      <div key={symbol} className="bg-[#0a0a15] rounded-xl p-3.5 border border-[#2a2a3e] hover:border-indigo-500/40 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${getTokenGradient(symbol)} flex items-center justify-center text-[10px] font-bold`}>
                            {symbol.slice(0, 2)}
                          </div>
                          {data && (
                            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${up ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                              {formatPercent(data.changePercent)}
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-slate-500">{symbol}/USD</p>
                        <p className="text-base font-bold font-mono mt-0.5">{data ? formatCurrency(data.price) : '---'}</p>
                        <div className="flex justify-between mt-1.5 pt-1.5 border-t border-[#1a1a2e] text-[10px] text-slate-600">
                          <span>H: {data ? formatCurrency(data.high24h) : '---'}</span>
                          <span>L: {data ? formatCurrency(data.low24h) : '---'}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Chart — pure SVG, no Recharts */}
                <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] overflow-hidden">
                  <div className="px-4 py-3 border-b border-[#2a2a3e] flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold">ETH/USD</h3>
                      <p className="text-[10px] text-slate-500">CoinGecko live data</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold font-mono">{formatCurrency(priceData.get('ETH')?.price)}</span>
                      {priceData.get('ETH') && (
                        <span className={`text-xs font-medium ${priceData.get('ETH').changePercent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {formatPercent(priceData.get('ETH').changePercent)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="h-64 p-2">
                    {chartData.length > 1 ? (
                      <Sparkline data={chartData} width={600} height={240} stroke="#6366f1" fill="#6366f1" />
                    ) : (
                      <div className="flex items-center justify-center h-full text-slate-500 text-sm">
                        Waiting for price data...
                      </div>
                    )}
                  </div>
                </div>

                {/* Wallet Summary */}
                {isConnected && (
                  <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold">Wallet</h3>
                      <button onClick={loadBalances} className="text-xs text-slate-400 hover:text-white">
                        <RefreshCw className={`w-3 h-3 ${balancesLoading ? 'animate-spin' : ''}`} />
                      </button>
                    </div>
                    {!isSepolia ? (
                      <div className="flex items-center gap-2 text-amber-400 text-xs">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Switch to Sepolia to see on-chain balances</span>
                      </div>
                    ) : tokenBalances.length === 0 ? (
                      <p className="text-xs text-slate-500">{balancesLoading ? 'Loading...' : 'No token balances found'}</p>
                    ) : (
                      <div className="space-y-2">
                        {tokenBalances.map(b => (
                          <div key={b.symbol} className="flex items-center justify-between py-1.5 border-b border-[#1a1a2e] last:border-0">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-medium">{b.symbol}</span>
                              <span className="text-[10px] text-slate-500 font-mono">{b.address.slice(0, 6)}...{b.address.slice(-4)}</span>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-mono">{!isNaN(parseFloat(b.balance)) ? parseFloat(b.balance).toFixed(b.decimals > 6 ? 4 : 2) : "0.00"}</span>
                              {(() => {
                                const p = priceData.get(b.symbol === 'WETH' ? 'ETH' : b.symbol);
                                return p && !isNaN(parseFloat(b.balance)) ? <span className="text-[10px] text-slate-500 ml-2">{formatCurrency(parseFloat(b.balance) * p.price)}</span> : null;
                              })()}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* FLASH ARBITRAGE */}
            {activeTab === 'arbitrage' && (
              <div className="max-w-xl mx-auto space-y-5">
                <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Zap className="w-4 h-4 text-amber-400" />
                    <h3 className="text-sm font-semibold">Flash Arbitrage — Sepolia</h3>
                  </div>
                  {!isSepolia && isConnected && (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 mb-4 text-xs text-amber-300">
                      <AlertTriangle className="w-3 h-3 inline mr-1" />
                      You must be on Sepolia to execute.{' '}
                      <button onClick={handleSwitchToSepolia} className="underline font-medium">Switch now</button>
                    </div>
                  )}
                  {!isConnected && (
                    <div className="bg-slate-800 rounded-lg p-3 mb-4 text-xs text-slate-400">Connect your wallet to trade on Sepolia.</div>
                  )}
                  <div className="space-y-3">
                    <div>
                      <label className="block text-[10px] text-slate-500 mb-1 uppercase">Flash Loan Asset</label>
                      <select className="w-full bg-[#080810] border border-[#2a2a3e] rounded-lg p-2.5 text-sm text-white" value={arbForm.asset} onChange={e => setArbForm(f => ({ ...f, asset: e.target.value }))}>
                        {Object.keys(SEPOLIA.tokens).map(s => <option key={s} value={s} className="bg-[#080810]">{s}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-500 mb-1 uppercase">Amount</label>
                      <input type="text" className="w-full bg-[#080810] border border-[#2a2a3e] rounded-lg p-2.5 text-sm text-white font-mono" value={arbForm.amount} onChange={e => setArbForm(f => ({ ...f, amount: e.target.value }))} placeholder="0.01" />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-500 mb-1 uppercase">Min Profit (wei)</label>
                      <input type="text" className="w-full bg-[#080810] border border-[#2a2a3e] rounded-lg p-2.5 text-sm text-white font-mono" value={arbForm.minProfit} onChange={e => setArbForm(f => ({ ...f, minProfit: e.target.value }))} placeholder="0" />
                    </div>
                    <Button onClick={handleExecuteArbitrage} disabled={arbExecuting || !isConnected || !isSepolia} className="w-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 disabled:opacity-40 text-white py-3 rounded-lg font-semibold text-sm">
                      {arbExecuting ? (<span className="flex items-center gap-2 justify-center"><LoadingSpinner size="sm" /> Executing...</span>) : (<span className="flex items-center gap-2 justify-center"><Zap className="w-4 h-4" /> Execute Arbitrage</span>)}
                    </Button>
                  </div>
                  {arbError && (<div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400 break-all">{arbError}</div>)}
                  {arbResult && (
                    <div className="mt-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-xs text-emerald-300 space-y-1">
                      <div className="flex items-center gap-1.5 font-semibold mb-1"><CheckCircle className="w-3.5 h-3.5" /> Arbitrage Executed</div>
                      <div className="font-mono text-[10px]">TX: {arbResult.hash}</div>
                      <div>Block: {arbResult.blockNumber} | Gas: {arbResult.gasUsed}</div>
                      {arbResult.explorer && <a href={arbResult.explorer} target="_blank" rel="noopener noreferrer" className="text-indigo-400 underline">View on Etherscan</a>}
                    </div>
                  )}
                </div>
                {txHistory.length > 0 && (
                  <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-4">
                    <h3 className="text-xs font-semibold mb-3">Transaction History</h3>
                    <div className="space-y-2">
                      {txHistory.map((tx, i) => (
                        <div key={i} className="flex items-center justify-between py-2 border-b border-[#1a1a2e] last:border-0 text-xs">
                          <div className="flex items-center gap-2"><CheckCircle className="w-3 h-3 text-emerald-400" /><span className="font-mono text-slate-400">{tx.hash.slice(0, 10)}...{tx.hash.slice(-6)}</span></div>
                          <div className="text-right"><span className="text-slate-300">{tx.amount} {tx.asset}</span><span className="text-slate-600 ml-2">{new Date(tx.timestamp).toLocaleTimeString()}</span></div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-4 text-xs text-slate-400">
                  <h3 className="font-semibold text-slate-300 mb-2">Contract Addresses</h3>
                  <div className="space-y-1 font-mono text-[10px]">
                    <div>FlashArbMaster: <span className="text-indigo-400">{SEPOLIA.flashArbMaster}</span></div>
                    <div>Aave PoolProvider: <span className="text-indigo-400">{SEPOLIA.aavePoolProvider}</span></div>
                    <div>UniV2 Router: <span className="text-indigo-400">{SEPOLIA.uniswapV2Router}</span></div>
                  </div>
                </div>
                <ErrorBoundary section="Legacy Arbitrage"><ProfitableFlashArbitrage /></ErrorBoundary>
              </div>
            )}

            {/* PORTFOLIO */}
            {activeTab === 'portfolio' && (
              <div className="space-y-5">
                {!isConnected ? (
                  <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-8 text-center">
                    <Wallet className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-400 mb-2">Connect your wallet to view portfolio</p>
                    <Button onClick={connectWallet} className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2 rounded-lg text-sm">Connect Wallet</Button>
                  </div>
                ) : (
                  <>
                    <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-5">
                      <p className="text-[10px] text-slate-500 uppercase mb-1">Portfolio Value</p>
                      <p className="text-3xl font-bold font-mono">{portfolioValue != null ? formatCurrency(portfolioValue) : '---'}</p>
                      {!isSepolia && <p className="text-amber-400 text-xs mt-2">Switch to Sepolia for on-chain balances</p>}
                    </div>
                    {tokenBalances.length > 0 ? (
                      <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-4">
                        <h3 className="text-sm font-semibold mb-3">Token Balances</h3>
                        <div className="space-y-2">
                          {tokenBalances.map(b => {
                            const p = priceData.get(b.symbol === 'WETH' ? 'ETH' : b.symbol);
                            const val = p && !isNaN(parseFloat(b.balance)) ? parseFloat(b.balance) * p.price : null;
                            return (
                              <div key={b.symbol} className="flex items-center justify-between py-2.5 border-b border-[#1a1a2e] last:border-0">
                                <div><span className="font-medium">{b.symbol}</span><span className="text-[10px] text-slate-600 font-mono ml-2">{b.address.slice(0, 6)}...{b.address.slice(-4)}</span></div>
                                <div className="text-right"><p className="font-mono text-sm">{!isNaN(parseFloat(b.balance)) ? parseFloat(b.balance).toFixed(b.decimals > 6 ? 4 : 2) : "0.00"}</p>{val != null && <p className="text-[10px] text-slate-500">{formatCurrency(val)}</p>}</div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-6 text-center">
                        <p className="text-sm text-slate-500">{isSepolia ? (balancesLoading ? 'Loading...' : 'No token balances on Sepolia') : 'Switch to Sepolia to view on-chain balances'}</p>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* AI COMPANIONS */}
            {activeTab === 'ai-companions' && (
              <ErrorBoundary section="AI Companions">
                <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-5"><AICompanionCreator /></div>
              </ErrorBoundary>
            )}

            {/* CONSCIOUSNESS */}
            {activeTab === 'consciousness' && (
              <ErrorBoundary section="Consciousness">
                <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-5"><HiveMindDisplay /></div>
              </ErrorBoundary>
            )}

            {/* MCP TOOLS */}
            {activeTab === 'mcp' && (
              <ErrorBoundary section="MCP Tools">
                <div className="bg-[#0a0a15] rounded-xl border border-[#2a2a3e] p-5">
                  <div className="flex items-center gap-2 mb-4"><Terminal className="w-4 h-4 text-indigo-400" /><h3 className="text-sm font-semibold">MCP Tools</h3></div>
                  <MCPFunctionVisualizer />
                </div>
              </ErrorBoundary>
            )}

            {/* AGENT TEAM */}
            {activeTab === 'agent-team' && (
              <ErrorBoundary section="Agent Team">
                <AgentTeam />
              </ErrorBoundary>
            )}

            {/* ALPHA INTEL */}
            {activeTab === 'alpha-intel' && (
              <ErrorBoundary section="Alpha Intel">
                <AlphaIntel />
              </ErrorBoundary>
            )}

            {/* TERMINAL */}
            {activeTab === 'terminal' && (
              <ErrorBoundary section="Terminal">
                <AgentTerminal />
              </ErrorBoundary>
            )}

            {/* BITTENSOR */}
            {activeTab === 'bittensor' && (
              <ErrorBoundary section="Bittensor">
                <BittensorNode />
              </ErrorBoundary>
            )}

            {/* REHOBOAM CORE */}
            {activeTab === 'rehoboam-core' && (
              <ErrorBoundary section="Rehoboam Core">
                <RehoboamCore />
              </ErrorBoundary>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;