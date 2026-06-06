export interface RiskMetrics {
  pnl: number;
  exposure: number;
  marginUsage: number;
  liquidationPrice?: number;
}