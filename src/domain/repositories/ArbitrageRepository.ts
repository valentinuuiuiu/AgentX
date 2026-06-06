import { ArbitrageOpportunity } from '../../models/ArbitrageOpportunity';

export interface ArbitrageRepository {
  getOpportunities(): Promise<ArbitrageOpportunity[]>;
}