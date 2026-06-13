import React, { useState } from 'react';
import { ArrowRightLeft, ShieldCheck, Key, AlertCircle, Link, Hexagon } from 'lucide-react';
import { toast } from 'sonner';

export function WalletView() {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [walletType, setWalletType] = useState<'CEX' | 'MetaMask' | 'Talisman' | null>(null);

  const [orderAsset, setOrderAsset] = useState('SPY');
  const [orderQuantity, setOrderQuantity] = useState('');
  const [orderType, setOrderType] = useState('Market Buy');
  const [limitPrice, setLimitPrice] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [taoGasPool, setTaoGasPool] = useState(24.50);

  const [executions, setExecutions] = useState([
    { id: 'tx-88392a', agent: 'Minimax-m2.7', asset: 'ETH/USDC', type: 'Arbitrage Buy', amount: '12.5 ETH', price: '$3,420.10', status: 'Confirmed', time: '2 mins ago' },
    { id: 'tx-99210b', agent: 'Kimi-k2.5', asset: 'SPY', type: 'Limit Buy', amount: '50 Shares', price: '$512.45', status: 'Pending', time: '15 mins ago' },
    { id: 'tx-11029c', agent: 'GLM-5', asset: 'GC=F (Gold)', type: 'Market Sell', amount: '2 Contracts', price: '$2,340.50', status: 'Confirmed', time: '1 hour ago' },
  ]);

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKey && apiSecret) {
      setIsConnected(true);
      setWalletType('CEX');
      toast.success('Centralized Exchange API connected via encrypted broker.');
    }
  };

  const connectWeb3Wallet = async (providerName: 'MetaMask' | 'Talisman') => {
    try {
      let provider = null;
      if (providerName === 'MetaMask' && (window as any).ethereum) {
        provider = (window as any).ethereum;
        if (!provider.isMetaMask) {
          console.warn('Provider is not explicitly flagged as MetaMask (isMetaMask is false/undefined), continuing anyway...');
        }
        await provider.request({ method: 'eth_requestAccounts' });
      } else if (providerName === 'Talisman' && (window as any).talismanEth) {
        provider = (window as any).talismanEth;
        await provider.request({ method: 'eth_requestAccounts' });
      } else {
        throw new Error(`${providerName} extension not found in browser.`);
      }

      setIsConnected(true);
      setWalletType(providerName);
      toast.success(`${providerName} Wallet connected successfully! You can now execute on-chain zero-fee routes.`);
    } catch (e: any) {
      toast.error(`Connection failed: ${e.message}`);
    }
  };

  const handlePlaceOrder = (e: React.FormEvent) => {
    e.preventDefault();
    if (orderAsset && orderQuantity) {
      setShowConfirm(true);
    }
  };

  const executeOrder = () => {
    const txId = `tx-${Math.random().toString(16).slice(2, 8)}`;
    const actualPrice = orderType.includes('Limit') ? `${limitPrice}` : 'Market';

    const newTx = {
      id: txId,
      agent: 'Manual (User)',
      asset: orderAsset,
      type: orderType,
      amount: orderQuantity,
      price: actualPrice,
      status: 'Pending',
      time: 'Just now'
    };

    setExecutions([newTx, ...executions]);
    setShowConfirm(false);
    setOrderQuantity('');
    setLimitPrice('');

    // Push Notification (Toast) for Pending Status
    toast.loading(`[${txId}] ${orderType} order for ${orderQuantity} ${orderAsset} submitted...`, {
      id: txId,
      duration: 30000 // Keep alive until filled
    });

    // Simulate delayed execution to show "push notification" of status change
    setTimeout(() => {
      const mockPrice = (Math.random() * 500 + 50).toFixed(2);
      setExecutions(prev => prev.map(tx =>
        tx.id === txId
          ? { ...tx, status: 'Confirmed', price: `$${mockPrice}` }
          : tx
      ));

      // Update the loading toast to success
      toast.success(`[${txId}] Order Filled! executed ${orderQuantity} ${orderAsset} @ $${mockPrice}`, {
        id: txId,
        duration: 5000 // Disappears after 5s
      });
    }, 3000 + Math.random() * 2000); // Fills after 3-5 seconds
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-gradient-to-r from-blue-900/50 to-emerald-900/50 border border-slate-800 rounded-xl relative overflow-hidden p-8">
        <div className="absolute top-0 right-0 p-8 opacity-20">
          <ShieldCheck className="w-48 h-48" />
        </div>

        <div className="relative z-10">
          {!isConnected ? (
             <div className="space-y-8">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                Connect Your Wallet to the Zero-Fee Core
              </h2>
              <p className="text-slate-300 max-w-md">
                Securely connect to unleash the Eliza Syndicate. We route your trades through zero-fee automated dark pools via zero-knowledge proofs. Choose Web3 wallets for DeFi or CEX keys for traditional markets.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">
                {/* Web3 Wallets */}
                <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6 flex flex-col gap-4">
                  <h3 className="font-semibold text-slate-200">Web3 / DeFi Wallets</h3>
                  <p className="text-xs text-slate-400">Connect directly to EVM/Polkadot chains for arbitrage routing by Minimax-m2.7.</p>

                  <button
                    onClick={() => connectWeb3Wallet('MetaMask')}
                    className="w-full bg-[#F6851B] hover:bg-[#E2761B] text-white px-4 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 shadow-lg"
                  >
                    Connect MetaMask
                  </button>

                  <button
                    onClick={() => connectWeb3Wallet('Talisman')}
                    className="w-full bg-[#e6007a] hover:bg-[#c20066] text-white px-4 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 shadow-lg"
                  >
                    Connect Talisman
                  </button>
                </div>

                {/* CEX API Keys */}
                <form onSubmit={handleConnect} className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6 flex flex-col gap-4">
                  <h3 className="font-semibold text-slate-200">Centralized Auth (CEX)</h3>
                  <p className="text-xs text-slate-400">Required for traditional equities (Kimi-k2.5) and forex (GLM-5).</p>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1 flex items-center gap-1"><Key className="w-3 h-3" /> API Key</label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1 flex items-center gap-1"><Key className="w-3 h-3" /> API Secret</label>
                    <input
                      type="password"
                      value={apiSecret}
                      onChange={(e) => setApiSecret(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 text-white"
                    />
                  </div>
                  <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium transition-colors">
                    Secure Connect API
                  </button>
                </form>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="text-slate-400 text-lg">Live Account Balance</h2>
                  <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2 py-0.5 rounded flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
                    {walletType || 'CEX'} Connected
                  </span>
                </div>
                <div className="text-5xl font-bold text-white mb-8">$0.00</div>

                <div className="flex gap-4">
                  <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2">
                    <ArrowRightLeft className="w-4 h-4" />
                    Deposit Funds
                  </button>
                  <button
                    onClick={() => {
                      setIsConnected(false);
                      setWalletType(null);
                      toast.info("Wallet disconnected.");
                    }}
                    className="bg-slate-800 hover:bg-slate-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors border border-slate-700 flex items-center gap-2"
                  >
                    <Link className="w-4 h-4" />
                    Disconnect
                  </button>
                </div>

                {/* TAO Gas Tank */}
                <div className="mt-8 pt-6 border-t border-slate-700/50">
                  <div className="flex items-center gap-3 mb-2 text-purple-400 font-medium">
                    <Hexagon className="w-5 h-5 bg-purple-500/20 p-1 rounded" />
                    TAO Arbitrage Gas Tank
                  </div>
                  <div className="flex items-end justify-between bg-black/20 p-4 rounded-lg border border-purple-500/20">
                    <div>
                      <p className="text-slate-400 text-sm mb-1">Mined TAO Available for Gas</p>
                      <div className="text-3xl font-bold font-mono text-slate-100 tracking-tight">τ {taoGasPool.toFixed(2)}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-emerald-400 font-medium text-sm">Zero-Fee Routes: ACTIVE</div>
                      <div className="text-xs text-slate-500 mt-1">Cross-chain bridging from SN8</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-700 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-slate-200 mb-4">Manual Trade Execution</h3>
                {showConfirm ? (
                  <div className="bg-slate-800 border border-slate-600 rounded-lg p-5">
                    <h4 className="text-emerald-400 font-medium mb-3">Confirm Order</h4>
                    <p className="text-sm text-slate-300 mb-4">
                      Are you sure you want to place a <strong>{orderType}</strong> order for <strong>{orderQuantity} {orderAsset}</strong>?
                    </p>
                    <div className="flex gap-3">
                      <button
                        onClick={executeOrder}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                      >
                        Confirm Execute
                      </button>
                      <button
                        onClick={() => setShowConfirm(false)}
                        className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handlePlaceOrder} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Asset</label>
                      <input
                        type="text"
                        value={orderAsset}
                        onChange={(e) => setOrderAsset(e.target.value.toUpperCase())}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 text-white placeholder-slate-500"
                        placeholder="e.g. BTC, AAPL"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Quantity</label>
                      <input
                        type="number"
                        step="any"
                        value={orderQuantity}
                        onChange={(e) => setOrderQuantity(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 text-white placeholder-slate-500"
                        placeholder="Amount"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Type</label>
                      <select
                        value={orderType}
                        onChange={(e) => setOrderType(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 text-white"
                      >
                        <option value="Market Buy">Market Buy</option>
                        <option value="Limit Buy">Limit Buy</option>
                        <option value="Market Sell">Market Sell</option>
                        <option value="Limit Sell">Limit Sell</option>
                      </select>
                    </div>
                    <button
                      type="submit"
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      Review Order
                    </button>
                  </form>
                )}
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
              {executions.map((tx) => (
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
