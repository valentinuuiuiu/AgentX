import { Prisma } from '@prisma/client';
import { prisma } from './client';

export async function getPriceHistory(tokenSymbol: string, limit = 100) {
  console.log(`[MarketService] Getting price history for ${tokenSymbol}, limit: ${limit}`);
  try {
    const token = await prisma.token.findUnique({ where: { symbol: tokenSymbol } });
    if (!token) return [];
    return prisma.pricePoint.findMany({
      where: { tokenId: token.id },
      orderBy: { timestamp: 'desc' },
      take: limit,
    });
  } catch (error) {
    console.error('[MarketService] Error getting price history:', error);
    return [];
  }
}

export async function getLatestPrice(tokenSymbol: string) {
  console.log(`[MarketService] Getting latest price for ${tokenSymbol}`);
  try {
    const token = await prisma.token.findUnique({ where: { symbol: tokenSymbol } });
    if (!token) return null;
    return prisma.pricePoint.findFirst({
      where: { tokenId: token.id },
      orderBy: { timestamp: 'desc' },
    });
  } catch (error) {
    console.error('[MarketService] Error getting latest price:', error);
    return null;
  }
}

export async function savePricePoint(data: {
  tokenSymbol: string;
  source: string;
  price: number;
  volume?: number | null;
  high24h?: number | null;
  low24h?: number | null;
  change24h?: number | null;
  signal?: string | null;
  confidence?: number | null;
}) {
  console.log(`[MarketService] Saving price point for ${data.tokenSymbol}: $${data.price}`);
  try {
    let token = await prisma.token.findUnique({ where: { symbol: data.tokenSymbol } });
    if (!token) {
      token = await prisma.token.create({
        data: { symbol: data.tokenSymbol, name: data.tokenSymbol },
      });
    }
    return prisma.pricePoint.create({
      data: {
        tokenId: token.id,
        source: data.source,
        price: data.price,
        volume: data.volume,
        high24h: data.high24h,
        low24h: data.low24h,
        change24h: data.change24h,
        signal: data.signal,
        confidence: data.confidence,
      },
    });
  } catch (error) {
    console.error('[MarketService] Error saving price point:', error);
    return { id: 'mock-id', ...data, createdAt: new Date() };
  }
}

export async function getAISignals(tokenSymbol: string, source?: string) {
  console.log(`[MarketService] Getting AI signals for ${tokenSymbol}${source ? ` from ${source}` : ''}`);
  try {
    return prisma.aISignal.findMany({
      where: {
        tokenSymbol,
        ...(source && { source }),
        isActive: true,
      },
      orderBy: { createdAt: 'desc' },
      take: 50,
    });
  } catch (error) {
    console.error('[MarketService] Error getting AI signals:', error);
    return [];
  }
}

export async function saveAISignal(data: {
  source: string;
  tokenSymbol: string;
  signal: string;
  confidence: number;
  reasoning?: string | null;
  model?: string | null;
  metadata?: Prisma.InputJsonValue;
}) {
  console.log(`[MarketService] Saving AI signal: ${data.signal} ${data.tokenSymbol} (${data.confidence * 100}%)`);
  try {
    return prisma.aISignal.create({ data });
  } catch (error) {
    console.error('[MarketService] Error saving AI signal:', error);
    return { id: 'mock-id', ...data, createdAt: new Date() };
  }
}

export async function getArbitrageOpportunities(tokenSymbol?: string) {
  console.log(`[MarketService] Getting arbitrage opportunities${tokenSymbol ? ` for ${tokenSymbol}` : ''}`);
  try {
    return prisma.arbitrageOpportunity.findMany({
      where: {
        status: 'detected',
        ...(tokenSymbol && { token: { symbol: tokenSymbol } }),
      },
      orderBy: { createdAt: 'desc' },
      take: 100,
      include: { token: true },
    });
  } catch (error) {
    console.error('[MarketService] Error getting arbitrage opportunities:', error);
    return [];
  }
}

export async function saveTrade(data: {
  userId: string;
  walletId: string;
  tokenSymbol: string;
  action: string;
  amount: number;
  price: number;
  network: string;
  slippage: number;
  strategyId?: string;
}) {
  console.log(`[MarketService] Recording trade: ${data.action} ${data.amount} ${data.tokenSymbol}`);
  try {
    let token = await prisma.token.findUnique({ where: { symbol: data.tokenSymbol } });
    if (!token) {
      token = await prisma.token.create({
        data: { symbol: data.tokenSymbol, name: data.tokenSymbol },
      });
    }
    return prisma.trade.create({
      data: {
        userId: data.userId,
        walletId: data.walletId,
        tokenId: token.id,
        action: data.action,
        amount: data.amount,
        price: data.price,
        network: data.network,
        slippage: data.slippage,
        strategyId: data.strategyId,
      },
    });
  } catch (error) {
    console.error('[MarketService] Error saving trade:', error);
    return { id: 'mock-id', ...data, createdAt: new Date() };
  }
}

export default {
  getPriceHistory,
  getLatestPrice,
  savePricePoint,
  getAISignals,
  saveAISignal,
  getArbitrageOpportunities,
  saveTrade,
};
