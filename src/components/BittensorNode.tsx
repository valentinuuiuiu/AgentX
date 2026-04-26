import React, { useState, useEffect } from 'react';
import { Server, Cpu, Database, Network, Activity, Zap, Hexagon, ArrowUpRight, ArrowRightLeft } from 'lucide-react';
import { toast } from 'sonner';

export function BittensorNode() {
  const [taoBalance, setTaoBalance] = useState(1024.53);
  const [emissionRate, setEmissionRate] = useState(14.24);
  const [subnets, setSubnets] = useState([
    { id: 8, name: 'Time Series Prediction', uid: '3x...9a', stake: 'τ 500.0', incentive: '0.045', status: 'MINING' },
    { id: 1, name: 'Text Prompting', uid: '7c...2b', stake: 'τ 250.0', incentive: '0.012', status: 'MINING' },
    { id: 9, name: 'Pre-training', uid: '9f...11', stake: 'τ 150.0', incentive: '0.008', status: 'VALIDATING' },
    { id: 27, name: 'Compute Provision', uid: '2a...8c', stake: 'τ 124.5', incentive: '0.033', status: 'MINING' },
  ]);

  useEffect(() => {
    // Simulate TAO emission ticks
    const interval = setInterval(() => {
      setTaoBalance(prev => prev + 0.0001);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleBridgeTAO = () => {
    if (emissionRate > 0) {
      toast.success(`Routed ${emissionRate.toFixed(2)} TAO to Minimax Arbitrage Gas Tank via cross-chain bridge!`);
      setTaoBalance(prev => prev + emissionRate);
      setEmissionRate(0);
    } else {
      toast.error('No TAO emissions available to bridge right now.');
    }
  };

  return (
    <div className="space-y-6 max-w-6xl text-slate-200">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
            <Hexagon className="w-6 h-6 text-purple-500" />
            Bittensor (TAO) Node Management
          </h1>
          <p className="text-slate-400 text-sm">
            Decentralized intelligence scaling. Mining and validating subnets to power Rehoboam's prediction models while generating TAO emissions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-purple-500/10 border border-purple-500/30 text-purple-400 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
            Node Synced: Block 2,849,102
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric Cards */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <Hexagon className="w-16 h-16" />
          </div>
          <p className="text-slate-400 text-sm mb-1 font-medium">Total Staked</p>
          <div className="text-3xl font-bold text-white mb-2 tracking-tight">τ {taoBalance.toFixed(4)}</div>
          <div className="flex items-center gap-1 text-emerald-400 text-xs font-medium">
            <ArrowUpRight className="w-3 h-3" /> +12.4% (30d)
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden flex flex-col justify-between">
          <div>
            <p className="text-slate-400 text-sm mb-1 font-medium">Daily Emission</p>
            <div className="text-3xl font-bold text-white mb-2 tracking-tight">τ {emissionRate.toFixed(2)}</div>
            <div className="flex items-center gap-1 text-emerald-400 text-xs font-medium mb-4">
              <ArrowUpRight className="w-3 h-3" /> Optimizing Weights
            </div>
          </div>
          <button 
            onClick={handleBridgeTAO}
            className="w-full bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 border border-purple-500/30 rounded-lg py-1.5 text-xs font-bold transition-colors flex items-center justify-center gap-2"
          >
            <ArrowRightLeft className="w-3 h-3" /> Bridge to Gas Tank
          </button>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <p className="text-slate-400 text-sm mb-1 font-medium">Active Subnets</p>
          <div className="text-3xl font-bold text-white mb-2 tracking-tight">{subnets.length} / 32</div>
          <div className="text-slate-500 text-xs font-medium">Running bittensor 6.12.0</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <p className="text-slate-400 text-sm mb-1 font-medium">Consensus Trust</p>
          <div className="text-3xl font-bold text-purple-400 mb-2 tracking-tight">98.4%</div>
          <div className="text-slate-500 text-xs font-medium">Synergistic validation active</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-5 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
              <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                <Network className="w-4 h-4 text-purple-400" />
                Subnet Registrations
              </h3>
              <button className="text-xs bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded transition-colors font-medium">
                Register New UID
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase">
                  <tr>
                    <th className="px-5 py-3 font-medium">Subnet</th>
                    <th className="px-5 py-3 font-medium">HotKey UID</th>
                    <th className="px-5 py-3 font-medium">Role</th>
                    <th className="px-5 py-3 font-medium">Stake</th>
                    <th className="px-5 py-3 font-medium">Incentive</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {subnets.map(sn => (
                    <tr key={sn.id} className="hover:bg-slate-800/20 transition-colors">
                      <td className="px-5 py-3">
                        <div className="font-medium text-slate-200">SN{sn.id}</div>
                        <div className="text-xs text-slate-500">{sn.name}</div>
                      </td>
                      <td className="px-5 py-3 font-mono text-slate-400">{sn.uid}</td>
                      <td className="px-5 py-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium tracking-wide ${
                          sn.status === 'VALIDATING' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                        }`}>
                          {sn.status}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-mono text-emerald-400">{sn.stake}</td>
                      <td className="px-5 py-3 font-mono text-slate-300">{sn.incentive}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="font-semibold text-slate-200 flex items-center gap-2 mb-4">
              <Server className="w-4 h-4 text-slate-400" />
              Miner Hardware Stats
            </h3>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">GPU 0 (RTX 4090) Load</span>
                  <span className="text-emerald-400">92%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: '92%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">GPU 1 (RTX 4090) Load</span>
                  <span className="text-emerald-400">88%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: '88%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">VRAM Usage</span>
                  <span className="text-amber-400">42GB / 48GB</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: '85%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Network Bandwidth</span>
                  <span className="text-blue-400">1.2 Gbps</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: '60%' }}></div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
             <h3 className="font-semibold text-slate-200 flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-yellow-500" />
              Weight Copy Operation
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Rehoboam periodically copies the top weights from SN8 (Time Series Prediction) to update its internal simulation models directly from the decentralized Bittensor consensus.
            </p>
            <button className="w-full bg-slate-800 hover:bg-slate-700 text-white rounded-lg py-2 text-sm font-medium transition-colors border border-slate-700">
              Force Weight Sync Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
