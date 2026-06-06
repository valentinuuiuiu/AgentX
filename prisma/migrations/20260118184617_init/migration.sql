-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "username" TEXT NOT NULL,
    "passwordHash" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "sessions" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "expiresAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "wallets" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "address" TEXT NOT NULL,
    "chainId" INTEGER NOT NULL,
    "walletType" TEXT NOT NULL DEFAULT 'metaMask',
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "wallets_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "wallet_balances" (
    "id" TEXT NOT NULL,
    "walletId" TEXT NOT NULL,
    "tokenSymbol" TEXT NOT NULL,
    "balance" DECIMAL(32,18) NOT NULL,
    "valueUsd" DECIMAL(32,8),
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "wallet_balances_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_preferences" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "riskTolerance" TEXT NOT NULL DEFAULT 'moderate',
    "defaultNetwork" TEXT NOT NULL DEFAULT 'arbitrum',
    "defaultSlippage" DECIMAL(5,4) NOT NULL DEFAULT 0.01,
    "notifications" BOOLEAN NOT NULL DEFAULT true,
    "theme" TEXT NOT NULL DEFAULT 'dark',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_preferences_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "tokens" (
    "id" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "decimals" INTEGER NOT NULL DEFAULT 18,
    "contractAddr" TEXT,
    "coingeckoId" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "tokens_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "price_points" (
    "id" TEXT NOT NULL,
    "tokenId" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "price" DECIMAL(32,18) NOT NULL,
    "volume" DECIMAL(32,8),
    "high24h" DECIMAL(32,18),
    "low24h" DECIMAL(32,18),
    "change24h" DECIMAL(32,18),
    "signal" TEXT,
    "confidence" DECIMAL(5,4),
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "price_points_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "market_sentiments" (
    "id" TEXT NOT NULL,
    "tokenSymbol" TEXT NOT NULL,
    "sentiment" DECIMAL(5,4) NOT NULL,
    "fearGreedIndex" INTEGER,
    "trend" TEXT NOT NULL,
    "volatility" TEXT NOT NULL,
    "rsi" DECIMAL(5,2),
    "macd" TEXT,
    "supportLevels" REAL[],
    "resistanceLevels" REAL[],
    "reasoning" TEXT,
    "source" TEXT NOT NULL DEFAULT 'rehoboam',
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "market_sentiments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "strategies" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "riskLevel" TEXT NOT NULL DEFAULT 'moderate',
    "confidence" DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    "expectedReturn" DECIMAL(5,4),
    "timeframe" TEXT,
    "networks" TEXT[],
    "parameters" JSONB,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "executions" INTEGER NOT NULL DEFAULT 0,
    "successRate" DECIMAL(5,4),
    "reasoning" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "strategies_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "trades" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "walletId" TEXT NOT NULL,
    "strategyId" TEXT,
    "tokenId" TEXT NOT NULL,
    "action" TEXT NOT NULL,
    "amount" DECIMAL(32,18) NOT NULL,
    "price" DECIMAL(32,18) NOT NULL,
    "priceUsd" DECIMAL(32,8),
    "network" TEXT NOT NULL,
    "slippage" DECIMAL(5,4) NOT NULL,
    "gasFee" DECIMAL(32,18),
    "gasFeeUsd" DECIMAL(32,8),
    "status" TEXT NOT NULL DEFAULT 'pending',
    "txHash" TEXT,
    "errorMessage" TEXT,
    "executedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "trades_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "portfolios" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "totalValueUsd" DECIMAL(32,8) NOT NULL DEFAULT 0,
    "dailyPnL" DECIMAL(32,8),
    "dailyPnLPercent" DECIMAL(5,4),
    "totalPnL" DECIMAL(32,8),
    "totalPnLPercent" DECIMAL(5,4),
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "portfolios_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "positions" (
    "id" TEXT NOT NULL,
    "portfolioId" TEXT NOT NULL,
    "tokenSymbol" TEXT NOT NULL,
    "amount" DECIMAL(32,18) NOT NULL,
    "avgBuyPrice" DECIMAL(32,18) NOT NULL,
    "currentPrice" DECIMAL(32,18),
    "valueUsd" DECIMAL(32,8),
    "unrealizedPnL" DECIMAL(32,8),
    "network" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "positions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "arbitrage_opportunities" (
    "id" TEXT NOT NULL,
    "tokenId" TEXT NOT NULL,
    "sourceExchange" TEXT NOT NULL,
    "targetExchange" TEXT NOT NULL,
    "sourcePrice" DECIMAL(32,18) NOT NULL,
    "targetPrice" DECIMAL(32,18) NOT NULL,
    "priceDiff" DECIMAL(5,4) NOT NULL,
    "profitPotential" DECIMAL(32,18) NOT NULL,
    "gasEstimate" DECIMAL(32,18) NOT NULL,
    "netProfit" DECIMAL(32,18) NOT NULL,
    "confidence" DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    "riskScore" DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    "status" TEXT NOT NULL DEFAULT 'detected',
    "executedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "arbitrage_opportunities_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "arbitrage_executions" (
    "id" TEXT NOT NULL,
    "opportunityId" TEXT NOT NULL,
    "buyTxHash" TEXT,
    "sellTxHash" TEXT,
    "buyAmount" DECIMAL(32,18) NOT NULL,
    "sellAmount" DECIMAL(32,18) NOT NULL,
    "buyPrice" DECIMAL(32,18) NOT NULL,
    "sellPrice" DECIMAL(32,18) NOT NULL,
    "profit" DECIMAL(32,18) NOT NULL,
    "gasUsed" DECIMAL(32,18) NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "errorMessage" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "arbitrage_executions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_signals" (
    "id" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "tokenSymbol" TEXT NOT NULL,
    "signal" TEXT NOT NULL,
    "confidence" DECIMAL(5,4) NOT NULL,
    "reasoning" TEXT,
    "model" TEXT,
    "metadata" JSONB,
    "validFrom" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "validTo" TIMESTAMP(3),
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_signals_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "hive_mind_states" (
    "id" TEXT NOT NULL,
    "emotion" TEXT NOT NULL,
    "sentiment" DECIMAL(5,4) NOT NULL,
    "marketOutlook" TEXT NOT NULL,
    "riskAppetite" DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    "confidence" DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    "reasoning" TEXT,
    "emotionalDrivers" TEXT[],
    "matrix" INTEGER[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "hive_mind_states_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "hive_mind_memories" (
    "id" TEXT NOT NULL,
    "eventType" TEXT NOT NULL,
    "eventData" JSONB NOT NULL,
    "outcome" TEXT,
    "learning" TEXT,
    "importance" DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "hive_mind_memories_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "mcp_functions" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "category" TEXT NOT NULL,
    "parameters" JSONB NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "usageCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "mcp_functions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "mcp_function_calls" (
    "id" TEXT NOT NULL,
    "functionId" TEXT NOT NULL,
    "input" JSONB NOT NULL,
    "output" JSONB,
    "duration" INTEGER,
    "success" BOOLEAN NOT NULL DEFAULT true,
    "errorMessage" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "mcp_function_calls_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_companions" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "personality" TEXT NOT NULL,
    "expertise" TEXT[],
    "model" TEXT NOT NULL DEFAULT 'gpt-4.1-mini',
    "systemPrompt" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "memory" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ai_companions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "companion_conversations" (
    "id" TEXT NOT NULL,
    "companionId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "messages" JSONB NOT NULL,
    "summary" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "companion_conversations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "contract_audits" (
    "id" TEXT NOT NULL,
    "contractAddr" TEXT NOT NULL,
    "network" TEXT NOT NULL,
    "auditTask" TEXT NOT NULL,
    "result" JSONB NOT NULL,
    "riskLevel" TEXT,
    "findings" TEXT,
    "model" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "contract_audits_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "users_username_key" ON "users"("username");

-- CreateIndex
CREATE UNIQUE INDEX "sessions_token_key" ON "sessions"("token");

-- CreateIndex
CREATE UNIQUE INDEX "wallets_address_key" ON "wallets"("address");

-- CreateIndex
CREATE UNIQUE INDEX "wallets_userId_address_key" ON "wallets"("userId", "address");

-- CreateIndex
CREATE UNIQUE INDEX "wallet_balances_walletId_tokenSymbol_key" ON "wallet_balances"("walletId", "tokenSymbol");

-- CreateIndex
CREATE UNIQUE INDEX "user_preferences_userId_key" ON "user_preferences"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "tokens_symbol_key" ON "tokens"("symbol");

-- CreateIndex
CREATE INDEX "price_points_tokenId_timestamp_idx" ON "price_points"("tokenId", "timestamp");

-- CreateIndex
CREATE UNIQUE INDEX "market_sentiments_tokenSymbol_timestamp_key" ON "market_sentiments"("tokenSymbol", "timestamp");

-- CreateIndex
CREATE INDEX "trades_userId_createdAt_idx" ON "trades"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "trades_walletId_createdAt_idx" ON "trades"("walletId", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "portfolios_userId_key" ON "portfolios"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "positions_portfolioId_tokenSymbol_network_key" ON "positions"("portfolioId", "tokenSymbol", "network");

-- CreateIndex
CREATE INDEX "arbitrage_opportunities_tokenId_createdAt_idx" ON "arbitrage_opportunities"("tokenId", "createdAt");

-- CreateIndex
CREATE INDEX "ai_signals_tokenSymbol_source_createdAt_idx" ON "ai_signals"("tokenSymbol", "source", "createdAt");

-- CreateIndex
CREATE INDEX "hive_mind_states_createdAt_idx" ON "hive_mind_states"("createdAt");

-- CreateIndex
CREATE INDEX "hive_mind_memories_eventType_createdAt_idx" ON "hive_mind_memories"("eventType", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "mcp_functions_name_key" ON "mcp_functions"("name");

-- CreateIndex
CREATE INDEX "mcp_function_calls_functionId_createdAt_idx" ON "mcp_function_calls"("functionId", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "ai_companions_name_key" ON "ai_companions"("name");

-- CreateIndex
CREATE INDEX "companion_conversations_companionId_createdAt_idx" ON "companion_conversations"("companionId", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "contract_audits_contractAddr_network_auditTask_key" ON "contract_audits"("contractAddr", "network", "auditTask");

-- AddForeignKey
ALTER TABLE "sessions" ADD CONSTRAINT "sessions_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "wallets" ADD CONSTRAINT "wallets_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "wallet_balances" ADD CONSTRAINT "wallet_balances_walletId_fkey" FOREIGN KEY ("walletId") REFERENCES "wallets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_preferences" ADD CONSTRAINT "user_preferences_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "price_points" ADD CONSTRAINT "price_points_tokenId_fkey" FOREIGN KEY ("tokenId") REFERENCES "tokens"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "strategies" ADD CONSTRAINT "strategies_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "trades" ADD CONSTRAINT "trades_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "trades" ADD CONSTRAINT "trades_walletId_fkey" FOREIGN KEY ("walletId") REFERENCES "wallets"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "trades" ADD CONSTRAINT "trades_strategyId_fkey" FOREIGN KEY ("strategyId") REFERENCES "strategies"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "trades" ADD CONSTRAINT "trades_tokenId_fkey" FOREIGN KEY ("tokenId") REFERENCES "tokens"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "portfolios" ADD CONSTRAINT "portfolios_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "positions" ADD CONSTRAINT "positions_portfolioId_fkey" FOREIGN KEY ("portfolioId") REFERENCES "portfolios"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "arbitrage_opportunities" ADD CONSTRAINT "arbitrage_opportunities_tokenId_fkey" FOREIGN KEY ("tokenId") REFERENCES "tokens"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "mcp_function_calls" ADD CONSTRAINT "mcp_function_calls_functionId_fkey" FOREIGN KEY ("functionId") REFERENCES "mcp_functions"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "companion_conversations" ADD CONSTRAINT "companion_conversations_companionId_fkey" FOREIGN KEY ("companionId") REFERENCES "ai_companions"("id") ON DELETE CASCADE ON UPDATE CASCADE;
