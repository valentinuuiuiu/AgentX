import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { Target, Activity, AlertTriangle, Crosshair, Eye, Cpu, Database, Network } from 'lucide-react';

export function RehoboamCore() {
  const [divergenceData, setDivergenceData] = useState<any[]>([]);
  const [anomalyLogs, setAnomalyLogs] = useState<string[]>([]);

  useEffect(() => {
    // Generate simulated divergence data
    const generateData = () => {
      const data = [];
      let baseline = 50;
      for (let i = 0; i < 60; i++) {
        baseline += (Math.random() - 0.5) * 5;
        data.push({
          time: i,
          projected: baseline,
          actual: baseline + (Math.random() - 0.5) * 15,
          divergence: Math.random() * 10
        });
      }
      setDivergenceData(data);
    };

    generateData();
    const interval = setInterval(generateData, 5000);
    return () => clearInterval(interval);
  }, []);

  const systemMetrics = [
    { subject: 'Macro Sentiment', A: 120, fullMark: 150 },
    { subject: 'Liquidity', A: 98, fullMark: 150 },
    { subject: 'Volatility', A: 86, fullMark: 150 },
    { subject: 'Arbitrage Opps', A: 99, fullMark: 150 },
    { subject: 'Risk Variance', A: 85, fullMark: 150 },
    { subject: 'Capital Flow', A: 65, fullMark: 150 },
  ];

  return (
    <div className="space-y-6 bg-[#050505] min-h-full p-2 text-slate-300 font-mono">
      <div className="flex items-center justify-between border-b border-red-900/30 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tighter text-white flex items-center gap-3 uppercase">
            <Eye className="w-8 h-8 text-red-600" />
            Rehoboam Framework
          </h1>
          <p className="text-red-500/70 text-sm tracking-widest mt-1">GLOBAL ASSET PREDICTION SYSTEM V4.0 // ACTIVE</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse" />
            <span className="text-red-500 uppercase tracking-widest">System Divergence: Nominal</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Visualization */}
        <div className="lg:col-span-2 relative bg-black border border-red-900/20 rounded-xl p-6 overflow-hidden flex flex-col items-center justify-center min-h-[500px]">
          {/* Decorative glowing background rings */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
            <div className="w-[400px] h-[400px] border border-red-500 rounded-full animate-[spin_60s_linear_infinite]" />
            <div className="w-[300px] h-[300px] border border-red-500 border-dashed rounded-full absolute animate-[spin_40s_linear_infinite_reverse]" />
            <div className="w-[200px] h-[200px] border border-red-500 rounded-full absolute animate-[ping_4s_cubic-bezier(0,0,0.2,1)_infinite]" />
          </div>

          <div className="z-10 w-full flex justify-between items-start mb-4">
             <h2 className="text-white/80 font-bold uppercase tracking-widest text-sm flex items-center gap-2">
               <Activity className="w-4 h-4 text-red-500" />
               Trajectory Divergence Analysis
             </h2>
             <span className="text-red-500 font-bold text-xl">D-0.24%</span>
          </div>
          
          <div className="w-full h-80 z-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={divergenceData}>
                <defs>
                  <linearGradient id="colorProjected" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ffffff" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#ffffff" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" hide />
                <YAxis domain={['auto', 'auto']} hide />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#000', borderColor: '#7f1d1d', borderRadius: '4px', fontFamily: 'monospace' }}
                  itemStyle={{ color: '#ef4444' }}
                />
                <Area type="monotone" dataKey="projected" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorProjected)" />
                <Area type="monotone" dataKey="actual" stroke="#ffffff" strokeWidth={1} strokeDasharray="3 3" fillOpacity={1} fill="url(#colorActual)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          <div className="w-full grid grid-cols-4 gap-4 mt-8 z-10 border-t border-red-900/30 pt-6">
            <div className="text-center">
              <div className="text-red-600/50 text-[10px] uppercase tracking-wider mb-1">Compute Load</div>
              <div className="text-white font-bold text-lg">94.2%</div>
            </div>
            <div className="text-center border-l border-red-900/30">
              <div className="text-red-600/50 text-[10px] uppercase tracking-wider mb-1">Market Vectors</div>
              <div className="text-white font-bold text-lg">3,402</div>
            </div>
            <div className="text-center border-l border-red-900/30">
              <div className="text-red-600/50 text-[10px] uppercase tracking-wider mb-1">Confidence</div>
              <div className="text-emerald-500 font-bold text-lg">99.1%</div>
            </div>
            <div className="text-center border-l border-red-900/30">
              <div className="text-red-600/50 text-[10px] uppercase tracking-wider mb-1">Anomalies</div>
              <div className="text-red-500 font-bold text-lg animate-pulse">2 DETECTED</div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Radar Chart */}
          <div className="bg-black border border-red-900/20 rounded-xl p-6 relative overflow-hidden">
             <h2 className="text-white/80 font-bold uppercase tracking-widest text-sm mb-4 flex items-center gap-2">
               <Crosshair className="w-4 h-4 text-red-500" />
               Agent Synergy Matrix
             </h2>
             <div className="h-48">
               <ResponsiveContainer width="100%" height="100%">
                 <RadarChart cx="50%" cy="50%" outerRadius="80%" data={systemMetrics}>
                   <PolarGrid stroke="#7f1d1d" strokeOpacity={0.3} />
                   <PolarAngleAxis dataKey="subject" tick={{ fill: '#ef4444', fontSize: 9, fontFamily: 'monospace' }} />
                   <PolarRadiusAxis angle={30} domain={[0, 150]} tick={false} axisLine={false} />
                   <Radar name="Strategy" dataKey="A" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
                 </RadarChart>
               </ResponsiveContainer>
             </div>
          </div>

          {/* Anomaly Log */}
          <div className="bg-black border border-red-900/20 rounded-xl p-6 h-64 flex flex-col">
            <h2 className="text-white/80 font-bold uppercase tracking-widest text-sm mb-4 flex items-center gap-2 border-b border-red-900/30 pb-2">
               <AlertTriangle className="w-4 h-4 text-red-500" />
               Critical Path Interventions
             </h2>
             <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                {[
                  { time: 'JUST NOW', msg: 'SYSTEM CHECK: ARCHITECTURE DIRECTIVE "REHOBOAM_INSTRUCTIONS_FOR_JULES.md" WRITTEN TO ROOT.', level: 'critical' },
                  { time: 'T-00:02', msg: 'JULES AUTHENTICATED. WAITING FOR WEB-SOCKET BINDING TO PYTHON ML CORE.', level: 'warn' },
                  { time: '10:42:01', msg: 'Divergence detected in EUR/USD flow. Injecting liquidity simulation.', level: 'info' },
                  { time: '10:41:15', msg: 'KIMI-K2.5 proposed standard deviations exceed risk parameters. Adjusting.', level: 'info' },
                  { time: '10:39:44', msg: 'UNANTICIPATED VOLATILITY IN NASDAQ (NQ=F). REROUTING CORE LOGIC.', level: 'critical' },
                ].map((log, i) => (
                  <div key={i} className="flex gap-3 text-xs border-l-2 pl-2" style={{ borderColor: log.level === 'critical' ? '#ef4444' : log.level === 'warn' ? '#f59e0b' : '#3b82f6' }}>
                    <span className="text-red-500/50 shrink-0">[{log.time}]</span>
                    <span className={log.level === 'critical' ? 'text-red-400 font-bold' : log.level === 'warn' ? 'text-amber-400' : 'text-slate-400'}>{log.msg}</span>
                  </div>
                ))}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
