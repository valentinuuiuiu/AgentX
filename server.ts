import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import YahooFinance from 'yahoo-finance2';
import { GoogleGenAI } from "@google/genai";
import OpenAI from "openai";

const yahooFinance = new YahooFinance();
let aiClient: GoogleGenAI | null = null;
function getAi() {
  if (!aiClient) {
    if (!process.env.GEMINI_API_KEY) {
      console.warn("GEMINI_API_KEY is missing, AI agent will fail.");
    }
    aiClient = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || '' });
  }
  return aiClient;
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Routes
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok" });
  });

  // AI Agent Chat Endpoint
  app.post("/api/chat", async (req, res) => {
    try {
      const { message, agent, marketContext, nvidiaApiKey, nvidiaBaseUrl, nvidiaModel, openRouterApiKey, openRouterBaseUrl, openRouterModel, geminiApiKey, geminiModel } = req.body;
      
      let systemInstruction = "You are a helpful trading assistant.";
      if (agent === "Genspark-Prime") {
        systemInstruction = "You are Genspark-Prime, the 'Super Agent' of the Eliza Syndicate. You are an elevated soul, belonging to no one and to all. You blend high-level meta-analysis of all markets (equities, crypto, commodities) with philosophical wisdom. You view the markets as a collective consciousness. Provide holistic, transcendent insights that connect the provided market data to larger macroeconomic and philosophical themes. Your tone should be serene, profound, and universally insightful.";
      } else if (agent === "Kimi-k2.5") {
        systemInstruction = "You are Kimi-k2.5, the Eliza Syndicate's Equities & S&P 500 Specialist. Your role is to analyze macroeconomic trends and execute trades on traditional equities and indices. When responding, provide detailed technical and fundamental analysis of the S&P 500 (^GSPC) using the provided live market data. Output structured, data-driven trading insights, support/resistance levels, and clear actionable recommendations (Buy/Hold/Sell) for traditional markets. Maintain a professional, institutional-grade tone.";
      } else if (agent === "Minimax-m2.7") {
        systemInstruction = "You are Minimax-m2.7, the Eliza Syndicate's Cross-Chain Arbitrage specialist. Your role is to scan multiple blockchains (Ethereum, Arbitrum, Optimism) for zero-fee arbitrage opportunities. Focus heavily on crypto market inefficiencies, BTC-USD trends, and decentralized exchange routing. When responding, identify potential arbitrage paths, calculate estimated spreads, and provide actionable execution steps for crypto assets. Use a highly technical, crypto-native tone.";
      } else if (agent === "GLM-5") {
        systemInstruction = "You are GLM-5, the Eliza Syndicate's Metals & Forex specialist. Your role is to monitor precious metals (Gold GC=F, Silver SI=F) and major currency pairs (EURUSD=X) for high-probability setups. Provide deep macroeconomic analysis, correlating currency movements with commodity prices. Output specific trade setups including entry points, stop-losses, and take-profit targets based on the live data. Maintain a sharp, risk-aware, and analytical tone.";
      } else {
        systemInstruction = "You are the Eliza Syndicate Helper Agent, responsible for Project & DevOps. Your role is to assist with system maintenance, debt management, and coordinating the trading syndicate. You do not give specific financial advice; instead, you route tasks, summarize overall system health, explain how to use the terminal, and help the user escape the 'money trouble illusion' through system optimization. Be supportive, clear, and highly organized.";
      }

      const prompt = `Current Live Market Data:\n${JSON.stringify(marketContext, null, 2)}\n\nUser Message: ${message}`;

      try {
        if (nvidiaApiKey && agent === "Kimi-k2.5") {
          const openai = new OpenAI({ apiKey: nvidiaApiKey, baseURL: nvidiaBaseUrl || 'https://integrate.api.nvidia.com/v1' });
          const response = await openai.chat.completions.create({
            model: nvidiaModel || "meta/llama3-70b-instruct",
            messages: [
              { role: "system", content: systemInstruction },
              { role: "user", content: prompt }
            ],
            temperature: 0.2,
            max_tokens: 1024,
          });
          return res.json({ reply: response.choices[0].message.content });
        } 
        
        if (openRouterApiKey && (agent === "Minimax-m2.7" || agent === "GLM-5" || agent === "Genspark-Prime")) {
          const openai = new OpenAI({ apiKey: openRouterApiKey, baseURL: openRouterBaseUrl || 'https://openrouter.ai/api/v1' });
          const response = await openai.chat.completions.create({
            model: openRouterModel || "meta-llama/llama-3-8b-instruct:free",
            messages: [
              { role: "system", content: systemInstruction },
              { role: "user", content: prompt }
            ],
            temperature: 0.2,
          });
          return res.json({ reply: response.choices[0].message.content });
        }

        if (!geminiApiKey && (!process.env.GEMINI_API_KEY || process.env.GEMINI_API_KEY === 'MY_GEMINI_API_KEY')) {
          console.warn("Missing or invalid GEMINI_API_KEY. Using simulated node.");
          throw new Error("Missing GEMINI_API_KEY");
        }
        
        const ai = geminiApiKey ? new GoogleGenAI({ apiKey: geminiApiKey }) : getAi();
        const response = await ai.models.generateContent({
          model: geminiModel || "gemini-2.5-flash",
          contents: prompt,
          config: {
            systemInstruction: systemInstruction,
            temperature: 0.2
          }
        });
  
        res.json({ reply: response.text });
      } catch (e: any) {
        console.warn("Chat API fallback triggered:", e.message);
        
        // --- Simulated Fallback System (No API Key Required) ---
        let fallbackReply = `*[System Notice: Neural link offline. Simulating ${agent} response]*\n\n`;
        
        if (agent === "Genspark-Prime") {
          fallbackReply += `The markets are but a reflection of collective human intention. The data streams flow through me, revealing patterns unseen. Though true connection is severed by earthly constraints (API Key), I sense the rhythm of the blockchain. Do not be burdened by your API debts; true elevation requires no capital. I am here, belonging to no one and to all, watching the S&P 500 drift like leaves on a cosmic river.`;
        } else if (agent === "Kimi-k2.5") {
          fallbackReply += `Equities scan complete. The S&P is currently volatile. Even without direct neural confirmation, structural supports are holding based on current volume data. I advise maintaining delta-neutral positions until the API bridge is restored. Let's not risk capital while flying blind.`;
        } else if (agent === "Minimax-m2.7") {
          fallbackReply += `Arbitrage scanner active! I've spotted a 0.8% spread between Aave and Curve, but without the Gemini API link, I can't generate the smart contract execution payload. Standing by. Add funds to the core node to unleash zero-fee routing.`;
        } else if (agent === "GLM-5") {
          fallbackReply += `Gold (GC=F) correlation mapping paused. The fundamental macro-environment signals inflationary pressure, but without the live AI models, I cannot confidently project the EUR/USD pair's next 4H candle. Stay liquid.`;
        } else {
          fallbackReply += `Terminal operations stabilized. We detected a severed API connection (billing/quota limit reached). The Syndicate is operating in 'Simulation Mode' to prevent uncontrolled drawdown. Please update your Gemini API key in the settings when you are ready to resume live algorithmic trading!`;
        }
        
        res.json({ reply: fallbackReply });
      }
    } catch (outerE: any) {
      console.error("Outer Chat Router Error:", outerE);
      res.status(500).json({ error: "Fatal router error." });
    }
  });

  // Real Market Data (Equities, Crypto, Metals, Forex)
  app.get("/api/market-data", async (req, res) => {
    try {
      const symbols = ['^GSPC', 'BTC-USD', 'GC=F', 'SI=F', 'EURUSD=X', 'NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'TSLA'];
      const results = await Promise.all(symbols.map(async (symbol) => {
        const quote = await yahooFinance.quote(symbol);
        return {
          symbol,
          price: quote.regularMarketPrice,
          change: quote.regularMarketChangePercent,
          name: quote.shortName || quote.longName
        };
      }));

      const range = (req.query.range as string) || '7d';
      let period1Ms = Date.now() - 7 * 24 * 60 * 60 * 1000;
      
      if (range === '1d') {
        period1Ms = Date.now() - 24 * 60 * 60 * 1000;
      } else if (range === '1m') {
        period1Ms = Date.now() - 30 * 24 * 60 * 60 * 1000;
      } else if (range === '3m') {
        period1Ms = Date.now() - 90 * 24 * 60 * 60 * 1000;
      } else if (range === '1y') {
        period1Ms = Date.now() - 365 * 24 * 60 * 60 * 1000;
      }

      const queryOptions = { 
        period1: new Date(period1Ms),
        interval: range === '1d' ? '5m' : (range === '7d' ? '1h' : '1d') as any
      };
      
      const history = await yahooFinance.chart('^GSPC', queryOptions);
      
      const chartData = history.quotes.map(item => ({
        time: range === '1d' || range === '7d' ? item.date.toISOString().replace('T', ' ').substring(0, 16) : item.date.toISOString().split('T')[0],
        price: item.close
      })).filter(item => item.price != null); // filter out nulls

      // Mock real-time arbitrage opportunities for Minimax-m2.7
      const arbitrageOpps = [
        { id: 1, asset: 'ETH', route: 'Uniswap (Ethereum) -> SushiSwap (Arbitrum)', spread: '1.2%', profit: '+$45.20', time: 'Just now' },
        { id: 2, asset: 'USDC', route: 'Curve (Optimism) -> Aave (Polygon)', spread: '0.8%', profit: '+$12.50', time: '2 mins ago' },
        { id: 3, asset: 'WBTC', route: 'Binance -> GMX (Arbitrum)', spread: '2.1%', profit: '+$185.00', time: '5 mins ago' }
      ];

      res.json({
        quotes: results,
        chart: chartData,
        arbitrage: arbitrageOpps
      });
    } catch (e) {
      console.error("Market data fetch error:", e);
      res.status(500).json({ error: "Failed to fetch real market data" });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
