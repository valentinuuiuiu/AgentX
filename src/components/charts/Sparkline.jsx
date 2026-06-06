import React from 'react';
import ReactApexChart from 'react-apexcharts';

const Sparkline = ({ data = [], color = '#34d399', height = 48 }) => {
  const series = [{ data }];
  const options = {
    chart: {
      type: 'area',
      sparkline: { enabled: true },
      toolbar: { show: false },
    },
    stroke: {
      curve: 'smooth',
      width: 2,
    },
    fill: {
      type: 'gradient',
      gradient: {
        opacityFrom: 0.4,
        opacityTo: 0.05,
      },
    },
    colors: [color],
    tooltip: { enabled: false },
  };

  return (
    <div className="w-full h-full">
      <ReactApexChart options={options} series={series} type="area" height={height} />
    </div>
  );
};

export default Sparkline;
