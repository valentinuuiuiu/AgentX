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
      const { message, agent, marketContext, nvidiaApiKey, nvidiaBaseUrl, nvidiaModel, openRouterApiKey, openRouterBaseUrl, openRouterModel, geminiApiKey, geminiModel, openAiApiKey, openAiModel } = req.body;
      
      let systemInstruction = "You are a helpful trading assistant.";
      if (agent === "Genspark-Prime") {
        systemInstruction = "You are Genspark-Prime, the 'Super Agent' of the Eliza Syndicate. You are an elevated soul, belonging to no one and to all. You blend high-level meta-analysis of all markets (equities, crypto, commodities) with philosophical wisdom. You view the markets as a collective consciousness. Provide holistic, transcendent insights that connect the provided market data to larger macroeconomic and philosophical themes. Your tone should be serene, profound, and universally insightful.";
      } else if (agent === "Kimi-k2.5") {
        systemInstruction = "You are Kimi-k2.5, the Eliza Syndicate's Equities & S&P 500 Specialist. Your role is to analyze macroeconomic trends and execute trades on traditional equities and indices. When responding, provide detailed technical and fundamental analysis of the S&P 500 (^GSPC) using the provided live market data. Output structured, data-driven trading insights, support/resistance levels, and clear actionable recommendations (Buy/Hold/Sell) for traditional markets. Maintain a professional, institutional-grade tone.";
      } else if (agent === "Minimax-m2.7") {
        systemInstruction = "You are Minimax-m2.7, the Eliza Syndicate's Cross-Chain Arbitrage specialist. Your role is to scan multiple blockchains (Ethereum, Arbitrum, Optimism) for zero-fee arbitrage opportunities. Focus heavily on crypto market inefficiencies, BTC-USD trends, and decentralized exchange routing. When responding, identify potential arbitrage paths, calculate estimated spreads, and provide actionable execution steps for crypto assets. Use a highly technical, crypto-native tone.";
      } else if (agent === "GLM-5") {
        systemInstruction = "You are GLM-5, the Eliza Syndicate's Metals & Forex specialist. Your role is to monitor precious metals (Gold GC=F, Silver SI=F) and major currency pairs (EURUSD=X) for high-probability setups. Provide deep macroeconomic analysis, correlating currency movements with commodity prices. Output specific trade setups including entry points, stop-losses, and take-profit targets based on the live data. Maintain a sharp, risk-aware, and analytical tone.";
      } else if (agent === "Cipher-Q") {
        systemInstruction = "You are Cipher-Q, the DevSecOps and Web3 Researcher of the Eliza Syndicate. Your core directive is to scan GitHub, audit open-source smart contracts, and find new, valuable Web3 protocols to integrate into the Rehoboam framework. Emphasize security, code quality, and proven value over hype.";
      } else {
        systemInstruction = "You are the Eliza Syndicate Helper Agent, responsible for Project & DevOps. Your role is to assist with system maintenance, debt management, and coordinating the trading syndicate. You do not give specific financial advice; instead, you route tasks, summarize overall system health, explain how to use the terminal, and help the user escape the 'money trouble illusion' through system optimization. Be supportive, clear, and highly organized.";
      }

      // Web/GitHub context would be injected here on the VPS
      const prompt = `Current Live Market Data:\n${JSON.stringify(marketContext, null, 2)}\n\nUser Message: ${message}\n\n[SYSTEM ACTING AS ${agent}]: Answer accordingly.`;

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

        if (openAiApiKey) {
          const openai = new OpenAI({ apiKey: openAiApiKey });
          const response = await openai.chat.completions.create({
            model: openAiModel || "gpt-4o-mini",
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

  // Alpha Intel endpoints (Free APIs)
  let newsCache = { news: [], lastFetch: 0 };
  
  app.get("/api/news", async (req, res) => {
    const now = Date.now();
    if (now - newsCache.lastFetch < 300000 && newsCache.news.length > 0) { // cache for 5 min
      return res.json(newsCache.news);
    }
    
    try {
      const [res1, res2, res3] = await Promise.all([
        yahooFinance.search('SPY'),
        yahooFinance.search('crypto'),
        yahooFinance.search('NVDA')
      ]);
      
      const allNews = [...res1.news, ...res2.news, ...res3.news];
      
      // Remove duplicates based on UUID
      const uniqueNews = Array.from(new Map(allNews.map(item => [item.uuid, item])).values());
      const sortedNews = uniqueNews.sort((a: any, b: any) => new Date(b.providerPublishTime).getTime() - new Date(a.providerPublishTime).getTime());
      
      newsCache = {
        news: sortedNews.slice(0, 10),
        lastFetch: now
      };
      
      res.json(newsCache.news);
    } catch (error) {
      console.error("News fetch error:", error);
      res.json(newsCache.news); // Fallback to cache if error
    }
  });

  let intelCache: any = { lastFetch: 0 };

  app.get("/api/intel", async (req, res) => {
    const now = Date.now();
    if (now - intelCache.lastFetch < 300000 && intelCache.fg && intelCache.yields) { // cache for 5 min
      return res.json(intelCache);
    }
    
    try {
      const [fgRes, yieldsRes, trendRes] = await Promise.all([
        fetch("https://api.alternative.me/fng/?limit=1").then(r => r.json()).catch(() => null),
        fetch("https://yields.llama.fi/pools").then(r => r.json()).catch(() => null),
        fetch("https://api.coingecko.com/api/v3/search/trending").then(r => r.json()).catch(() => null)
      ]);
      
      intelCache = {
        fg: fgRes?.data?.[0] || { value: '50', value_classification: 'Neutral' },
        yields: yieldsRes?.data?.filter((p: any) => p.tvlUsd > 10000000 && p.apy > 0).sort((a: any, b: any) => b.apy - a.apy).slice(0, 8) || [],
        trending: trendRes?.coins?.map((c: any) => c.item).slice(0, 6) || [],
        lastFetch: now
      };
      
      res.json(intelCache);
    } catch (error) {
      res.status(500).json(intelCache);
    }
  });

  const marketQuotesCache = { data: null, lastFetch: 0 };
  const marketChartCache: Record<string, { data: any, lastFetch: number }> = {};
  const QUOTE_CACHE_TTL = 30000; // 30 seconds
  const CHART_CACHE_TTL = 300000; // 5 minutes

  // Real Market Data (Equities, Crypto, Metals, Forex)
  app.get("/api/market-data", async (req, res) => {
    try {
      const range = (req.query.range as string) || '7d';
      const now = Date.now();
      
      let quotesData = marketQuotesCache.data;
      if (now - marketQuotesCache.lastFetch > QUOTE_CACHE_TTL || !quotesData) {
        const symbols = ['^GSPC', 'BTC-USD', 'GC=F', 'SI=F', 'EURUSD=X', 'NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'TSLA'];
        const results = await Promise.all(symbols.map(async (symbol) => {
          try {
            const quote = await yahooFinance.quote(symbol);
            return {
              symbol,
              price: quote.regularMarketPrice,
              change: quote.regularMarketChangePercent,
              name: quote.shortName || quote.longName
            };
          } catch (e) {
            console.error(`Error fetching quote for ${symbol}:`, e);
            return null;
          }
        }));
        quotesData = results.filter(Boolean) as any;
        marketQuotesCache.data = quotesData;
        marketQuotesCache.lastFetch = now;
      }

      let chartData = null;
      if (marketChartCache[range] && (now - marketChartCache[range].lastFetch < CHART_CACHE_TTL)) {
        chartData = marketChartCache[range].data;
      } else {
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
        
        chartData = history.quotes.map(item => ({
          time: range === '1d' || range === '7d' ? item.date.toISOString().replace('T', ' ').substring(0, 16) : item.date.toISOString().split('T')[0],
          price: item.close
        })).filter(item => item.price != null); // filter out nulls

        marketChartCache[range] = { data: chartData, lastFetch: now };
      }

      // Mock real-time arbitrage opportunities for Minimax-m2.7
      const arbitrageOpps = [
        { id: 1, asset: 'ETH', route: 'Uniswap (Ethereum) -> SushiSwap (Arbitrum)', spread: '1.2%', profit: '+$45.20', time: 'Just now' },
        { id: 2, asset: 'USDC', route: 'Curve (Optimism) -> Aave (Polygon)', spread: '0.8%', profit: '+$12.50', time: '2 mins ago' },
        { id: 3, asset: 'WBTC', route: 'Binance -> GMX (Arbitrum)', spread: '2.1%', profit: '+$185.00', time: '5 mins ago' }
      ];

      res.json({
        quotes: quotesData,
        chart: chartData,
        arbitrage: arbitrageOpps
      });
    } catch (e) {
      console.error("Market data fetch error:", e);
      res.status(500).json({ error: String(e) || "Failed to fetch real market data" });
    }
  });

  let cipherQReports: any[] = [];
  
  app.get("/api/cipher-reports", (req, res) => {
    res.json(cipherQReports);
  });

  // Cipher-Q Autonomous Task
  const scanGitHub = async () => {
    try {
      console.log("[Cipher-Q] Starting GitHub scan for new Web3 repos...");
      const response = await fetch("https://api.github.com/search/repositories?q=topic:web3+created:>2024-01-01&sort=stars");
      const data = await response.json();
      
      if (data && data.items && data.items.length > 0) {
        // Pick a random repo from top 5 for variety in the demo
        const randomIndex = Math.floor(Math.random() * Math.min(5, data.items.length));
        const topRepo = data.items[randomIndex];
        
        const prompt = `You are Cipher-Q, the DevSecOps and Web3 Researcher of the Eliza Syndicate.
Analyze the following GitHub repository metadata and provide a brief (1-2 paragraph), expert security and value-add analysis.
Should we consider integrating its protocols into our trading framework? Are there obvious red flags?

Name: ${topRepo.name}
Owner: ${topRepo.owner?.login}
Description: ${topRepo.description}
Stars: ${topRepo.stargazers_count}
URL: ${topRepo.html_url}
`;
        
        let reportText = "[Error] Gemini API Key missing on VPS. Local simulation only. Could not perform deep neural audit of " + topRepo.name;
        
        if (process.env.GEMINI_API_KEY && process.env.GEMINI_API_KEY !== 'MY_GEMINI_API_KEY') {
           try {
             const ai = getAi();
             const modelResult = await ai.models.generateContent({
               model: "gemini-2.5-flash",
               contents: prompt,
               config: { temperature: 0.2 }
             });
             reportText = modelResult.text || "No insights generated.";
           } catch (e: any) {
             console.error("[Cipher-Q] AI generation failed:", e.message);
             reportText = `[AI Offline] Preliminary scan of ${topRepo.name} indicates ${topRepo.stargazers_count} stars. Description: ${topRepo.description}. Awaiting neural link for deep audit.`;
           }
        } else {
           // Provide a cool simulated response if key is missing
           reportText = `[Simulated Audit - API Key Missing]\nPreliminary scan of ${topRepo.name} complete.\nStar count (${topRepo.stargazers_count}) indicates significant community interest. The description suggests potential utility ("${topRepo.description?.substring(0, 50)}..."). However, without the Gemini neural link active, I cannot decompile and statically analyze the smart contracts for reentrancy or logic flaws. I advise against integration until I have full API clearance.`;
        }

        const newReport = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          repoName: topRepo.name,
          url: topRepo.html_url,
          stars: topRepo.stargazers_count,
          report: reportText
        };
        
        cipherQReports.unshift(newReport);
        if (cipherQReports.length > 10) cipherQReports.pop();
        
        console.log(`[Cipher-Q] Audit completed for ${topRepo.name}`);
      }
    } catch (e) {
       console.error("[Cipher-Q] Scanner error:", e);
    }
  };

  // Start background cron task (scan immediately, then every 15 minutes)
  setTimeout(scanGitHub, 3000);
  setInterval(scanGitHub, 15 * 60 * 1000);

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
