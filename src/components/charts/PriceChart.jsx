import React, { useMemo } from 'react';
import ReactApexChart from 'react-apexcharts';

const PriceChart = ({ seriesData = [], height = 360 }) => {
  // seriesData: array of numbers (prices) OR array of {x: timestamp, y: price}
  const ohlc = useMemo(() => {
    let prices = seriesData || [];

    // Normalize input: if it's array of objects {x, y} convert to numbers
    if (prices.length > 0 && typeof prices[0] === 'object') {
      prices = prices.map(p => p.y);
    }

    if (!prices.length) return [];

    const targetCandles = 40; // aim for ~40 candles
    const groupSize = Math.max(1, Math.floor(prices.length / targetCandles));
    const result = [];

    for (let i = 0; i < prices.length; i += groupSize) {
      const slice = prices.slice(i, i + groupSize);
      const open = slice[0];
      const close = slice[slice.length - 1];
      const high = Math.max(...slice);
      const low = Math.min(...slice);
      // create synthetic timestamp (recent to older)
      const timestamp = Date.now() - (prices.length - i) * 60000; // minute steps
      result.push({ x: new Date(timestamp), y: [open, high, low, close] });
    }

    return result;
  }, [seriesData]);

  const options = {
    chart: {
      type: 'candlestick',
      background: 'transparent',
      toolbar: { show: false },
      zoom: { enabled: true }
    },
    theme: { mode: 'dark' },
    xaxis: {
      type: 'datetime',
      labels: { datetimeUTC: false }
    },
    yaxis: {
      tooltip: { enabled: true }
    },
    tooltip: {
      enabled: true
    }
  };

  const series = [{ data: ohlc }];

  return (
    <div className="w-full">
      <ReactApexChart options={options} series={series} type="candlestick" height={height} />
    </div>
  );
};

export default PriceChart;
