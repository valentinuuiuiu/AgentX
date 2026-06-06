import { useState, useEffect, useCallback, useRef } from 'react';

interface BOSignalData {
  symbol: string;
  price: number;
  signal?: 'BUY' | 'SELL' | 'HOLD';
  confidence?: number;
  timestamp: number;
  source: 'bo_signals_ai';
}

interface BOSignalsAIHook {
  signals: Map<string, BOSignalData>;
  isConnected: boolean;
  lastUpdate: number | null;
  error: string | null;
  getSignal: (symbol: string) => BOSignalData | undefined;
  getAllSignals: () => BOSignalData[];
}

export function useBOSignalsAI(): BOSignalsAIHook {
  const [signals, setSignals] = useState<Map<string, BOSignalData>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const listenersRef = useRef<Set<(data: BOSignalData) => void>>(new Set());

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      try {
        if (event.source !== window) return;

        const message = event.data;
        if (!message || typeof message !== 'object') return;

        if (message.type === 'BO_SIGNALS_UPDATE' || message.type === 'BO_SIGNALS_PRICE') {
          const data = message.data as BOSignalData;
          if (data && data.symbol && typeof data.price === 'number') {
            setSignals(prev => {
              const newSignals = new Map(prev);
              newSignals.set(data.symbol.toUpperCase(), {
                ...data,
                symbol: data.symbol.toUpperCase(),
                source: 'bo_signals_ai'
              });
              return newSignals;
            });
            setLastUpdate(Date.now());
            setIsConnected(true);
            setError(null);

            listenersRef.current.forEach(callback => callback(data));
          }
        } else if (message.type === 'BO_SIGNALS_CONNECTED') {
          setIsConnected(true);
          setError(null);
        } else if (message.type === 'BO_SIGNALS_ERROR') {
          setError(message.error || 'Unknown error from BO Signals AI');
        }
      } catch (err) {
        console.error('Error processing BO Signals message:', err);
      }
    };

    const handleCustomEvent = (event: CustomEvent) => {
      try {
        const data = event.detail as BOSignalData;
        if (data && data.symbol && typeof data.price === 'number') {
          setSignals(prev => {
            const newSignals = new Map(prev);
            newSignals.set(data.symbol.toUpperCase(), {
              ...data,
              symbol: data.symbol.toUpperCase(),
              source: 'bo_signals_ai'
            });
            return newSignals;
          });
          setLastUpdate(Date.now());
          setIsConnected(true);
          setError(null);
        }
      } catch (err) {
        console.error('Error processing BO Signals custom event:', err);
      }
    };

    window.addEventListener('message', handleMessage);
    window.addEventListener('bo_signals_update', handleCustomEvent as EventListener);

    const checkExtension = () => {
      const hasBOSignals = (
        typeof (window as any).BOSignalsAI !== 'undefined' ||
        typeof (window as any).boSignals !== 'undefined' ||
        typeof (window as any).BOSignals !== 'undefined' ||
        document.querySelector('[data-bo-signals]') !== null
      );

      if (hasBOSignals) {
        setIsConnected(true);
        (window as any).BOSignalsAI?.onPriceUpdate?.((data: BOSignalData) => {
          setSignals(prev => {
            const newSignals = new Map(prev);
            newSignals.set(data.symbol.toUpperCase(), data);
            return newSignals;
          });
          setLastUpdate(Date.now());
        });
      } else {
        setTimeout(checkExtension, 1000);
      }
    };

    const timer = setTimeout(checkExtension, 500);

    return () => {
      window.removeEventListener('message', handleMessage);
      window.removeEventListener('bo_signals_update', handleCustomEvent as EventListener);
      clearTimeout(timer);
    };
  }, []);

  const getSignal = useCallback((symbol: string): BOSignalData | undefined => {
    return signals.get(symbol.toUpperCase());
  }, [signals]);

  const getAllSignals = useCallback((): BOSignalData[] => {
    return Array.from(signals.values());
  }, [signals]);

  return {
    signals,
    isConnected,
    lastUpdate,
    error,
    getSignal,
    getAllSignals
  };
}

export default useBOSignalsAI;
