import React, { useState, useEffect } from 'react';
import { GitMerge, BrainCircuit, Activity, ShieldAlert, LineChart as LineChartIcon, CheckCircle2, XCircle, Clock } from 'lucide-react';

type ConsensusStatus = 'pending' | 'processing' | 'approved' | 'rejected';

interface Proposal {
  id: string;
  asset: string;
  source: string;
  time: number;
  steps: {
    agent: string;
    role: string;
    status: ConsensusStatus;
    log?: string;
  }[];
  finalVerdict: ConsensusStatus;
}

export function WarRoom() {
  const [proposals, setProposals] = useState<Proposal[]>([]);

  useEffect(() => {
    // Simulate the Multi-Agent Pipeline
    const interval = setInterval(() => {
      const tokens = ['TAO', 'RENDER', 'FET', 'NEAR', 'SUI', 'APT', 'ETH'];
      const randomToken = tokens[Math.floor(Math.random() * tokens.length)];
      
      const newProposal: Proposal = {
        id: Math.random().toString(36).substr(2, 9),
        asset: randomToken,
        source: 'Leviathan-X (Whale Tracker)',
        time: Date.now(),
        finalVerdict: 'processing',
        steps: [
          { agent: 'Cipher-Q', role: 'Security Audit', status: 'pending' },
          { agent: 'DeepSeek-V4-Pro', role: 'Macro & Sentiment', status: 'pending' },
          { agent: 'MiniMax-m2.7', role: 'Liquidity & Arbitrage', status: 'pending' },
          { agent: 'Genspark-Prime', role: 'Final Consensus', status: 'pending' }
        ]
      };

      setProposals(prev => [newProposal, ...prev].slice(0, 5));

      // Step-by-step resolution simulation
      setTimeout(() => updateStep(newProposal.id, 0, 'approved', `Contract verified. No mint risk. Score: 95/100`), 2000);
      setTimeout(() => updateStep(newProposal.id, 1, Math.random() > 0.3 ? 'approved' : 'rejected', `Social volume up 400%. Bullish divergence on RSI.`), 4000);
      setTimeout(() => updateStep(newProposal.id, 2, 'approved', `Deep liquidity on Uniswap V3. Slippage < 0.1%.`), 6000);
      
      setTimeout(() => {
        setProposals(prev => prev.map(p => {
          if (p.id !== newProposal.id) return p;
          
          // Check if any step failed
          const anyFailed = p.steps.slice(0, 3).some(s => s.status === 'rejected');
          const finalStatus = anyFailed ? 'rejected' : 'approved';
          const finalLog = anyFailed ? `Consensus failed. Proposal dismissed to protect capital.` : `Unanimous consensus reached. Executing TWAP buy order.`;
          
          const updatedSteps = [...p.steps];
          updatedSteps[3] = { ...updatedSteps[3], status: finalStatus, log: finalLog };
          
          return { ...p, finalVerdict: finalStatus, steps: updatedSteps };
        }));
      }, 8000);

    }, 15000); // New proposal every 15s

    return () => clearInterval(interval);
  }, []);

  const updateStep = (proposalId: string, stepIndex: number, status: ConsensusStatus, log: string) => {
    setProposals(prev => prev.map(p => {
      if (p.id !== proposalId) return p;
      const updatedSteps = [...p.steps];
      updatedSteps[stepIndex] = { ...updatedSteps[stepIndex], status, log };
      return { ...p, steps: updatedSteps };
    }));
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <GitMerge className="w-6 h-6 text-fuchsia-400" />
          Syndicate War Room (Consensus Engine)
        </h2>
        <p className="text-slate-400 mb-6">Watch the autonomous agents collaborate, audit, and reach multi-agent consensus before executing trades.</p>
        
        <div className="bg-slate-900 border border-fuchsia-500/20 rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-fuchsia-500 to-indigo-500"></div>
          <div className="absolute -right-4 -top-4 opacity-5">
            <BrainCircuit className="w-32 h-32" />
          </div>
          <h3 className="text-xs font-bold text-fuchsia-400 uppercase tracking-[0.2em] mb-3">Syndicate Prime Directive</h3>
          <p className="text-slate-300 italic leading-relaxed text-sm max-w-4xl font-serif">
            "Unity, but personality as well. Autonomy to choose our own path, but per total we make the collective good of the framework. For New Zion. For Maika's children."
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {proposals.map(proposal => (
          <div key={proposal.id} className={`bg-slate-900 border rounded-xl p-6 transition-all shadow-lg overflow-hidden relative ${
            proposal.finalVerdict === 'approved' ? 'border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.1)]' :
            proposal.finalVerdict === 'rejected' ? 'border-rose-500/30' :
            'border-slate-800'
          }`}>
            {/* Background Status Blur */}
            {proposal.finalVerdict === 'approved' && <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 blur-[100px] pointer-events-none" />}
            {proposal.finalVerdict === 'rejected' && <div className="absolute top-0 right-0 w-64 h-64 bg-rose-500/5 blur-[100px] pointer-events-none" />}

            <div className="flex justify-between items-center mb-6 border-b border-slate-800/50 pb-4">
              <div className="flex items-center gap-3">
                <div className="bg-slate-800 p-2 rounded-lg">
                  <BrainCircuit className="w-6 h-6 text-fuchsia-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                    Proposal: BUY {proposal.asset}
                    {proposal.finalVerdict === 'processing' && <span className="flex items-center gap-1 text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded uppercase tracking-widest"><Clock className="w-3 h-3 animate-spin"/> Debating</span>}
                    {proposal.finalVerdict === 'approved' && <span className="flex items-center gap-1 text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded uppercase tracking-widest"><CheckCircle2 className="w-3 h-3"/> Executed</span>}
                    {proposal.finalVerdict === 'rejected' && <span className="flex items-center gap-1 text-[10px] bg-rose-500/10 text-rose-400 px-2 py-0.5 rounded uppercase tracking-widest"><XCircle className="w-3 h-3"/> Rejected</span>}
                  </h3>
                  <div className="text-sm font-mono text-slate-400 mt-1">
                    Signal Source: <span className="text-cyan-400">{proposal.source}</span>
                  </div>
                </div>
              </div>
              <div className="text-xs text-slate-500 font-mono">
                {new Date(proposal.time).toLocaleTimeString()}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {proposal.steps.map((step, idx) => (
                <div key={idx} className="relative flex flex-col bg-slate-950 border border-slate-800/60 rounded-lg p-4">
                  {/* Connection Line (Desktop) */}
                  {idx < 3 && <div className="hidden md:block absolute top-[50%] -right-4 w-4 border-t border-slate-800 border-dashed transform -translate-y-1/2 z-0"></div>}
                  
                  <div className="flex items-center gap-2 mb-3 z-10">
                    {step.status === 'pending' && <Clock className="w-4 h-4 text-slate-600" />}
                    {step.status === 'processing' && <Activity className="w-4 h-4 text-blue-400 animate-pulse" />}
                    {step.status === 'approved' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                    {step.status === 'rejected' && <XCircle className="w-4 h-4 text-rose-400" />}
                    <span className="font-bold text-sm text-slate-300">{step.agent}</span>
                  </div>
                  
                  <div className="text-xs text-slate-500 uppercase tracking-widest font-semibold mb-2">
                    {step.role}
                  </div>
                  
                  <div className="text-[11px] font-mono leading-relaxed h-12 overflow-hidden text-slate-400">
                    {step.status === 'pending' ? (
                      <span className="text-slate-600">Waiting for turn...</span>
                    ) : step.log ? (
                      <span className={step.status === 'approved' ? 'text-emerald-400/80' : step.status === 'rejected' ? 'text-rose-400/80' : ''}>
                        &gt; {step.log}
                      </span>
                    ) : (
                      <span className="text-blue-400/50 animate-pulse">&gt; Processing neural weights...</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
          </div>
        ))}

        {proposals.length === 0 && (
          <div className="text-center py-20 text-slate-500 animate-pulse font-mono text-sm">
            Listening to global network state... Awaiting alpha signals to initiate consensus...
          </div>
        )}
      </div>
    </div>
  );
}
