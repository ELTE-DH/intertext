import { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import { Card } from '@mui/material';

import { getMatchIdsBySort } from '../../rest/resource/resource';
import { setClickedElement, setCurrentCardData } from '../../store/actions/visualizationAction';
import { getSearchResults, setMatchIdsBySort } from '../../store/actions/searchAction';

import AdvancedSearch from '../AdvancedSearch/AdvancedSearch';
import SearchBar from '../SearchBar/SearchBar';
import Results from '../Results/Results';
import LoadingIndicator from '../../components/LoadingIndicator/LoadingIndicator';

const sortByOptions = [
  { label: 'Length', value: 'length', translationKey: 'length' },
  { label: 'Similarity', value: 'similarity', translationKey: 'similarity' },
  { label: 'Author', value: 'author', translationKey: 'author' },
  { label: 'Title', value: 'title', translationKey: 'title' },
  { label: 'Date', value: 'year', translationKey: 'date' },
];

const cardDataDefaultValues = {
  type: '',
  title: '',
  file_id: '',
  author: '',
  year: '',
};

const Cards = () => {
  const [sortBy, setSortBy] = useState(sortByOptions[0].value);
  const {
    data: { largestMatchLength },
    results: { totalResults },
    isLoading,
  } = useSelector(reduxState => reduxState.search);
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(setCurrentCardData(cardDataDefaultValues));
  }, []);

  const handleSortByChange = ({ target: { value } }) => {
    setSortBy(value);
    getMatchIdsBySort(value).then(response => {
      dispatch(setMatchIdsBySort(response));
      dispatch(getSearchResults(response));
    });
    dispatch(setClickedElement({ clickedElement: null }));
  };

  return largestMatchLength !== null && totalResults !== null ? (
    <div className="cards-page">
      <div className="content-left">
        <Card className="results-number-card">
          <div>
            <FormattedMessage id="results.title" /> ({totalResults})
          </div>
        </Card>
        <AdvancedSearch largestMatchLength={largestMatchLength} />
      </div>
      <div className="content-right">
        <SearchBar
          sortByOptions={sortByOptions}
          sortByValue={sortBy}
          handleSortByChange={handleSortByChange}
        />
        {isLoading ? <LoadingIndicator /> : <Results />}
      </div>
    </div>
  ) : (
    <LoadingIndicator />
  );
};

export default Cards;
