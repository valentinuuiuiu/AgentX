import React, { useState, useEffect } from 'react';
import { Send, Bot, User, Zap, Settings, Key } from 'lucide-react';

export function Chat() {
  const [messages, setMessages] = useState([
    { role: 'agent', content: 'Eliza Syndicate Terminal initialized. I am your Helper Agent. I have connected to the MCP Server for S&P 500 data, Chainlink OCR for live feeds, and CoinGecko for crypto arbitrage. How can we escape the money trouble illusion today?', agent: 'Helper Agent' }
  ]);
  const [input, setInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('Helper Agent');
  const [isTyping, setIsTyping] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

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

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const newMsg = { role: 'user', content: input, agent: 'User' };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    setIsTyping(true);
    
    try {
      // Fetch fresh market data for context
      const marketRes = await fetch('/api/market-data');
      const marketData = await marketRes.json();

      // Call real AI agent
      const chatRes = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: newMsg.content, 
          agent: selectedAgent,
          marketContext: marketData.quotes || [],
          geminiApiKey,
          geminiModel,
          nvidiaApiKey,
          nvidiaModel,
          openRouterApiKey,
          openRouterModel
        })
      });
      
      const chatJson = await chatRes.json();

      if (!chatRes.ok || chatJson.error) {
        setMessages(prev => [...prev, { 
          role: 'agent', 
          content: `Error: ${chatJson.error || "Agent offline or error processing request."}`,
          agent: selectedAgent
        }]);
      } else {
        setMessages(prev => [...prev, { 
          role: 'agent', 
          content: chatJson.reply,
          agent: selectedAgent
        }]);
      }
    } catch (e) {
      console.error("Chat error:", e);
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: "Connection to agent cognitive core failed. Please ensure the server is running and API keys are set.",
        agent: selectedAgent
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between z-10 relative">
        <div className="flex items-center gap-3">
          <Bot className="w-5 h-5 text-blue-400" />
          <span className="font-medium">Terminal Interface</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full hidden sm:flex">
            <Zap className="w-3 h-3" />
            MCP Connected
          </div>
          <select 
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-sm rounded-lg px-3 py-1.5 outline-none focus:border-blue-500"
          >
            <option value="Genspark-Prime">Genspark-Prime (Super Agent)</option>
            <option value="Helper Agent">Helper Agent (Dev/Ops)</option>
            <option value="Kimi-k2.5">Kimi-k2.5 (Equities)</option>
            <option value="Minimax-m2.7">Minimax-m2.7 (Arbitrage)</option>
            <option value="GLM-5">GLM-5 (Metals/Forex)</option>
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
                <label className="text-xs text-slate-400 font-medium block">NVIDIA NIM (powers Kimi-k2.5)</label>
                <input type="password" value={nvidiaApiKey} onChange={e => setNvidiaApiKey(e.target.value)} placeholder="API Key" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-emerald-500 text-white" />
                <input type="text" value={nvidiaModel} onChange={e => setNvidiaModel(e.target.value)} placeholder="Model Name" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-emerald-500 text-slate-400" />
              </div>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-medium block">OpenRouter (powers Minimax & GLM)</label>
                <input type="password" value={openRouterApiKey} onChange={e => setOpenRouterApiKey(e.target.value)} placeholder="API Key" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-purple-500 text-white" />
                <input type="text" value={openRouterModel} onChange={e => setOpenRouterModel(e.target.value)} placeholder="Model Name" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-purple-500 text-slate-400" />
              </div>

              <div className="space-y-2">
                <label className="text-xs text-slate-400 font-medium block">Google Gemini (Fallback/Primary)</label>
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
                {msg.content}
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
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
              </div>
            </div>
          </div>
        )}
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

