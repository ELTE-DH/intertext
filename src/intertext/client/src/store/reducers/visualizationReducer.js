import {
  SET_CURRENT_CARD_DATA,
  SET_CHART_DATA,
  SET_VISUALIZED_BY,
  SET_CLICKED_ELEMENT,
} from '../actions/actionTypes';

const initialState = {
  type: '', // source or target
  title: '',
  file_id: '',
  author: '',
  year: '',
  visualizedBy: 'author',
  matches: [],
  chartData: [],
  xAxisValues: [],
  width: null,
  columnCountsByXAxisValues: {},
  maxColumn: null,
  chartMargin: { top: 0, right: 10, bottom: 100, left: 10 },
  marginBetweenColumns: 20,
  clickedElement: null,
  squareSize: 12,
  squarePerColumn: 10,
  visualizedByFields: {
    author: 'author',
    segment: 'segment_ids',
    year: 'year',
  },
};

const visualizationReducer = (state = initialState, { type, payload }) => {
  switch (type) {
    case SET_VISUALIZED_BY:
      return {
        ...state,
        visualizedBy: payload.visualizedBy,
      };
    case SET_CLICKED_ELEMENT:
      return {
        ...state,
        clickedElement: payload.clickedElement,
      };
    case SET_CURRENT_CARD_DATA:
      return {
        ...state,
        type: payload.type,
        title: payload.title,
        file_id: payload.file_id,
        author: payload.author,
        year: payload.year,
        width: payload.width,
      };
    case SET_CHART_DATA:
      return {
        ...state,
        matches: payload.matches,
        chartData: payload.chartData,
        xAxisValues: payload.xAxisValues,
        visualizedBy: payload.visualizedBy,
        width: payload.width,
        columnCountsByXAxisValues: payload.columnCountsByXAxisValues,
        maxColumn: payload.maxColumn,
      };
    default:
      return state;
  }
};

export default visualizationReducer;
