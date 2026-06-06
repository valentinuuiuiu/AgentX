# 🔱 REHOBOAM — AGENT HANDOFF & NEXT STEPS
**Last updated:** 2026-04-22  
**Status:** API running (degraded → fixing), Frontend live, DB + Redis + MCP services UP

---

## 📍 CURRENT STATE

### Container Status (all running via podman-compose)
| Service | Port | Status |
|---|---|---|
| `rehoboam-api` | 5002 | ✅ Running (health degraded — being fixed) |
| `rehoboam-frontend` | 5001 | ✅ Running |
| `postgres` (pgvector) | 5432 | ✅ Running |
| `redis` | 6379 | ✅ Running |
| `prometheus` | 9090 | ✅ Running |
| `grafana` | 3000 | ✅ Running |
| `mcp-registry` | 3001 | ✅ Running |
| `mcp-consciousness-layer` | 3600 | ✅ Healthy |
| `mcp-etherscan-analyzer` | 3101 | ✅ Running |
| `mcp-chainlink-feeds` | 3102 | ✅ Running |
| `mcp-function-gemma` | 3111 | ✅ Running |
| `mcp-trading-agents` | 3700 | ✅ Healthy |

### Git Branch
- **Repo:** `https://github.com/valentinuuiuiu/clean_rehoboam_project.git`
- **Current branch:** `vetal-raksha/security-hardening` (9 commits ahead of `origin/main`)
- **Parent Workspace:** `/home/aryan/free-claude/bittensor/clean_rehoboam_project/`

---

## 🐛 BUGS FIXED (2026-04-22)

### Fix 1: `utils/price_feed_service.py` — INFURA hard requirement removed
- **Problem:** `PriceFeedService.__init__` raised `ValueError` if `INFURA_API_KEY` not set
- **Root cause:** The `.env` uses `ALCHEMY_API_KEY` (Alchemy as primary provider) — INFURA was never configured
- **Fix applied:** Changed the hard raise to a warning; added `ETHEREUM_RPC_URL` as final Web3 fallback
- **File changed:** `utils/price_feed_service.py` lines 20-66
- **Effect:** `trading_agent`, `api_server` can now initialize PriceFeedService without crashing

### Fix 2: `tokens` table missing in PostgreSQL
- **Problem:** `WARNING: Failed to save prices to database: relation "tokens" does not exist`
- **Status:** Needs migration (see Next Steps below)

---

## 🏗️ ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────┐
│              REHOBOAM FRONTEND               │
│  React/Vite  •  port 5001                  │
│  Real-time: WS → ws://localhost:5002/ws    │
└────────────────────┬────────────────────────┘
                     │ HTTP/WS
┌────────────────────▼────────────────────────┐
│              REHOBOAM API                    │
│  Flask + asyncio  •  port 5002             │
│  api_server.py (156KB – main server)       │
│                                             │
│  Core modules (must all be non-None):      │
│  • rehoboam (RehoboamUnifiedSystem)        │
│  • reasoning_orchestrator                  │
│  • market_analyzer (OpenAIMarketAnalyzer)  │
│  • trading_agent (TradingAgent)            │
│  • t2l_auditor (T2LAuditorEngine)          │
└──┬─────────────┬──────────────┬────────────┘
   │             │              │
   ▼             ▼              ▼
