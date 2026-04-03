import React, { useState } from 'react';
import { Activity, Users, MessageSquare, Wallet, BarChart2, Shield } from 'lucide-react';
import { Dashboard } from './components/Dashboard';
import { Team } from './components/Team';
import { Chat } from './components/Chat';
import { WalletView } from './components/Wallet';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="flex h-screen bg-[#0f172a] text-slate-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">Eliza Syndicate</span>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          <NavItem icon={<BarChart2 className="w-5 h-5" />} label="Dashboard" isActive={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <NavItem icon={<Wallet className="w-5 h-5" />} label="Zero-Fee Wallet" isActive={activeTab === 'wallet'} onClick={() => setActiveTab('wallet')} />
          <NavItem icon={<Users className="w-5 h-5" />} label="Agent Team" isActive={activeTab === 'team'} onClick={() => setActiveTab('team')} />
          <NavItem icon={<MessageSquare className="w-5 h-5" />} label="Terminal" isActive={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
        </nav>
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-900/50 backdrop-blur-sm z-10">
          <h1 className="text-xl font-semibold capitalize">{activeTab.replace('-', ' ')}</h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-400 bg-slate-800 px-3 py-1.5 rounded-full">
              <Shield className="w-4 h-4 text-emerald-500" />
              Arbitrage Active
            </div>
          </div>
        </header>
        <div className="flex-1 overflow-auto p-8">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'wallet' && <WalletView />}
          {activeTab === 'team' && <Team />}
          {activeTab === 'chat' && <Chat />}
        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, isActive, onClick }: { icon: React.ReactNode, label: string, isActive: boolean, onClick: () => void }) {
  return (
    <button onClick={onClick} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium ${isActive ? 'bg-blue-600/10 text-blue-400' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}>
      {icon}
      {label}
    </button>
  );
}
