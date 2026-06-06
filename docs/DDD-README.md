# DDD Core Domain – Rehoboam Trading Platform

## What has been built
- **Domain models** (`src/domain/models/*.ts`) for `Price`, `ArbitrageOpportunity`, `RiskMetrics`, `Wallet`.
- **Repository contracts** (`src/domain/repositories/*.ts`) that abstract the external data sources.
- **Application services** (`src/application/services/*.ts`) that implement the use‑cases:
  - `PriceService` – subscribes to live price updates.
  - `ArbitrageService` – fetches current arbitrage opportunities.
  - `RiskService` – (placeholder) provides risk metrics.
- **DI container** (`src/infrastructure/di.ts`) wiring concrete implementations.
- **UI integration** – `TradingInterface` now uses `PriceService` via the container, removing direct WebSocket handling.
- **Unit‑test scaffold** – folder `src/application/__tests__` prepared for future tests.
- **Documentation** – `docs/domain-model.md` and this README.

## Next steps
1. Implement concrete `ArbitrageRepository` and `RiskRepository` (e.g., call backend APIs).
2. Add unit tests for each service (Jest + React Testing Library).
3. Extend the UI with the `ArbitrageService` and risk display widgets.
4. Secure the WebSocket connection (auth tokens, reconnection strategy).
5. Deploy the backend WS server (`npm run ws`) alongside the Vite dev server.

## How to use
```ts
import { container } from './infrastructure/di';
container.priceService.start(["ETH/USD","BTC/USD"], (prices) => {
  // React state update or other side‑effects
});
```

Feel free to extend the domain model as new trading features arise.
