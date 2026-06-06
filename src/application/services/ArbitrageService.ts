import { ArbitrageOpportunity } from '../../models/ArbitrageOpportunity';
import { ArbitrageRepository } from '../../repositories/ArbitrageRepository';

export class ArbitrageService {
  constructor(private repo: ArbitrageRepository) {}

  async getCurrent(): Promise<ArbitrageOpportunity[]> {
    return await this.repo.getOpportunities();
  }
}