import { PriceService } from '../../application/services/PriceService';
import { PriceFeedRepository } from '../../domain/repositories/PriceFeedRepository';

class MockPriceFeedRepo implements PriceFeedRepository {
  subscribe(pairs: string[], onUpdate: (prices: Record<string, any>) => void) {}
  unsubscribe(pairs: string[]) {}
}

describe('PriceService', () => {
  it('starts and stops without error', () => {
    const repo = new MockPriceFeedRepo();
    const service = new PriceService(repo);
    const mockHandler = jest.fn();
    service.start(['ETH/USD'], mockHandler);
    expect(mockHandler).not.toHaveBeenCalled();
    service.stop(['ETH/USD']);
  });
});
