import React, { useEffect } from 'react';
import { TradingProvider } from '../contexts/TradingContext';
import TradingInterface from '../components/TradingInterface';
import TradingChart from '../components/TradingChart';
import PriceCard from '../components/PriceCard';
import ArbitrageCard from '../components/ArbitrageCard';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

const TradingDashboard: React.FC = () => {
  // Staggered entrance animation for all sections
  useEffect(() => {
    const sections = document.querySelectorAll('.ag-section');
    gsap.from(sections, {
      y: 50,
      opacity: 0,
      duration: 0.8,
      ease: 'power3.out',
      stagger: 0.15,
      scrollTrigger: {
        trigger: sections[0],
        start: 'top 80%',
        toggleActions: 'play none none reverse',
      },
    });
  }, []);

  return (
    <TradingProvider>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 text-white relative overflow-hidden">
        {/* Floating gradient background for depth */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_var(--tw-gradient-stops))] from-purple-800/30 via-indigo-800/20 to-slate-900/10 pointer-events-none" />
        <header className="border-b border-gray-800 p-6 backdrop-blur-sm bg-gray-900/30">
          <div className="container mx-auto">
            <h1 className="text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-500 to-indigo-600">
              Rehoboam Dashboard
            </h1>
            <p className="text-gray-300 mt-2">
              AI‑Powered Multi‑Chain Trading with Antigravity UI
            </p>
          </div>
        </header>

        <main className="container mx-auto p-8 space-y-12">
          {/* Market Overview */}
          <section className="ag-section">
            <h2 className="text-3xl font-semibold mb-6 text-purple-200">Market Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {/* Price cards rendered by TradingInterface */}
              <PriceCard />
            </div>
          </section>

          {/* Trading UI */}
          <section className="ag-section grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-gray-800/50 backdrop-blur-md rounded-xl border border-purple-700 shadow-2xl p-6 transform hover:scale-105 transition-transform duration-300">
              <h2 className="text-2xl font-bold mb-4 text-pink-300">Trading Chart</h2>
              <TradingChart data={[]} />
            </div>
            <div className="bg-gray-800/50 backdrop-blur-md rounded-xl border border-purple-700 shadow-2xl p-6 transform hover:scale-105 transition-transform duration-300">
              <h2 className="text-2xl font-bold mb-4 text-pink-300">Trading Interface</h2>
              <TradingInterface />
            </div>
          </section>

          {/* Arbitrage Opportunities */}
          <section className="ag-section">
            <h2 className="text-3xl font-semibold mb-6 text-purple-200">Arbitrage Opportunities</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <ArbitrageCard />
            </div>
          </section>
        </main>
      </div>
    </TradingProvider>
  );
};

export default TradingDashboard;