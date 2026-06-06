import { PriceFeedSocketRepository } from '../domain/repositories/PriceFeedSocketRepository';
import { PriceService } from '../application/services/PriceService';
import { ArbitrageRepository } from '../domain/repositories/ArbitrageRepository';
import { ArbitrageService } from '../application/services/ArbitrageService';

// Simple DI container
export const container = {
  priceFeedRepo: new PriceFeedSocketRepository(),
  priceService: null as any,
  arbitrageRepo: new (class implements ArbitrageRepository {
    async getOpportunities() { return []; }
  })(),
  arbitrageService: null as any,
};

container.priceService = new PriceService(container.priceFeedRepo);
container.arbitrageService = new ArbitrageService(container.arbitrageRepo);
