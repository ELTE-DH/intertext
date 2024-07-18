import { getFilesFromMatches } from '../../rest/resource/resource';
import { getFilteredMatchIds } from '../../utils/searchUtils';
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
} from './actionTypes';

export const setResults = payload => ({
  type: SET_RESULTS,
  payload,
});

export const getSearchResults = (matchIds, page) => (dispatch, getState) => {
  const {
    search: {
      data: { fileIdsByField },
      pagination: { resultsPerPage },
    },
  } = getState();

  if (!Object.keys(fileIdsByField).length) return;

  const currentPage = page || 1;
  const filteredMatchIds = getFilteredMatchIds(matchIds);
  const slicedMatchedIds = filteredMatchIds.slice(0, resultsPerPage * currentPage);
  const sourceFileIds = slicedMatchedIds.map(d => d[1]);
  const uniqueSourceFileIds = [...new Set(sourceFileIds)];

  getFilesFromMatches(uniqueSourceFileIds).then(matchFiles => {
    const displayedResults = slicedMatchedIds.reduce((results, [matchIndex, matchFileId]) => {
      const matchFileIndexInMatchIds = uniqueSourceFileIds.indexOf(matchFileId);
      const result = matchFiles[matchFileIndexInMatchIds][matchIndex];
      results.push(result);
      return results;
    }, []);

    dispatch(setResults({ displayedResults, totalResults: filteredMatchIds.length, currentPage }));
  });
};

export const setIsLoading = payload => ({
  type: SET_IS_LOADING,
  payload,
});

export const setMetadata = metadata => ({
  type: SET_METADATA,
  payload: { metadata },
});

export const setFileIdsByField = metadata => ({
  type: SET_FILE_IDS_BY_FIELD,
  payload: { metadata },
});

export const setAutocompleteDropdownOptions = field => ({
  type: SET_AUTOCOMPLETE_DROPDOWN_OPTIONS,
  payload: { field },
});

export const setSearchField = field => ({
  type: SET_SEARCH_FIELD,
  payload: { field },
});

export const setSearchQuery = query => ({
  type: SET_SEARCH_QUERY,
  payload: { query },
});

export const setMatchIdsBySort = matchIds => ({
  type: SET_MATCH_IDS_BY_SORT,
  payload: { matchIds },
});

export const setFilters = advancedSearchParams => ({
  type: SET_ADVANCED_SEARCH,
  payload: { advancedSearchParams },
});
