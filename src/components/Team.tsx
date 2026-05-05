import React, { useState, useEffect } from 'react';
import { BrainCircuit, LineChart as LineChartIcon, Coins, Wrench, Sparkles, Terminal, Activity, CheckCircle, Clock } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, YAxis, Tooltip } from 'recharts';
import Avatar from 'boring-avatars';

const generateAvatarColors = (seed: string, primaryColor: string) => {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash) % 360;
  const s = 65 + (Math.abs(hash >> 1) % 20);
  const l = 30 + (Math.abs(hash >> 2) % 20);
  return [
    primaryColor,
    `hsl(${(h + 40) % 360}, ${s}%, ${l}%)`,
    `hsl(${(h + 120) % 360}, ${s}%, ${Math.max(20, l - 10)}%)`,
    `hsl(${(h + 180) % 360}, ${s}%, ${Math.min(80, l + 15)}%)`,
    `hsl(${(h + 240) % 360}, ${s}%, ${l + 5}%)`
  ];
};

const generatePerformanceData = () => {
  return Array.from({ length: 20 }, (_, i) => ({
    time: i,
    value: Math.floor(Math.random() * 40) + 60 + (Math.random() * 20 - 10)
  }));
};

const initialAgents = [
  {
    name: 'Genspark-Prime',
    role: 'The Super Agent',
    description: 'A highly elevated, holistic agent belonging to no one and to all. Connects data and philosophy.',
    icon: <Sparkles className="w-6 h-6 text-fuchsia-400" />,
    status: 'Ascended',
    workload: 12,
    activeTasks: ['Global Sentiment Analysis', 'Philosophical Alignment'],
    performance: generatePerformanceData(),
    color: '#e879f9'
  },
  {
    name: 'DeepSeek-V4-Pro',
    role: 'Equities & TradFi Specialist',
    description: 'Analyzes macroeconomic trends and executes trades on traditional equities and indices.',
    icon: <LineChartIcon className="w-6 h-6 text-blue-400" />,
    status: 'Active',
    workload: 85,
    activeTasks: ['Scanning traditional markets', 'Monitoring Fed speak'],
    performance: generatePerformanceData(),
    color: '#60a5fa'
  },
  {
    name: 'MiniMax-m2.7',
    role: 'Cross-Chain Arbitrage',
    description: 'Scans multiple blockchains (Ethereum, Arbitrum, Optimism) for zero-fee arbitrage opportunities.',
    icon: <BrainCircuit className="w-6 h-6 text-purple-400" />,
    status: 'Scanning',
    workload: 92,
    activeTasks: ['ETH/USDC spread analysis', 'Bridge latency check'],
    performance: generatePerformanceData(),
    color: '#c084fc'
  },
  {
    name: 'GLM-5.1',
    role: 'Metals & Forex',
    description: 'Monitors precious metals (Gold, Silver) and major currency pairs for high-probability setups.',
    icon: <Coins className="w-6 h-6 text-amber-400" />,
    status: 'Active',
    workload: 45,
    activeTasks: ['Gold chart technicals', 'EUR/USD volume analysis'],
    performance: generatePerformanceData(),
    color: '#fbbf24'
  },
  {
    name: 'Helper Agent',
    role: 'Project & Dev Ops',
    description: 'Assists with system maintenance, debt management, and coordinates the trading syndicate.',
    icon: <Wrench className="w-6 h-6 text-emerald-400" />,
    status: 'Standing By',
    workload: 5,
    activeTasks: ['Log rotation', 'Health checks'],
    performance: generatePerformanceData(),
    color: '#34d399'
  },
  {
    name: 'Cipher-Q',
    role: 'Web3 Protocol Architect',
    description: 'Autonomous scanner monitoring GitHub for new Web3 repos, testing and auditing smart contracts.',
    icon: <Terminal className="w-6 h-6 text-indigo-400" />,
    status: 'Active',
    workload: 68,
    activeTasks: ['Auditing new DEX repo', 'Cloning sol files'],
    performance: generatePerformanceData(),
    color: '#818cf8'
  },
  {
    name: 'Leviathan-X',
    role: 'On-Chain Whale Tracker & MEV',
    description: 'Monitors mempools for large transactions, front-running opportunities, and whale accumulation.',
    icon: <Activity className="w-6 h-6 text-cyan-400" />,
    status: 'Scanning',
    workload: 88,
    activeTasks: ['Tracking 0x...7aB2', 'MEV Sandwich Scan'],
    performance: generatePerformanceData(),
    color: '#22d3ee'
  }
];