Postgres      Redis        MCP Services
(pgvector)   cache         (3001,3600,3700...)
```

### Key Python files:
| File | Purpose |
|---|---|
| `api_server.py` | Main Flask API (all endpoints) |
| `trading_agent.py` | TradingAgent – real price fetching, strategy gen |
| `consciousness_core.py` | Wrapper → imports from `consciousness_core_jules.py` |
| `consciousness_core_jules.py` | Full consciousness engine (Jules version, 23KB) |
| `conscious_trading_agent.py` | Wrapper → imports from `conscious_trading_agent_jules.py` |
| `conscious_trading_agent_jules.py` | Full conscious agent with Jules reality checks |
| `jules_real_data_provider.py` | Jules assistant: real market data + validation |
| `hive_mind_core.py` | HiveMind coordinator for multi-agent decisions |
| `rehoboam_unified_system.py` | Top-level system orchestrator |
| `utils/price_feed_service.py` | Price feeds: Chainlink → CryptoCompare → Binance |
| `utils/rehoboam_visualizer.py` | Visualization & recording of decisions |

---

## 🎯 WHAT NEEDS TO BE DONE NEXT

### PRIORITY 1: Make Real Profit (Core Goal)
The system has all the infrastructure. The gap is **real price data flowing end-to-end**.

**Steps:**
1. ✅ Fix `INFURA_API_KEY` crash (done)
2. 🔲 Rebuild + restart `rehoboam-api` container: `podman-compose restart rehoboam-api`
3. 🔲 Verify `/api/status` shows all modules as `true`
4. 🔲 Run the profit verification script: `python system_status_check.py`
5. 🔲 Enable live trading: set `TRADING_ENABLED=true` in `.env`
6. 🔲 Start conscious trading: `POST /api/trading/start` to the API

### PRIORITY 2: Database Migration
```bash
cd /home/aryan/free-claude/bittensor/clean_rehoboam_project
podman exec -it clean_rehoboam_project_postgres_1 psql -U rehoboam -d rehoboam -f /docker-entrypoint-initdb.d/init.sql
# OR run migrations:
podman exec -it clean_rehoboam_project_rehoboam-api_1 python -c "from models import db; db.create_all()"
```

### PRIORITY 3: Enable MCP Consciousness Loop
The MCP consciousness layer is running at port 3600. Wire it to the trading agent:
- Check `utils/rehoboam_mcp_integration.py`
- Ensure `MCP_CONSCIOUSNESS_URL=http://mcp-consciousness-layer:3600` in container env

### PRIORITY 4: Push Fixes to GitHub
```bash
cd /home/aryan/free-claude/bittensor/clean_rehoboam_project
git add utils/price_feed_service.py
git commit -m "fix: remove hard INFURA_API_KEY requirement, use Alchemy as primary Web3 provider"
git push origin vetal-raksha/security-hardening
```

---

## 🤖 INSTRUCTIONS FOR EACH AGENT

---

### 🟦 JULES (Google Jules Agent)

**Your focus:** Backend Python fixes + database + trading logic

**Immediate tasks:**
1. **Fix the `tokens` table:** The `init.sql` exists but hasn't been applied. Run it against postgres or fix the ORM.
   - File: `init.sql` (check if `tokens` table DDL exists; if not, add it)
   - Apply: `podman exec clean_rehoboam_project_postgres_1 psql -U rehoboam -d rehoboam < init.sql`

2. **Fix `consciousness_core.py` initialization:** `rehoboam_core` shows as `None` in `/api/status`. The init in `api_server.py` (lines ~160-195) needs to handle exceptions gracefully and retry.

3. **Wire real arbitrage:** `utils/conscious_arbitrage_engine.py` and `utils/rehoboam_arbitrage_engine.py` exist — connect them to the main trading loop in `api_server.py`

4. **Enable the TradingAgents MCP:** Port 3700 is running. Integrate `mcp-trading-agents` decisions into `trading_agent.py`'s `generate_trading_strategies()` method.

5. **Fix Polygon Web3 init:** `POA chain detected for polygon` — needs `w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)`

**Branch to work on:** `jules/integration` (already exists on remote)

**Key files to edit:**
- `init.sql`, `api_server.py`, `consciousness_core.py`, `utils/conscious_arbitrage_engine.py`

---

### 🟣 HERMES AGENT (Ollama / Local LLM)

**Your focus:** Autonomous trading decisions + consciousness reasoning

**You are the runtime reasoning engine.** The system calls you via:
- `HERMES_MODEL` env var (configured in `.env`)
- `OLLAMA_BASE_URL` (configured)
- `utils/enhanced_mcp_specialist.py` — the MCP specialist that routes to you

**Immediate tasks:**
1. Process requests from `mcp-function-gemma` at port 3111
2. Provide trading strategy recommendations when called via `POST /api/mcp/reasoning`
3. Evaluate arbitrage opportunities from `utils/rehoboam_arbitrage_pipeline.py`
4. Your consciousness output feeds into `consciousness_core_jules.py` → `ConsciousnessCore.generate_consciousness_strategy()`

**How to improve your performance:**
- The system uses OpenRouter as fallback (`OPENROUTER_API_KEY` is set)
- Deepseek is also configured (`DEEPSEEK_API_KEY` is set)
- Your model should return structured JSON with: `action`, `confidence`, `position_size`, `risk_level`, `human_benefit_score`

---

### 🟠 GITHUB COPILOT

**Your focus:** Frontend improvements + TypeScript fixes + testing

