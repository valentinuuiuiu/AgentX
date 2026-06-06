import { Price } from '../../models/Price';

export interface PriceFeedRepository {
  subscribe(pairs: string[], onUpdate: (prices: Record<string, Price>) => void): void;
  unsubscribe(pairs: string[]): void;
}