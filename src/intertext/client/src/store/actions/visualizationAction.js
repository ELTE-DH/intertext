import { getMatchFile } from '../../rest/resource/resource';
import {
  SET_CURRENT_CARD_DATA,
  SET_CHART_DATA,
  SET_VISUALIZED_BY,
  SET_CLICKED_ELEMENT,
} from './actionTypes';

export const setCurrentCardData = payload => ({
  type: SET_CURRENT_CARD_DATA,
  payload,
});

export const setChartData = payload => ({
  type: SET_CHART_DATA,
  payload,
});

export const setVisualizedBy = payload => ({
  type: SET_VISUALIZED_BY,
  payload,
});

export const setClickedElement = payload => ({
  type: SET_CLICKED_ELEMENT,
  payload,
});

export const getClickedElement = id => (dispatch, getState) => {
  const {
    visualization: { matches },
  } = getState();

  dispatch(setClickedElement({ clickedElement: matches.find(match => match._id === id) }));
};

export const getChartData = () => (dispatch, getState) => {
  const {
    visualization: {
      file_id: fileId,
      visualizedBy,
      visualizedByFields,
      squarePerColumn,
      squareSize,
      marginBetweenColumns,
      chartMargin: { right: rightMargin, left: leftMargin },
    },
  } = getState();

  return getMatchFile(fileId).then(matches => {
    const chartData = [];
    let matchCountsByXAxisValues = {};
    let columnCountsByXAxisValues = {};

    matches.map(match => {
      const { _id, target_file_id, similarity } = match;

      const isTargetFile = fileId === target_file_id;
      const propertyName = isTargetFile
        ? `source_${visualizedByFields[visualizedBy]}`
        : `target_${visualizedByFields[visualizedBy]}`;
      const currentXAxisValue = match[propertyName];

      let matchCount = 0;
      let columnCount = 1;

      if (matchCountsByXAxisValues[currentXAxisValue] >= 0) {
        matchCount = matchCountsByXAxisValues[currentXAxisValue] + 1;
      }

      matchCountsByXAxisValues[currentXAxisValue] = matchCount;

      const columnIndex = Math.floor(matchCountsByXAxisValues[currentXAxisValue] / squarePerColumn);

      if (columnCountsByXAxisValues[currentXAxisValue]) {
        columnCount = Math.max(columnCountsByXAxisValues[currentXAxisValue], columnIndex + 1);
      }

      columnCountsByXAxisValues[currentXAxisValue] = columnCount;

      const dataObject = {
        id: _id,
        x: currentXAxisValue.toString(),
        row: matchCountsByXAxisValues[currentXAxisValue] % squarePerColumn,
        column: columnIndex,
        similarity,
      };

      chartData.push(dataObject);
      return null;
    });

    const xAxisValues = Object.keys(columnCountsByXAxisValues);
    const largestColumn = Math.max(...Object.values(columnCountsByXAxisValues));
    const largestColumnLabel = xAxisValues.find(
      key => columnCountsByXAxisValues[key] === largestColumn
    );

    let chartWidth =
      xAxisValues.length *
        (columnCountsByXAxisValues[largestColumnLabel] * squareSize + marginBetweenColumns) +
      rightMargin +
      leftMargin;

    dispatch(
      setChartData({
        matches,
        chartData,
        xAxisValues,
        visualizedBy,
        width: chartWidth,
        columnCountsByXAxisValues,
        maxColumn: columnCountsByXAxisValues[largestColumnLabel],
      })
    );
  });
};
