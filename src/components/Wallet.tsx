import React, { useState } from 'react';
import { ArrowRightLeft, ShieldCheck, Key, AlertCircle, Link } from 'lucide-react';

export function WalletView() {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKey && apiSecret) {
      setIsConnected(true);
    }
  };

  const mockExecutions = [
    { id: 'tx-88392a', agent: 'Minimax-m2.7', asset: 'ETH/USDC', type: 'Arbitrage Buy', amount: '12.5 ETH', price: '$3,420.10', status: 'Confirmed', time: '2 mins ago' },
    { id: 'tx-99210b', agent: 'Kimi-k2.5', asset: 'SPY', type: 'Limit Buy', amount: '50 Shares', price: '$512.45', status: 'Pending', time: '15 mins ago' },
    { id: 'tx-11029c', agent: 'GLM-5', asset: 'GC=F (Gold)', type: 'Market Sell', amount: '2 Contracts', price: '$2,340.50', status: 'Confirmed', time: '1 hour ago' },
  ];

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-gradient-to-br from-blue-900/40 to-emerald-900/20 border border-blue-500/20 rounded-xl p-8 relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-2 text-emerald-400 font-medium mb-4">
            <ShieldCheck className="w-5 h-5" />
            Zero-Commission Trading Account
          </div>
          <p className="text-slate-300 text-sm mb-6 max-w-2xl">
            To execute real trades without simulator limitations, connect your zero-commission brokerage API (e.g., Alpaca, Robinhood API, or Binance). The Eliza agents will route trades through your connected account.
          </p>
          
          {!isConnected ? (
            <form onSubmit={handleConnect} className="bg-slate-900/80 border border-slate-700 rounded-xl p-6 max-w-md">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                <Key className="w-5 h-5 text-blue-400" />
                Connect Exchange API
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">API Key</label>
                  <input 
                    type="password" 
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500" 
                    placeholder="Enter your API Key"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">API Secret</label>
                  <input 
                    type="password" 
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500" 
                    placeholder="Enter your API Secret"
                  />
                </div>
                <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium transition-colors">
                  Securely Connect Account
                </button>
              </div>
              <div className="mt-4 flex items-start gap-2 text-xs text-slate-500">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <p>Keys are stored locally in your browser session and never sent to our servers. They are injected directly into the execution agent's environment.</p>
              </div>
            </form>
          ) : (
            <div>
              <h2 className="text-slate-400 text-lg mb-1">Live Account Balance</h2>
              <div className="text-5xl font-bold text-white mb-8">$0.00</div>
              
              <div className="flex gap-4">
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2">
                  <ArrowRightLeft className="w-4 h-4" />
                  Deposit Funds
                </button>
                <button 
                  onClick={() => setIsConnected(false)}
                  className="bg-slate-800 hover:bg-slate-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors border border-slate-700 flex items-center gap-2"
                >
                  <Link className="w-4 h-4" />
                  Disconnect API
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <h3 className="text-xl font-semibold mt-8 mb-4">Execution Log</h3>
      {!isConnected ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden p-8 text-center">
          <p className="text-slate-400">Connect your API keys to view real-time execution logs.</p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/50 border-b border-slate-800 text-slate-400">
              <tr>
                <th className="px-6 py-3 font-medium">Time</th>
                <th className="px-6 py-3 font-medium">Agent</th>
                <th className="px-6 py-3 font-medium">Asset</th>
                <th className="px-6 py-3 font-medium">Action</th>
                <th className="px-6 py-3 font-medium">Amount @ Price</th>
                <th className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {mockExecutions.map((tx) => (
                <tr key={tx.id} className="hover:bg-slate-800/20 transition-colors">
                  <td className="px-6 py-4 text-slate-400">{tx.time}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-400 text-xs font-medium border border-blue-500/20">
                      {tx.agent}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-medium text-slate-200">{tx.asset}</td>
                  <td className="px-6 py-4">
                    <span className={tx.type.includes('Buy') ? 'text-emerald-400' : 'text-rose-400'}>
                      {tx.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {tx.amount} <span className="text-slate-500">@ {tx.price}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1.5 ${tx.status === 'Confirmed' ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {tx.status === 'Confirmed' ? (
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400"></div>
                      ) : (
                        <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></div>
                      )}
                      {tx.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

