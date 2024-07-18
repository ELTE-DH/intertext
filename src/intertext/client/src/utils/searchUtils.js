import { store } from '../store/store';

const getMatchIds = (query, fileIdsByField) => {
  const values = [];

  Object.keys(fileIdsByField).map(key => {
    const value = key?.toLowerCase();
    const queryString = query?.toLowerCase();
    const isIncludes = value.includes(queryString);

    if (!query?.length || (query?.length && isIncludes)) {
      fileIdsByField[key].map(value => values.push(value));
    }

    return null;
  });

  return values;
};

const getFilteredFileIds = (advancedFilters, fileIdsByField) => {
  const { fileId, title, author } = advancedFilters;
  const { title: fileIdsByTitle, author: fileIdsByAuthor } = fileIdsByField;

  if (fileId) {
    return [parseInt(fileId)];
  }

  const titleMatches = getMatchIds(title, fileIdsByTitle);
  const authorMatches = getMatchIds(author, fileIdsByAuthor);
  const result = titleMatches.filter(match => authorMatches.includes(match));

  return result;
};

export const getFilteredMatchIds = matchIds => {
  const {
    search: {
      data: { fileIdsByField },
      searchParams: { query, field },
      advancedSearchParams: { earlierText, laterText, matchLength, similarity },
    },
  } = store.getState();
  const matchedFileIdsFromQuery = getMatchIds(query, fileIdsByField[field]);

  const queryMatches = matchIds.filter(
    ([, earlierId, laterId]) =>
      matchedFileIdsFromQuery.includes(earlierId) || matchedFileIdsFromQuery.includes(laterId)
  );

  const earlierTextMatches = getFilteredFileIds(earlierText, fileIdsByField);
  const laterTextMatches = getFilteredFileIds(laterText, fileIdsByField);

  const result = queryMatches.filter(item => {
    const [, currentEarlierText, currentLaterText, currentLength, , currentSimilarity] = item;

    const isNotInMatchLengthRange =
      currentLength < matchLength[0] || currentLength > matchLength[1];
    const isNotInSimilarityRange =
      currentSimilarity < similarity[0] || currentSimilarity > similarity[1];
    const isNotInEarlierText = !earlierTextMatches.includes(currentEarlierText);
    const isNotInLaterText = !laterTextMatches.includes(currentLaterText);
    const isSkipItem =
      isNotInMatchLengthRange || isNotInSimilarityRange || isNotInEarlierText || isNotInLaterText;

    if (isSkipItem) {
      return false;
    } else {
      return true;
    }
  });

  return result;
};
