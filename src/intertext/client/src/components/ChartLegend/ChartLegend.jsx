const ChartLegend = ({ domainElements, chartColors }) => {
  const getDomainRangeLabel = index => {
    const min = domainElements[index];
    const max =
      index === chartColors.length - 1 ? domainElements[index + 1] : domainElements[index + 1] - 1;
    const label = `${min}% - ${max}%`;

    return label;
  };

  return (
    <div className="chart-legend">
      <div className="colors">
        {chartColors.map((chartColor, index) => (
          <div className="color-container">
            <div key={chartColor} style={{ backgroundColor: chartColor }} className="color">
              {getDomainRangeLabel(index)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChartLegend;
