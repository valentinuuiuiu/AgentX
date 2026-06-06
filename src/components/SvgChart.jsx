import React, { useMemo } from 'react';

export function SvgLineChart({ data, width = 600, height = 300, margin = { top: 5, right: 5, bottom: 30, left: 50 } }) {
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const { path, xTicks, yTicks, yDomain } = useMemo(() => {
    if (!data || data.length === 0) return { path: '', xTicks: [], yTicks: [], yDomain: [0, 0] };

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

    const xTicks = data.filter((_, i) => i % Math.ceil(data.length / 5) === 0).map((d, i) => ({
      x: xScale(i * Math.ceil(data.length / 5)),
      label: new Date(d.timestamp).toLocaleTimeString(),
    }));

    const yTickCount = 5;
    const yTicks = Array.from({ length: yTickCount + 1 }, (_, i) => {
      const value = yMin + (i / yTickCount) * (yMax - yMin);
      return {
        y: yScale(value),
        value: value.toFixed(2),
      };
    });

    return { path: pathD, xTicks, yTicks, yDomain: [yMin, yMax] };
  }, [data, margin.left, margin.right, margin.top, margin.bottom, innerWidth, innerHeight]);

  if (!data || data.length === 0) {
    return (
      <svg width={width} height={height} className="w-full h-full">
        <text x={width / 2} y={height / 2} textAnchor="middle" fill="#9CA3AF">
          No data
        </text>
      </svg>
    );
  }

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
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
      <line x1={margin.left} y1={margin.top} x2={margin.left} y2={height - margin.bottom} stroke="#4B5563" />
      {yTicks.map((tick, i) => (
        <g key={`y-${i}`}>
          <text x={margin.left - 8} y={tick.y + 4} textAnchor="end" fill="#9CA3AF" fontSize={10}>
            {tick.value}
          </text>
        </g>
      ))}

      {/* X axis */}
      <line x1={margin.left} y1={height - margin.bottom} x2={width - margin.right} y2={height - margin.bottom} stroke="#4B5563" />
      {xTicks.map((tick, i) => (
        <g key={`x-${i}`}>
          <text x={tick.x} y={height - margin.bottom + 16} textAnchor="middle" fill="#9CA3AF" fontSize={10}>
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
  );
}

export function SvgSparkline({ data, width = 200, height = 60, color = '#10B981' }) {
  const pathD = useMemo(() => {
    if (!data || data.length === 0) return '';
    const values = data.map(d => d.price || d.value || d);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    return values.map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  }, [data, width, height]);

  if (!data || data.length === 0) return null;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SvgAreaChart({ data, width = 600, height = 300, color = '#10B981', fillOpacity = 0.1 }) {
  const { path, areaPath } = useMemo(() => {
    if (!data || data.length === 0) return { path: '', areaPath: '' };
    const values = data.map(d => d.price || d.value || 0);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    const points = values.map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - min) / range) * (height - 20) - 10;
      return [x, y];
    });

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`).join(' ');
    const areaD = `${pathD} L ${width} ${height} L 0 ${height} Z`;

    return { path: pathD, areaPath: areaD };
  }, [data, width, height]);

  if (!data || data.length === 0) return null;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
      <defs>
        <linearGradient id={`area-gradient-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={fillOpacity + 0.15} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#area-gradient-${color.replace('#', '')})`} />
      <path d={path} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" />
    </svg>
  );
}