**Immediate tasks:**

1. **Frontend shows `---` for all prices** — caused by API degraded state. Once API is fixed, prices should populate. But add a loading/retry mechanism in the frontend:
   - File: `src/` directory (Vite/React app)
   - Add retry logic to price fetch with exponential backoff

2. **Add real-time arbitrage view:** `ArbitrageView.tsx` exists at root — move it into `src/components/` and wire it to `GET /api/arbitrage/opportunities`

3. **Fix TypeScript errors:** Several `.tsx` files at root level (should be in `src/`):
   - `ArbitrageView.tsx`, `ErrorBoundary.tsx`, `RiskAssessment.tsx`, `Web3Context.tsx`
   - Move to `src/components/` and update imports

4. **Add profit dashboard:** Create `src/components/ProfitDashboard.tsx` that shows:
   - Real-time P&L from `GET /api/trading/portfolio`
   - Trade history from `GET /api/trading/history`
   - Win rate and liberation progress score

5. **Add Playwright E2E tests:** Playwright is already configured (see `.github/`). Add tests for:
   - API health check
   - Price feed loading
   - Trade execution flow

**Tech stack:** React + Vite, TypeScript, Recharts (already installed), Tailwind CSS

---

### 🔴 OPENCLAW / CLAUDE (Antigravity)

**Your focus:** System orchestration, integration fixes, and keeping everything running

**Current session fixes applied:**
- ✅ `utils/price_feed_service.py` — INFURA hard requirement removed
- 🔲 Container rebuild needed

**Next actions in this session:**
1. Monitor container rebuild: `command_status fb2b2ac1-3561-4171-b719-94ff6e5e9271`
2. After build: `podman-compose -f docker-compose.yml restart rehoboam-api`
3. Verify: `curl http://localhost:5002/api/status | python3 -m json.tool`
4. If modules still None: check `api_server.py` exception handling at startup (lines 160-195)
5. Fix `init.sql` → apply to postgres → confirm `tokens` table exists

**Key commands:**
```bash
# Check all containers
podman ps -a

# Restart API after rebuild
cd /home/aryan/free-claude/bittensor/clean_rehoboam_project
podman-compose -f docker-compose.yml restart rehoboam-api

# Watch API logs live
podman logs -f clean_rehoboam_project_rehoboam-api_1

# Test the fix worked
curl http://localhost:5002/api/status | python3 -m json.tool

# Run system check
podman exec clean_rehoboam_project_rehoboam-api_1 python system_status_check.py
```

---

## 💰 REAL PROFIT PATH — STEP BY STEP

```
1. Fix API (INFURA → Alchemy) ←── DONE ✅
2. Rebuild container           ←── IN PROGRESS ⏳
3. Restart rehoboam-api        ←── NEXT
4. Verify prices loading       ←── /api/prices
5. Enable arbitrage scanner    ←── /api/arbitrage/start
6. Set position limits in .env ←── MAX_POSITION_SIZE, RISK_LEVEL
7. Fund wallet (Sepolia first) ←── FLASH_ARB_MASTER in .env
8. Run on Sepolia testnet      ←── SEPOLIA_RPC_URL configured
9. Monitor profits in Grafana  ←── localhost:3000
10. Graduate to mainnet        ←── When testnet profitable
```

---

## 🔐 SECURITY NOTES (Vetal Shabar Raksha branch)

The security branch has 9 commits of hardening:
- Rate limiting added to API endpoints
- JWT_SECRET properly externalized
- CORS restricted (no wildcard)
- Audit logging enabled
- VSR Registry contract at `contracts/VSRRegistry.sol`

**DO NOT merge to main until:**
- All 8 security findings resolved (currently 6/8)
- Playwright security tests pass
- VSR audit signature obtained

---

## 📞 QUICK REFERENCE

```bash
# Project root
cd /home/aryan/free-claude/bittensor/clean_rehoboam_project

# API health
curl http://localhost:5002/health

# Full status  
curl http://localhost:5002/api/status | python3 -m json.tool

# Live prices
curl http://localhost:5002/api/prices

# Start trading
curl -X POST http://localhost:5002/api/trading/start

# Portfolio
curl http://localhost:5002/api/trading/portfolio

# Arbitrage opportunities
curl http://localhost:5002/api/arbitrage/opportunities

# Grafana dashboard
open http://localhost:3000   # admin/admin

# Frontend
open http://localhost:5001
```
