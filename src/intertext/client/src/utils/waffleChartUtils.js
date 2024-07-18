import * as d3 from 'd3';

import { CHART_COLORS } from '../containers/WaffleChart/WaffleVisualization';

export const createChartSVG = chartId => {
  const chartSVG = d3.select(chartId).append('svg').attr('class', 'chart-svg');
  const chartItemsContainer = chartSVG.append('g').attr('class', 'chart-items-container');

  chartItemsContainer.append('g').attr('class', 'x axis');
  chartItemsContainer.append('g').attr('class', 'y axis');
  chartItemsContainer.append('g').attr('class', 'chart-data-container');
};

export const updateChartElements = ({ width, height, margin }) => {
  const { top: topMargin, bottom: bottomMargin, left: leftMargin } = margin;
  const chartSVG = d3.select('.chart-svg').attr('width', width).attr('height', height);

  chartSVG
    .select('.chart-items-container')
    .attr('transform', `translate(${leftMargin},${topMargin})`);
  chartSVG.select('.x.axis').attr('transform', `translate(0,${height - topMargin - bottomMargin})`);
};

export const getXAxisScale = (chartProps, xAxisValues) => {
  const {
    width,
    margin: { right: rightMargin, left: leftMargin },
  } = chartProps;

  return d3
    .scaleBand()
    .domain(xAxisValues)
    .range([0, width - rightMargin - leftMargin]);
};

export const updateXAxis = (chartId, { xAxisLabelRotation }, xScale) => {
  const xAxis = d3.axisBottom(xScale).tickPadding(5);
  const transform = `rotate(${xAxisLabelRotation})`;

  d3.select(`${chartId} g.x.axis`)
    .call(xAxis)
    .selectAll('text')
    .style('text-anchor', 'start')
    .attr('transform', transform);
};

export const drawChart = (chartId, chartProps, xScale) => {
  const {
    chartData,
    height,
    squareSize,
    margin: { bottom: bottomMargin },
    marginBetweenColumns,
    maxColumn,
    columnCounts,
    chartDataDomain,
    onClick,
  } = chartProps;

  const chart = d3
    .select(`${chartId} .chart-data-container`)
    .selectAll('.square')
    .data(chartData, ({ id }) => id);

  const initialJoin = chart
    .enter()
    .append('rect')
    .attr('class', 'square')
    .attr('x', 0)
    .attr('y', 0)
    .on('click', squareData => onClick(squareData.id));

  const calculateCoordinateX = currentSquareData => {
    const { x: xAxisValue, column } = currentSquareData;

    const xAxisScale = xScale(xAxisValue);
    const existingColumnsWidth = column * squareSize;
    const emptyColumnsWidth = (maxColumn - columnCounts[xAxisValue]) * squareSize;
    const centerOfXAxisValueColumns = (emptyColumnsWidth + marginBetweenColumns) / 2;
    const xCoordinate = xAxisScale + existingColumnsWidth + centerOfXAxisValueColumns;

    return xCoordinate;
  };

  const calculateCoordinateY = currentSquareData => {
    const { row } = currentSquareData;

    // row starts from 0
    const actualRow = row + 1;
    const actualHeight = height - bottomMargin;
    const existingRowsHeight = actualRow * squareSize;
    const yCoordinate = actualHeight - existingRowsHeight;

    return yCoordinate;
  };

  // Add white color to the beginning of the array.
  // Explanation from the D3js documentation (scaleThreshold):
  // "If the number of values in the scale’s domain is n, the number of values in the scale’s range must be n + 1."
  // Any value below domain[0] will be '#fff'.
  const colors = ['#fff', ...CHART_COLORS];
  const getColor = d3.scaleThreshold().domain(chartDataDomain).range(colors);

  chart
    .merge(initialJoin)
    .transition()
    .duration(750)
    .attr('width', squareSize)
    .attr('height', squareSize)
    .attr('x', calculateCoordinateX)
    .attr('y', calculateCoordinateY)
    .attr('fill', ({ similarity }) => getColor(similarity))
    .attr('stroke-width', 1);

  chart.exit().remove();
};
