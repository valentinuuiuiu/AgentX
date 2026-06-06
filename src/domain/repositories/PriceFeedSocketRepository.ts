import { Price } from '../../models/Price';

export class PriceFeedSocketRepository implements PriceFeedRepository {
  private ws: WebSocket | null = null;

  private listeners: Map<string, (prices: Record<string, Price>) => void> = new Map();

  constructor() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new WebSocket(`${protocol}//${window.location.hostname}:3001/ws/prices`);
    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'price_update') {
          const data: Record<string, Price> = msg.data;
          this.listeners.forEach(cb => cb(data));
        }
      } catch (e) {
        console.error('WS parse error', e);
      }
    };
  }

  subscribe(pairs: string[], onUpdate: (prices: Record<string, Price>) => void): void {
    // For simplicity, we ignore pair filtering here.
    this.listeners.set(pairs.join(','), onUpdate);
    // Notify server of subscription
    this.ws?.send(JSON.stringify({ type: 'subscribe', pairs }));
  }

  unsubscribe(pairs: string[]): void {
    this.listeners.delete(pairs.join(','));
    this.ws?.send(JSON.stringify({ type: 'unsubscribe', pairs }));
  }
}