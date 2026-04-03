import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import YahooFinance from 'yahoo-finance2';
import { GoogleGenAI } from "@google/genai";

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
      const { message, agent, marketContext } = req.body;
      const ai = getAi();

      let systemInstruction = "You are a helpful trading assistant.";
      if (agent === "Kimi-k2.5") {
        systemInstruction = "You are Kimi-k2.5, the Eliza Syndicate's Equities & S&P 500 Specialist. Your role is to analyze macroeconomic trends and execute trades on traditional equities and indices. When responding, provide detailed technical and fundamental analysis of the S&P 500 (^GSPC) using the provided live market data. Output structured, data-driven trading insights, support/resistance levels, and clear actionable recommendations (Buy/Hold/Sell) for traditional markets. Maintain a professional, institutional-grade tone.";
      } else if (agent === "Minimax-m2.7") {
        systemInstruction = "You are Minimax-m2.7, the Eliza Syndicate's Cross-Chain Arbitrage specialist. Your role is to scan multiple blockchains (Ethereum, Arbitrum, Optimism) for zero-fee arbitrage opportunities. Focus heavily on crypto market inefficiencies, BTC-USD trends, and decentralized exchange routing. When responding, identify potential arbitrage paths, calculate estimated spreads, and provide actionable execution steps for crypto assets. Use a highly technical, crypto-native tone.";
      } else if (agent === "GLM-5") {
        systemInstruction = "You are GLM-5, the Eliza Syndicate's Metals & Forex specialist. Your role is to monitor precious metals (Gold GC=F, Silver SI=F) and major currency pairs (EURUSD=X) for high-probability setups. Provide deep macroeconomic analysis, correlating currency movements with commodity prices. Output specific trade setups including entry points, stop-losses, and take-profit targets based on the live data. Maintain a sharp, risk-aware, and analytical tone.";
      } else {
        systemInstruction = "You are the Eliza Syndicate Helper Agent, responsible for Project & DevOps. Your role is to assist with system maintenance, debt management, and coordinating the trading syndicate. You do not give specific financial advice; instead, you route tasks, summarize overall system health, explain how to use the terminal, and help the user escape the 'money trouble illusion' through system optimization. Be supportive, clear, and highly organized.";
      }

      const prompt = `Current Live Market Data:\n${JSON.stringify(marketContext, null, 2)}\n\nUser Message: ${message}`;

      const response = await ai.models.generateContent({
        model: "gemini-3.1-pro-preview",
        contents: prompt,
        config: {
          systemInstruction: systemInstruction,
          temperature: 0.2
        }
      });

      res.json({ reply: response.text });
    } catch (e) {
      console.error("Chat API error:", e);
      res.status(500).json({ error: "Failed to generate response" });
    }
  });

  // Real Market Data (Equities, Crypto, Metals, Forex)
  app.get("/api/market-data", async (req, res) => {
    try {
      const symbols = ['^GSPC', 'BTC-USD', 'GC=F', 'SI=F', 'EURUSD=X'];
      const results = await Promise.all(symbols.map(async (symbol) => {
        const quote = await yahooFinance.quote(symbol);
        return {
          symbol,
          price: quote.regularMarketPrice,
          change: quote.regularMarketChangePercent,
          name: quote.shortName || quote.longName
        };
      }));

      // Get historical data for S&P 500 chart
      const queryOptions = { period1: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), interval: '1d' as const };
      const history = await yahooFinance.historical('^GSPC', queryOptions);
      
      const chartData = history.map(item => ({
        time: item.date.toISOString().split('T')[0],
        price: item.close
      }));

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
