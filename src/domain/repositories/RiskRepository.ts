import { RiskMetrics } from '../../models/RiskMetrics';

export interface RiskRepository {
  getMetrics(): Promise<RiskMetrics>;
}