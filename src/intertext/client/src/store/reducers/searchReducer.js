import {
  SET_RESULTS,
  SET_FILE_IDS_BY_FIELD,
  SET_AUTOCOMPLETE_DROPDOWN_OPTIONS,
  SET_SEARCH_FIELD,
  SET_SEARCH_QUERY,
  SET_MATCH_IDS_BY_SORT,
  SET_ADVANCED_SEARCH,
  SET_IS_LOADING,
  SET_METADATA,
} from '../actions/actionTypes';

const initialState = {
  metadata: [],
  data: {
    matchIds: [],
    largestMatchLength: null,
    fileIdsByField: {},
    autocompleteOptions: [],
  },
  results: {
    displayedResults: [],
    totalResults: null,
  },
  searchParams: {
    query: null,
    field: 'title',
  },
  advancedSearchParams: {
    matchLength: [1, 100],
    similarity: [1, 100],
    earlierText: {
      author: '',
      title: '',
      fileId: '',
    },
    laterText: {
      author: '',
      title: '',
      fileId: '',
    },
  },
  pagination: {
    currentPage: 1,
    resultsPerPage: 15,
    totalPage: 0,
  },
  isLoading: false,
};

const searchReducer = (state = initialState, { type, payload }) => {
  switch (type) {
    case SET_IS_LOADING:
      return { ...state, isLoading: payload.isLoading };
    case SET_SEARCH_QUERY:
      return { ...state, searchParams: { ...state.searchParams, query: payload.query } };
    case SET_SEARCH_FIELD:
      return { ...state, searchParams: { ...state.searchParams, field: payload.field } };
    case SET_MATCH_IDS_BY_SORT:
      const lengths = payload.matchIds.map(match => match[3]);
      const largestMatchLength = Math.max(...lengths);
      return {
        ...state,
        data: {
          ...state.data,
          matchIds: payload.matchIds,
          largestMatchLength,
        },
        advancedSearchParams: {
          ...state.advancedSearchParams,
          matchLength: [1, largestMatchLength],
        },
      };
    case SET_ADVANCED_SEARCH:
      return { ...state, advancedSearchParams: payload.advancedSearchParams };
    case SET_METADATA:
      return { ...state, metadata: payload.metadata };
    case SET_RESULTS:
      const totalPage = Math.ceil(payload.totalResults / state.pagination.resultsPerPage);
      return {
        ...state,
        results: {
          ...state.results,
          displayedResults: payload.displayedResults,
          totalResults: payload.totalResults,
        },
        pagination: { ...state.pagination, currentPage: payload.currentPage, totalPage },
        isLoading: false,
      };
    case SET_AUTOCOMPLETE_DROPDOWN_OPTIONS:
      return {
        ...state,
        data: {
          ...state.data,
          autocompleteOptions: Object.keys(state.data.fileIdsByField[payload.field]),
        },
      };
    case SET_FILE_IDS_BY_FIELD:
      const fileIds = {
        author: {},
        title: {},
      };

      payload.metadata.forEach(({ id, author, title }) => {
        fileIds.author[author] = author in fileIds.author ? [...fileIds.author[author], id] : [id];
        fileIds.title[title] = title in fileIds.title ? [...fileIds.title[title], id] : [id];
      });

      const autocompleteOptions = Object.keys(fileIds[state.searchParams.field]);

      return {
        ...state,
        data: { ...state.data, fileIdsByField: fileIds, autocompleteOptions },
      };
    default:
      return state;
  }
};

export default searchReducer;
