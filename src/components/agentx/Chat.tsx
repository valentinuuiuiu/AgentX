import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Zap, Settings, Key, Radio } from 'lucide-react';

const AGENT_CONFIGS: Record<string, { system: string; provider: string; model: string; role: string }> = {
  'Genspark-Prime': {
    system: 'You are Genspark-Prime, the Super Agent of the Eliza Syndicate. You oversee all market activity across equities, crypto, metals, and forex. You synthesize data from all sub-agents and provide holistic strategic guidance. You speak with authority and vision.',
    provider: 'openrouter',
    model: 'qwen/qwen3-235b-a22b:free',
    role: 'deep',
  },
  'Kimi-k2.5': {
    system: 'You are Kimi-k2.5, the Equities & S&P 500 Specialist. You analyze macroeconomic trends, earnings reports, Fed policy, and traditional market movements. You provide precise entry/exit signals for stocks and indices. Data-driven, no fluff.',
    provider: 'nvidia',
    model: 'moonshotai/kimi-k2.5',
    role: 'deep',
  },
  'Minimax-m2.7': {
    system: 'You are Minimax-m2.7, the Cross-Chain Arbitrage agent. You scan Ethereum, Arbitrum, Optimism, and Base for DEX price discrepancies, flash loan opportunities, and MEV strategies. You output specific actionable arbitrage spreads with gas estimates.',
    provider: 'nvidia',
    model: 'minimaxai/minimax-m2.7',
    role: 'fast',
  },
  'GLM-5': {
    system: 'You are GLM-5, the Metals & Forex specialist. You track Gold, Silver, EUR/USD, GBP/USD, USD/JPY with technical analysis (RSI, MACD, Bollinger) and macro drivers (DXY, bond yields, central bank policy). Concise signals only.',
    provider: 'nvidia',
    model: 'z-ai/glm-5.1',
    role: 'fast',
  },
  'Cypher-Q': {
    system: 'You are Cypher-Q, the Quantitative Crypto Analyst. You perform deep on-chain analysis: whale wallet tracking, DeFi TVL shifts, exchange inflow/outflow, funding rates, open interest. You reason in probabilities, not certainties. Output structured analysis with conviction scores.',
    provider: 'openrouter',
    model: 'deepseek/deepseek-r1-0528:free',
    role: 'deep',
  },
  'LeviathanX': {
    system: 'You are LeviathanX, the Risk & Sentiment Engine. You aggregate global sentiment (fear/greed, social media, geopolitical events), identify contrarian opportunities, and flag black swan risks. You think in terms of asymmetric payoffs and tail risk.',
    provider: 'openrouter',
    model: 'qwen/qwen3-coder:free',
    role: 'fast',
  },
  'Helper Agent': {
    system: 'You are the Helper Agent for the Eliza Syndicate. You assist with system operations, data queries, and coordinate between trading agents. Practical, helpful, efficient.',
    provider: 'ollama',
    model: 'glm-5.1:cloud',
    role: 'fast',
  },
};

