import { useEffect } from 'react';
import {
  createChartSVG,
  drawChart,
  getXAxisScale,
  updateXAxis,
  updateChartElements,
} from '../../utils/waffleChartUtils';

const WaffleChart = props => {
  const chartId = '#chart';

  useEffect(() => {
    createChartContainer(chartId);
  }, []);

  useEffect(() => {
    updateChart(chartId);
  }, [props]);

  const createChartContainer = chartRef => {
    createChartSVG(chartRef, props);
    updateChart(chartRef, props);
  };

  const updateChart = elementId => {
    const { xAxisValues } = props;
    const xScale = getXAxisScale(props, xAxisValues);

    updateChartElements(props);
    updateXAxis(elementId, props, xScale);
    drawChart(elementId, props, xScale);
  };

  return <div id={chartId.substring(1)} className="waffle-chart"></div>;
};

export default WaffleChart;
