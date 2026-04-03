import React from 'react';
import { BrainCircuit, LineChart, Coins, Wrench } from 'lucide-react';

const agents = [
  {
    name: 'Kimi-k2.5',
    role: 'Equities & S&P 500 Specialist',
    description: 'Analyzes macroeconomic trends and executes trades on traditional equities and indices.',
    icon: <LineChart className="w-6 h-6 text-blue-400" />,
    status: 'Active',
  },
  {
    name: 'Minimax-m2.7',
    role: 'Cross-Chain Arbitrage',
    description: 'Scans multiple blockchains (Ethereum, Arbitrum, Optimism) for zero-fee arbitrage opportunities.',
    icon: <BrainCircuit className="w-6 h-6 text-purple-400" />,
    status: 'Scanning',
  },
  {
    name: 'GLM-5',
    role: 'Metals & Forex',
    description: 'Monitors precious metals (Gold, Silver) and major currency pairs for high-probability setups.',
    icon: <Coins className="w-6 h-6 text-amber-400" />,
    status: 'Active',
  },
  {
    name: 'Helper Agent',
    role: 'Project & Dev Ops',
    description: 'Assists with system maintenance, debt management, and coordinates the trading syndicate.',
    icon: <Wrench className="w-6 h-6 text-emerald-400" />,
    status: 'Standing By',
  }
];

export function Team() {
  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2">Eliza Syndicate Team</h2>
        <p className="text-slate-400">Powered by Nvidia NIM API. Manage your specialized trading and helper agents.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {agents.map((agent) => (
          <div key={agent.name} className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-slate-800 flex items-center justify-center">
                  {agent.icon}
                </div>
                <div>
                  <h3 className="text-lg font-semibold">{agent.name}</h3>
                  <span className="text-sm text-slate-400">{agent.role}</span>
                </div>
              </div>
              <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                agent.status === 'Active' ? 'bg-emerald-500/10 text-emerald-400' :
                agent.status === 'Scanning' ? 'bg-blue-500/10 text-blue-400' :
                'bg-slate-800 text-slate-300'
              }`}>
                {agent.status}
              </span>
            </div>
            <p className="text-slate-300 text-sm flex-1">{agent.description}</p>
            <div className="mt-6 pt-4 border-t border-slate-800 flex gap-3">
              <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-white py-2 rounded-lg text-sm font-medium transition-colors">
                Configure
              </button>
              <button className="flex-1 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 py-2 rounded-lg text-sm font-medium transition-colors">
                View Logs
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