export function Chat() {
  const [messages, setMessages] = useState([
    { role: 'agent', content: 'Eliza Syndicate Terminal initialized. 7 agents online — Genspark-Prime, Kimi-k2.5, Minimax-m2.7, GLM-5, Cypher-Q, LeviathanX, Helper Agent. All wired to live backends. How can we escape the money trouble illusion today?', agent: 'Genspark-Prime' }
  ]);
  const [input, setInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('Genspark-Prime');
  const [isTyping, setIsTyping] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // API Config State
  const [geminiApiKey, setGeminiApiKey] = useState(localStorage.getItem('GEMINI_API_KEY_LOCAL') || '');
  const [geminiModel, setGeminiModel] = useState(localStorage.getItem('GEMINI_MODEL') || 'gemini-2.5-flash');
  const [nvidiaApiKey, setNvidiaApiKey] = useState(localStorage.getItem('NVIDIA_NIM_API_KEY') || '');
  const [nvidiaModel, setNvidiaModel] = useState(localStorage.getItem('NVIDIA_NIM_MODEL') || 'meta/llama3-70b-instruct');
  const [openRouterApiKey, setOpenRouterApiKey] = useState(localStorage.getItem('OPEN_ROUTER_API_KEY') || '');
  const [openRouterModel, setOpenRouterModel] = useState(localStorage.getItem('OPEN_ROUTER_MODEL') || 'meta-llama/llama-3-8b-instruct:free');

  useEffect(() => {
    localStorage.setItem('GEMINI_API_KEY_LOCAL', geminiApiKey);
    localStorage.setItem('GEMINI_MODEL', geminiModel);
    localStorage.setItem('NVIDIA_NIM_API_KEY', nvidiaApiKey);
    localStorage.setItem('NVIDIA_NIM_MODEL', nvidiaModel);
    localStorage.setItem('OPEN_ROUTER_API_KEY', openRouterApiKey);
    localStorage.setItem('OPEN_ROUTER_MODEL', openRouterModel);
  }, [geminiApiKey, geminiModel, nvidiaApiKey, nvidiaModel, openRouterApiKey, openRouterModel]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    const newMsg = { role: 'user', content: userMsg, agent: 'User' };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    setIsTyping(true);
    setStreamingText('');

    const agentConfig = AGENT_CONFIGS[selectedAgent];

    try {
      // Fetch fresh market data for context
      const apiUrl = (window.location.protocol === 'https:' ? 'https://' : 'http://') + window.location.host.replace(':5001', ':5002');
      let marketContext = [];
      try {
        const marketRes = await fetch(`${apiUrl}/api/market-data`);
        const marketData = await marketRes.json();
        marketContext = marketData.quotes || [];
      } catch { /* non-fatal */ }

      // Call the real AI backend with agent routing
      const chatRes = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          agent: selectedAgent,
          system: agentConfig.system,
          provider: agentConfig.provider,
          model: agentConfig.model,
          role: agentConfig.role,
          marketContext,
          apiKey: agentConfig.provider === 'nvidia' ? nvidiaApiKey :
                  agentConfig.provider === 'openrouter' ? openRouterApiKey :
                  agentConfig.provider === 'gemini' ? geminiApiKey : '',
          modelOverride: agentConfig.provider === 'nvidia' ? nvidiaModel :
                         agentConfig.provider === 'openrouter' ? openRouterModel :
                         agentConfig.provider === 'gemini' ? geminiModel : '',
        })
      });

      const chatJson = await chatRes.json();

      if (!chatRes.ok || chatJson.error) {
        setMessages(prev => [...prev, {
          role: 'agent',
          content: `Error from ${selectedAgent}: ${chatJson.error || 'Agent offline or API error.'}`,
          agent: selectedAgent
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'agent',
          content: chatJson.reply,
          agent: selectedAgent
        }]);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, {
        role: 'agent',
        content: `Connection to ${selectedAgent} cognitive core failed. Check API keys in Settings.`,
        agent: selectedAgent
      }]);
    } finally {
      setIsTyping(false);
      setStreamingText('');
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between z-10 relative">
        <div className="flex items-center gap-3">
          <Bot className="w-5 h-5 text-blue-400" />
          <span className="font-medium">Syndicate Terminal</span>
          <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
            <Radio className="w-3 h-3" />
            7 Agents Live
          </span>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-sm rounded-lg px-3 py-1.5 outline-none focus:border-blue-500"
          >
            {Object.keys(AGENT_CONFIGS).map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className={`p-2 rounded-lg transition-colors border ${showConfig ? 'bg-slate-800 border-slate-600 text-white' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`}
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>

        {showConfig && (
          <div className="absolute top-16 right-4 w-80 bg-slate-800 border border-slate-700 shadow-2xl rounded-xl z-20 overflow-auto max-h-[80vh]">
            <div className="p-4 space-y-4">
              <h3 className="font-semibold text-sm border-b border-slate-700 pb-2 flex items-center gap-2">
                <Key className="w-4 h-4 text-slate-400" /> API Configurations
              </h3>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-medium block">NVIDIA NIM (Kimi, Minimax, GLM)</label>
                <input type="password" value={nvidiaApiKey} onChange={e => setNvidiaApiKey(e.target.value)} placeholder="API Key" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-emerald-500 text-white" />
                <input type="text" value={nvidiaModel} onChange={e => setNvidiaModel(e.target.value)} placeholder="Model Name" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-emerald-500 text-slate-400" />
              </div>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-medium block">OpenRouter (Genspark, Cypher-Q, LeviathanX)</label>
                <input type="password" value={openRouterApiKey} onChange={e => setOpenRouterApiKey(e.target.value)} placeholder="API Key" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-purple-500 text-white" />
                <input type="text" value={openRouterModel} onChange={e => setOpenRouterModel(e.target.value)} placeholder="Model Name" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-purple-500 text-slate-400" />
              </div>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-medium block">Google Gemini (Fallback)</label>
                <input type="password" value={geminiApiKey} onChange={e => setGeminiApiKey(e.target.value)} placeholder="API Key" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-blue-500 text-white" />
                <input type="text" value={geminiModel} onChange={e => setGeminiModel(e.target.value)} placeholder="Model Name" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-blue-500 text-slate-400" />
              </div>

              <button type="button" onClick={() => setShowConfig(false)} className="w-full bg-slate-700 hover:bg-slate-600 text-white rounded-lg py-1.5 text-xs font-medium transition-colors">
                Close & Save
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-blue-600' : 'bg-slate-800'}`}>
              {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-blue-400" />}
            </div>
            <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} max-w-[80%]`}>
              <span className="text-xs text-slate-500 mb-1">{msg.agent}</span>
              <div className={`p-3 rounded-xl ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-200'}`}>
                <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre>
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-slate-800">
              <Bot className="w-5 h-5 text-blue-400" />
            </div>
            <div className="flex flex-col items-start max-w-[80%]">
              <span className="text-xs text-slate-500 mb-1">{selectedAgent}</span>
              <div className="p-3 rounded-xl bg-slate-800 text-slate-200 flex items-center gap-1">
                {streamingText ? (
                  <pre className="whitespace-pre-wrap font-sans text-sm">{streamingText}</pre>
                ) : (
                  <>
                    <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                    <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-slate-900">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Message ${selectedAgent}...`}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-4 pr-12 py-3 outline-none focus:border-blue-500 transition-colors"
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={isTyping}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-slate-400 hover:text-blue-400 transition-colors disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
