import { Price } from '../../models/Price';
import { PriceFeedRepository } from '../../repositories/PriceFeedRepository';

export class PriceService {
  constructor(private repo: PriceFeedRepository) {}

  start(pairs: string[], handler: (prices: Record<string, Price>) => void) {
    this.repo.subscribe(pairs, handler);
  }

  stop(pairs: string[]) {
    this.repo.unsubscribe(pairs);
  }
}