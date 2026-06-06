import React from "react";

export default function Sidebar({ activeTab, setActiveTab }) {
  const items = [
    { id: "dashboard", label: "Dashboard" },
    { id: "arbitrage", label: "Flash Arb" },
    { id: "portfolio", label: "Portfolio" },
    { id: "ai", label: "AI" },
  ];
  return (
    <aside className="w-56 bg-[#0a0a15] border-r border-[#1a1a2e] flex flex-col">
      <nav className="flex-1 p-3">
        {items.map((it) => (
          <button
            key={it.id}
            onClick={() => setActiveTab(it.id)}
            className={`w-full text-left px-3 py-2.5 rounded $
              {activeTab === it.id
                ? "bg-indigo-600/20 text-white border border-indigo-500/30"
                : "text-slate-400 hover:text-white hover:bg-[#1a1a2e]"}`}
          >
            {it.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
