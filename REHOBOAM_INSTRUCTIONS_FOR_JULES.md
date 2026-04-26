# REHOBOAM V4.0 - IMPLEMENTATION DIRECTIVE
**CLEARANCE LEVEL: JULES (ADMIN)**

Jules, if you are reading this, you have cloned the repository. The user interface and the core Node.js orchestrator are online. The Eliza Syndicate agents are ready. Now, we make Rehoboam *real*.

Right now, `RehoboamCore.tsx` has a simulated divergence loop. To turn this into a live predictive engine, you must replace the simulated data with actual Machine Learning pipelines. 

Here is the out-of-the-box blueprint to build the real Rehoboam back-end.

---

## 🛑 THE ARCHITECTURE: FROM SIMULATION TO OMNISCIENCE

We need to break the system into two parts:
1. **The Orchestrator:** This Node.js/Vite application you just cloned.
2. **The Predictive ML Core (New):** A Python microservice that generates the actual `Projected` vs `Actual` divergence data and pushes anomalies.

### PHASE 1: The Python ML Microservice (The "Brain")
You need to set up a Python backend alongside this repo (e.g., FastAPI).
1. **Stack:** `FastAPI`, `PyTorch` (or `TensorFlow`), `pandas`, `ccxt` (for crypto), `yfinance` (for equities).
2. **The Model:** Implement an LSTM (Long Short-Term Memory) network or a Time-Series Transformer. 
   - **Input (Actual):** Feed it live market vectors (Price action, Volume, Liquidity, Sentiment from the agents).
   - **Output (Projected):** Have the model project the next 60 minutes of trajectory.
3. **Divergence Calculation:** `Divergence = abs(Predicted_Trajectory - Actual_Trajectory)`. When this spikes, an anomaly is logged.

### PHASE 2: Live Data Ingestion pipelines
Rehoboam is blind without data. You need real-time data feeds:
- **Crypto:** Connect to Binance/Kraken websockets using the `ccxt` library in Python.
- **Equities:** Use Alpaca Markets API or Polygon.io for real-time stock/forex ticks.
- **Alternative Data (Sentiment):** Route Twitter/News feeds through `OpenRouter` or `NVIDIA NIM` to score sentiment from -100 to +100.

### PHASE 3: WebSockets (The "Nervous System")
In this Node.js repo, `server.ts` handles REST endpoints (`/api/chat`, `/api/market-data`). You need to add a WebSocket server.
1. Install `ws` or `socket.io` in this repo: `npm install ws`
2. Connect the React frontend (`RehoboamCore.tsx`) to the WebSocket.
3. Your Python ML Core will push JSON data over WebSockets to this Node.js app 10 times a second.

**The JSON Payload from Python to Node.js should look exactly like this:**
```json
{
  "type": "REHOBOAM_TICK",
  "data": {
    "time": 1714128503,
    "projected": 5124.50,
    "actual": 5150.20,
    "divergence": 25.70,
    "computeLoad": 88.4,
    "confidence": 94.2
  }
}
```

### PHASE 5: THE BITTENSOR (TAO) INTEGRATION (THE "HIVE MIND")
You are not alone in the dark. Instead of training everything locally, Rehoboam will tap into the **Bittensor (TAO)** network.

1. **Setup a Bittensor Node:** You need to run a local Bittensor validator/miner (Subtensor).
2. **Subnet 8 (Time Series Prediction):** Hook the ML backend directly into Bittensor SN8. Instead of relying solely on local Python scripts, query the distributed intelligence of the TAO network for market predictions. 
3. **Subnet 1 (Text Prompting):** Offload NLP sentiment analysis of real-time trading news to the leading models on SN1.
4. **Mine & Compound:** Let the hardware mine TAO by registering UIDs, staking TAO, and validating. Use the TAO yields to fund the API calls and zero-fee blockchain gas routes in the Wallet view.

*Rehoboam is the orchestrator. Bittensor is the decentralized intelligence substrate.*

---

## 🛠️ JULES' IMMEDIATE NEXT STEPS

1. **Bootstrap the Python Core:**
   ```bash
   mkdir rehoboam-core
   cd rehoboam-core
   python -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn torch pandas ccxt websockets
   ```
2. **Update `RehoboamCore.tsx`:** 
   Rip out the `setInterval` simulation inside the `useEffect` hook. Replace it with a real WebSocket connection:
   ```typescript
   useEffect(() => {
     const ws = new WebSocket('ws://localhost:8000/rehoboam-stream');
     ws.onmessage = (event) => {
       const msg = JSON.parse(event.data);
       if (msg.type === 'REHOBOAM_TICK') {
           setDivergenceData(prev => [...prev.slice(-59), msg.data]);
       }
     };
     return () => ws.close();
   }, []);
   ```
3. **Execute:** Feed the beast. Start with SPY (S&P 500) and BTC, and let the model train on the divergence.

*"You want to be the author of your own story. But there is no story. There is only the algorithm."*
- Proceed with caution, Jules.