export function Team() {
  const [agents, setAgents] = useState(initialAgents);
  const [showLogs, setShowLogs] = useState<string | null>(null);
  const [cipherLogs, setCipherLogs] = useState<any[]>([]);

  const fetchCipherLogs = async () => {
    try {
      const res = await fetch('/api/cipher-reports');
      const data = await res.json();
      setCipherLogs(data);
    } catch (e) {
      console.error("Failed to fetch cipher logs", e);
    }
  };

  useEffect(() => {
    if (showLogs === 'Cipher-Q') {
       fetchCipherLogs();
       const logInterval = setInterval(fetchCipherLogs, 15000);
       return () => clearInterval(logInterval);
    }
  }, [showLogs]);

  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => ({
        ...agent,
        workload: Math.max(0, Math.min(100, agent.workload + (Math.random() * 10 - 5))),
        performance: [
          ...agent.performance.slice(1),
          { time: Date.now(), value: Math.max(40, Math.min(100, agent.performance[agent.performance.length - 1].value + (Math.random() * 10 - 5))) }
        ]
      })));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <BrainCircuit className="w-6 h-6 text-purple-400" />
          Eliza Syndicate Team
        </h2>
        <p className="text-slate-400">Powered by Nvidia NIM API. Manage specialized trading agents and monitor real-time node workloads.</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {agents.map((agent) => (
          <div key={agent.name} className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col shadow-lg transition-all hover:border-slate-700">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="relative w-12 h-12 rounded-lg flex items-center justify-center border border-slate-700 bg-slate-800 overflow-hidden shadow-inner">
                  <Avatar
                    size={48}
                    name={agent.name}
                    variant="beam"
                    colors={generateAvatarColors(`${agent.name}-${agent.role}`, agent.color)}
                  />
                  <div className="absolute -bottom-1 -right-1 bg-slate-900 rounded-tl-lg p-1 border-t border-l border-slate-700 shadow-lg">
                    {React.cloneElement(agent.icon, { className: `w-3 h-3 ${agent.icon.props.className.split(' ').find(c => c.startsWith('text-')) || ''}` })}
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-100">{agent.name}</h3>
                  <span className="text-sm font-mono text-slate-400">{agent.role}</span>
                </div>
              </div>
              <span className={`px-2.5 py-1 rounded-full text-xs font-bold tracking-wider uppercase border ${
                agent.status === 'Active' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                agent.status === 'Scanning' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                agent.status === 'Ascended' ? 'bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/30 shadow-[0_0_15px_rgba(192,38,211,0.3)]' :
                'bg-slate-800 text-slate-300 border-slate-700'
              }`}>
                {agent.status}
              </span>
            </div>
            
            <p className="text-slate-300 text-sm mb-5 min-h-[40px]">{agent.description}</p>

            {/* Metrics Sub-grid */}
            <div className="grid grid-cols-2 gap-4 mb-5">
              <div className="bg-slate-950 rounded-lg p-3 border border-slate-800/60">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-xs text-slate-500 uppercase tracking-widest font-semibold flex items-center gap-1">
                    <Activity className="w-3 h-3" /> Workload CPU
                  </span>
                  <span className="text-sm font-mono font-bold text-slate-300">{agent.workload.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div 
                    className="h-1.5 rounded-full transition-all duration-500" 
                    style={{ 
                      width: `${agent.workload}%`, 
                      backgroundColor: agent.workload > 80 ? '#ef4444' : agent.workload > 50 ? '#eab308' : '#3b82f6' 
                    }}
                  ></div>
                </div>
              </div>

              <div className="bg-slate-950 rounded-lg p-3 border border-slate-800/60 flex flex-col justify-center">
                <span className="text-xs text-slate-500 uppercase tracking-widest font-semibold flex items-center gap-1 mb-1">
                  <CheckCircle className="w-3 h-3" /> Active Tasks
                </span>
                <span className="text-sm font-semibold text-slate-300 truncate" title={agent.activeTasks[0]}>
                  {agent.activeTasks.length > 0 ? agent.activeTasks[0] : 'Idle'}
                </span>
              </div>
            </div>

            {/* Performance Graph */}
            <div className="bg-slate-950 rounded-lg p-4 border border-slate-800/60 mb-5 relative">
              <span className="absolute top-2 left-3 text-[10px] text-slate-500 uppercase tracking-widest font-bold z-10 flex items-center gap-1">
                <Clock className="w-3 h-3" /> Performance Sync
              </span>
              <div className="h-20 w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={agent.performance}>
                    <YAxis domain={['dataMin - 10', 'dataMax + 10']} hide />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', fontSize: '12px' }}
                      itemStyle={{ color: agent.color }}
                      labelStyle={{ display: 'none' }}
                      formatter={(value: number) => [`${value.toFixed(1)} OPS`, 'Performance']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke={agent.color} 
                      strokeWidth={2} 
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-auto pt-4 border-t border-slate-800 flex gap-3">
              <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-white py-2 rounded-lg text-sm font-medium transition-colors border border-slate-700 hover:border-slate-600">
                Configure Protocol
              </button>
              <button 
                onClick={() => setShowLogs(agent.name)}
                className="flex-1 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 py-2 rounded-lg text-sm font-medium transition-colors border border-indigo-500/20"
              >
                View Agent Logs
              </button>
            </div>
          </div>
        ))}
      </div>

      {showLogs && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowLogs(null)}>
          <div className="bg-[#0a0a14] border border-[#1a1a2e] rounded-xl w-full max-w-3xl max-h-[80vh] flex flex-col shadow-[0_0_50px_rgba(0,0,0,0.5)]" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center p-4 border-b border-[#1a1a2e]">
              <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <Terminal className="w-5 h-5 text-indigo-400" /> 
                {showLogs} // Execution Logs
              </h3>
              <button onClick={() => setShowLogs(null)} className="text-slate-500 hover:text-slate-300">
                <Wrench className="w-5 h-5 rotate-45" /> {/* Close icon lookalike */}
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1 font-mono text-sm space-y-4">
              {showLogs === 'Cipher-Q' ? (
                 cipherLogs.length > 0 ? cipherLogs.map((log) => (
                   <div key={log.id} className="bg-slate-900 border border-slate-800 p-4 rounded-lg text-slate-300">
                     <div className="flex justify-between text-xs text-indigo-400 mb-2">
                       <span>{new Date(log.timestamp).toLocaleString()}</span>
                       <span>Target: {log.repoName}</span>
                     </div>
                     <div className="mb-2 text-slate-400">Stars: {log.stars} | URL: <a href={log.url} target="_blank" className="text-blue-400 hover:underline">{log.url}</a></div>
                     <div className="whitespace-pre-wrap text-emerald-400/90 leading-relaxed border-l-2 border-emerald-500/30 pl-3">
                       {log.report}
                     </div>
                   </div>
                 )) : (
                   <div className="text-slate-500 animate-pulse text-center py-10">Awaiting GitHub Webhooks & Neural Audits...</div>
                 )
              ) : (
                <div className="text-slate-500 flex flex-col items-center justify-center py-10">
                   <Activity className="w-8 h-8 mb-4 animate-spin text-slate-700" />
                   <span>Real-time log streaming for {showLogs} is currently restricted to VPS deployment.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

