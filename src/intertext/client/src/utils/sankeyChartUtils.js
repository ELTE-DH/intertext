import * as d3 from 'd3';
import { sankey, sankeyLinkHorizontal } from 'd3-sankey';

import { CHART_COLORS } from '../containers/SankeyChart/SankeyChart';

const SVG_MARGIN = { top: 50, right: 200, bottom: 50, left: 220 };
const SVG_WIDTH = 950;
const LINE_HEIGHT = 30;
const NODE_WIDTH = 10;
const NODE_LABEL_WIDTH = 210;
const PADDING_BETWEEN_NODES = 20;
const TITLE_WIDTH = 25;

// ADDITIONAL FUNCTIONS
// Create an svg for the sankey chart
const createChartSVG = (chartId, svgHeight) => {
  const { top: topMargin, left: leftMargin } = SVG_MARGIN;

  return d3
    .select(chartId)
    .append('svg')
    .attr('width', SVG_WIDTH)
    .attr('height', svgHeight)
    .attr('class', 'chart-svg')
    .append('g')
    .attr('class', 'chart-elements-container')
    .attr('transform', `translate(${leftMargin}, ${topMargin})`);
};

// Create the nodes container and the nodes of the sankey chart
const createChartNodes = (chartSvg, sankeyNodes) => {
  return chartSvg
    .append('g')
    .attr('class', 'chart-nodes')
    .selectAll('.node')
    .data(sankeyNodes)
    .enter()
    .append('g')
    .attr('class', 'node')
    .attr('transform', ({ x0, y0 }) => `translate(${x0},${y0})`);
};

// Handle search when user click on a line
const handleSearch = (lineData, onSearch) => {
  onSearch({ sourceId: lineData.source.id, targetId: lineData.target.id });
};

// Assemble the label which appear on 'line hover'
const getLabel = (source, target) => {
  const { label: sourceLabel, author: sourceAuthor, year: sourceYear } = source;
  const { label: targetLabel, author: targetAuthor, year: targetYear } = target;

  return `${sourceAuthor} (${sourceYear}): ${sourceLabel}\n\n${targetAuthor} (${targetYear}): ${targetLabel}`;
};

// Check if the work is an earlier/later text
const checkType = (id, type) => {
  return id.indexOf(type) === 0;
};

// Calculate the y axis offset
const calculateYOffset = (y0, y1) => y1 - y0;

// Get the shortened title of the current work
const getShortenedTitle = title => {
  let titleString = title;

  if (title.length > TITLE_WIDTH) {
    titleString = `${title.slice(0, TITLE_WIDTH)}...`;
  }

  return titleString;
};

// Add the 'selected' classname
const setLinesToSelected = ({ nodeId, id }) => {
  const selector = ['.line'];

  if (checkType(nodeId, 'earlier')) {
    selector.push(`.source-node-${id}`);
  } else if (checkType(nodeId, 'later')) {
    selector.push(`.target-node-${id}`);
  }

  d3.selectAll(selector.join('')).classed('selected', true);
};

// Remove the 'selected' classname
const resetSelectedLines = () => {
  d3.selectAll('.line').classed('selected', false);
};

// MAIN FUNCTION
// Create the sankey chart
export const createSankeyChart = ({ chartId, chartData, domain, onSearch }) => {
  const { top: topMargin, right: rightMargin, bottom: bottomMargin, left: leftMargin } = SVG_MARGIN;
  const { nodes: chartNodesData, links: chartLinesData } = chartData;

  const svgHeight = chartNodesData.length * LINE_HEIGHT;

  const chartSvg = createChartSVG(chartId, svgHeight);

  // Add white color to the beginning of the array.
  // Explanation from the D3js documentation (scaleThreshold):
  // "If the number of values in the scale’s domain is n, the number of values in the scale’s range must be n + 1."
  // Any value below domain[0] will be '#fff'.
  const colors = ['#fff', ...CHART_COLORS];
  const getLineColor = d3.scaleThreshold().domain(domain).range(colors);

  const chartWidth = SVG_WIDTH - leftMargin - rightMargin;
  const chartHeight = svgHeight - topMargin - bottomMargin;

  // Create the chart
  const sankeyChart = sankey()
    .size([chartWidth, chartHeight])
    .nodeId(({ nodeId }) => nodeId)
    .nodeWidth(NODE_WIDTH)
    .nodePadding(PADDING_BETWEEN_NODES)
    .nodeSort(null);

  // Constructs a new Sankey generator
  sankeyChart(chartData);

  // Add lines
  chartSvg
    .append('g')
    .attr('class', 'chart-lines')
    .selectAll('.line')
    .data(chartLinesData)
    .enter()
    .append('path')
    .attr(
      'class',
      ({ source: { id: sourceId }, target: { id: targetId } }) =>
        `line source-node-${sourceId} target-node-${targetId}`
    )
    .attr('fill', 'none')
    .attr('d', sankeyLinkHorizontal())
    .style('stroke-width', ({ width }) => (width > 1 ? width : 1))
    .attr('stroke', ({ similarity }) => getLineColor(similarity))
    .on('click', data => handleSearch(data, onSearch))
    .append('title')
    .text(({ source, target }) => getLabel(source, target));

  // Add nodes
  const chartNodes = createChartNodes(chartSvg, chartNodesData);

  // Create the rectangle inside a node
  chartNodes
    .append('rect')
    .attr('class', 'node-rect')
    .attr('width', sankeyChart.nodeWidth())
    .attr('height', ({ y0, y1 }) => calculateYOffset(y0, y1))
    .on('mouseover', setLinesToSelected)
    .on('mouseleave', resetSelectedLines);

  // Create label container
  const labelContainer = chartNodes
    .append('foreignObject')
    .attr('class', ({ nodeId }) => {
      const type = checkType(nodeId, 'earlier') ? 'earlier' : 'later';
      return `node-label ${type}`;
    })
    .attr('width', NODE_LABEL_WIDTH)
    .attr('height', ({ y0, y1 }) => {
      const offset = calculateYOffset(y0, y1);
      return offset > PADDING_BETWEEN_NODES ? offset : PADDING_BETWEEN_NODES;
    })
    .attr('x', ({ nodeId }) =>
      checkType(nodeId, 'earlier') ? -NODE_LABEL_WIDTH - NODE_WIDTH : NODE_WIDTH * 2
    )
    .attr('y', ({ y0, y1 }) => {
      const offset = calculateYOffset(y0, y1);
      const y = offset >= PADDING_BETWEEN_NODES ? 0 : -(PADDING_BETWEEN_NODES - offset) / 2;
      return y;
    });

  // Add div element and label
  labelContainer
    .append('xhtml:div')
    .text(({ label }) => getShortenedTitle(label))
    .on('mouseover', setLinesToSelected)
    .on('mouseleave', resetSelectedLines);

  // Display the full label when hover on title
  labelContainer.append('title').text(({ label }) => label);
};
