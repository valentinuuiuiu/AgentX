import React, { useState } from 'react';
import { Activity, Users, MessageSquare, Wallet, BarChart2, Shield, Eye, Hexagon } from 'lucide-react';
import { Dashboard } from './components/Dashboard';
import { Team } from './components/Team';
import { Chat } from './components/Chat';
import { WalletView } from './components/Wallet';
import { RehoboamCore } from './components/RehoboamCore';
import { BittensorNode } from './components/BittensorNode';
import { Toaster } from 'sonner';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const isRehoboam = activeTab === 'rehoboam';

  return (
    <div className={`flex h-screen overflow-hidden font-sans ${isRehoboam ? 'bg-[#050505] text-slate-100' : 'bg-[#0f172a] text-slate-50'}`}>
      <Toaster theme="dark" position="bottom-right" />
      {/* Sidebar */}
      <aside className={`w-64 border-r flex flex-col transition-colors ${isRehoboam ? 'bg-black border-red-900/30' : 'bg-slate-900 border-slate-800'}`}>
        <div className="p-6 flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${isRehoboam ? 'bg-red-900/30 text-red-500 border border-red-500/30 animate-pulse' : 'bg-blue-600'}`}>
            {isRehoboam ? <Eye className="w-5 h-5 text-red-500" /> : <Activity className="w-5 h-5 text-white" />}
          </div>
          <div>
            <span className={`font-bold text-lg tracking-tight ${isRehoboam ? 'text-red-500 uppercase tracking-widest' : ''}`}>
              {isRehoboam ? 'REHOBOAM' : 'Eliza Syndicate'}
            </span>
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          <NavItem icon={<BarChart2 className="w-5 h-5" />} label="Dashboard" isActive={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} isRehoboam={isRehoboam} />
          <NavItem icon={<Wallet className="w-5 h-5" />} label="Zero-Fee Wallet" isActive={activeTab === 'wallet'} onClick={() => setActiveTab('wallet')} isRehoboam={isRehoboam} />
          <NavItem icon={<Users className="w-5 h-5" />} label="Agent Team" isActive={activeTab === 'team'} onClick={() => setActiveTab('team')} isRehoboam={isRehoboam} />
          <NavItem icon={<MessageSquare className="w-5 h-5" />} label="Terminal" isActive={activeTab === 'chat'} onClick={() => setActiveTab('chat')} isRehoboam={isRehoboam} />
          <NavItem icon={<Hexagon className="w-5 h-5" />} label="TAO Network" isActive={activeTab === 'bittensor'} onClick={() => setActiveTab('bittensor')} isRehoboam={isRehoboam} />
          
          <div className={`pt-4 mt-4 border-t ${isRehoboam ? 'border-red-900/30' : 'border-slate-800'}`}>
            <NavItem icon={<Eye className="w-5 h-5" />} label="Rehoboam Core" isActive={activeTab === 'rehoboam'} onClick={() => setActiveTab('rehoboam')} isRehoboam={isRehoboam} />
          </div>
        </nav>
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header className={`h-16 border-b flex items-center justify-between px-8 backdrop-blur-sm z-10 transition-colors ${isRehoboam ? 'border-red-900/30 bg-black/50' : 'border-slate-800 bg-slate-900/50'}`}>
          <h1 className={`text-xl font-semibold capitalize ${isRehoboam ? 'text-red-500 tracking-wider' : ''}`}>{activeTab.replace('-', ' ')}</h1>
          <div className="flex items-center gap-6">
            <div className={`flex items-center gap-2 text-sm px-3 py-1.5 rounded-full hidden sm:flex ${isRehoboam ? 'bg-red-900/20 text-red-400' : 'text-slate-400 bg-slate-800'}`}>
              <Shield className={`w-4 h-4 ${isRehoboam ? 'text-red-500' : 'text-emerald-500'}`} />
              {isRehoboam ? 'System Override' : 'Arbitrage Active'}
            </div>
            
            <div className="flex items-center gap-3 pl-4 border-l border-slate-700/50">
              <div className="text-right hidden md:block">
                <div className={`text-sm font-bold ${isRehoboam ? 'text-red-400' : 'text-slate-200'}`}>Eliza Syndicate</div>
                <div className={`text-xs ${isRehoboam ? 'text-red-600' : 'text-emerald-400'} font-mono uppercase tracking-widest`}>Ishvara Pranidana</div>
              </div>
              <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center relative overflow-hidden ${
                isRehoboam 
                  ? 'border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.5)]' 
                  : 'border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)]'
              }`}>
                <div className={`absolute inset-0 opacity-20 ${isRehoboam ? 'bg-red-500' : 'bg-blue-500'} animate-pulse`}></div>
                <Hexagon className={`w-6 h-6 ${isRehoboam ? 'text-red-400' : 'text-blue-400'} z-10`} />
              </div>
            </div>
          </div>
        </header>
        <div className={`flex-1 overflow-auto p-4 md:p-8 ${isRehoboam ? 'bg-gradient-to-b from-[#050505] to-black' : ''}`}>
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'wallet' && <WalletView />}
          {activeTab === 'team' && <Team />}
          {activeTab === 'chat' && <Chat />}
          {activeTab === 'bittensor' && <BittensorNode />}
          {activeTab === 'rehoboam' && <RehoboamCore />}
        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, isActive, onClick, isRehoboam }: { icon: React.ReactNode, label: string, isActive: boolean, onClick: () => void, isRehoboam: boolean }) {
  let activeClass = 'bg-blue-600/10 text-blue-400';
  let hoverClass = 'text-slate-400 hover:bg-slate-800 hover:text-slate-200';
  
  if (isRehoboam) {
    activeClass = 'bg-red-900/20 text-red-500 border border-red-900/50 shadow-[0_0_15px_rgba(239,68,68,0.1)]';
    hoverClass = 'text-red-500/50 hover:bg-red-900/10 hover:text-red-400';
  }

  return (
    <button onClick={onClick} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium ${isActive ? activeClass : hoverClass}`}>
      {icon}
      {label}
    </button>
  );
}
