import React, { useMemo } from 'react';

export function PriceChart({ data, pair }) {
  const width = 600;
  const height = 300;
  const margin = { top: 5, right: 5, bottom: 30, left: 50 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const formatCurrency = (value) => {
    if (value == null || isNaN(value)) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency: 'USD',
      minimumFractionDigits: 2, maximumFractionDigits: 2
    }).format(value);
  };

  const { path, xTicks, yTicks } = useMemo(() => {
    if (!data || data.length === 0) {
      return { path: '', xTicks: [], yTicks: [] };
    }

    const prices = data.map(d => d.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const padding = (maxPrice - minPrice) * 0.1 || 1;
    const yMin = minPrice - padding;
    const yMax = maxPrice + padding;

    const xScale = (i) => margin.left + (i / (data.length - 1)) * innerWidth;
    const yScale = (v) => margin.top + innerHeight - ((v - yMin) / (yMax - yMin)) * innerHeight;

    const pathD = data.map((d, i) => {
      const x = xScale(i);
      const y = yScale(d.price);
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    const step = Math.max(1, Math.floor(data.length / 5));
    const xTicks = data.filter((_, i) => i % step === 0 || i === data.length - 1).map((d, i) => ({
      x: xScale(i * step),
      label: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }));

    const yTickCount = 5;
    const yTicks = Array.from({ length: yTickCount + 1 }, (_, i) => {
      const value = yMin + (i / yTickCount) * (yMax - yMin);
      return {
        y: yScale(value),
        value: value.toFixed(2),
      };
    });

    return { path: pathD, xTicks, yTicks };
  }, [data, innerWidth, innerHeight]);

  if (!data || data.length === 0) {
    return (
      <div className="h-[300px] w-full flex items-center justify-center bg-gray-900 rounded-lg">
        <p className="text-gray-400">No price data available</p>
      </div>
    );
  }

  return (
    <div className="h-[300px] w-full">
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        className="w-full h-full"
      >
        {/* Grid lines */}
        {yTicks.map((tick, i) => (
          <g key={`grid-${i}`}>
            <line
              x1={margin.left}
              y1={tick.y}
              x2={width - margin.right}
              y2={tick.y}
              stroke="#374151"
              strokeDasharray="3 3"
            />
          </g>
        ))}

        {/* Y axis */}
        <line
          x1={margin.left} y1={margin.top}
          x2={margin.left} y2={height - margin.bottom}
          stroke="#4B5563"
        />
        {yTicks.map((tick, i) => (
          <g key={`y-${i}`}>
            <text
              x={margin.left - 8} y={tick.y + 4}
              textAnchor="end" fill="#9CA3AF" fontSize={10}
            >
              {tick.value}
            </text>
          </g>
        ))}

        {/* X axis */}
        <line
          x1={margin.left} y1={height - margin.bottom}
          x2={width - margin.right} y2={height - margin.bottom}
          stroke="#4B5563"
        />
        {xTicks.map((tick, i) => (
          <g key={`x-${i}`}>
            <text
              x={tick.x} y={height - margin.bottom + 16}
              textAnchor="middle" fill="#9CA3AF" fontSize={10}
            >
              {tick.label}
            </text>
          </g>
        ))}

        {/* Data line */}
        <path
          d={path}
          fill="none"
          stroke="#10B981"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
