# Domain Model Overview

The Rehoboam platform is split into four **bounded contexts**:

1. **PriceFeed** – Real‑time market data (price, change, timestamp).
2. **ArbitrageEngine** – Detects cross‑pair profit opportunities.
3. **RiskManagement** – Calculates P&L, exposure, margin usage, liquidation risk.
4. **Wallet** – Handles user wallet connection, balance, and network.

Each context exposes **domain models**, **repository interfaces**, and **application services** that orchestrate business logic.  The UI consumes these services via a simple DI container, keeping the presentation layer independent from transport concerns (WebSocket, HTTP, etc.).
