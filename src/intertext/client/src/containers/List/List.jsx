import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useHistory } from 'react-router-dom';
import { Card } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

import { getConfig } from '../../rest/resource/resource';
import {
  getSearchResults,
  setIsLoading,
  setMetadata,
  setSearchField,
  setSearchQuery,
} from '../../store/actions/searchAction';

const List = () => {
  const {
    data: { matchIds },
    metadata,
  } = useSelector(reduxState => reduxState.search);
  const dispatch = useDispatch();
  const history = useHistory();

  useEffect(() => {
    if (!metadata.length) {
      getConfig().then(data => {
        dispatch(setMetadata(data.metadata));
      });
    }
  }, [metadata]);

  const handleSearch = title => {
    dispatch(setSearchQuery(title));
    dispatch(setSearchField('title'));
    dispatch(setIsLoading({ isLoading: true }));
    dispatch(getSearchResults(matchIds));
    history.push('/home');
  };

  return (
    <div className="list-page">
      {metadata.map(({ author, title, year, matches }) => (
        <Card className="list-card">
          <div className="list-info-container">
            <div className="author">
              {author}, {year}
            </div>
            <div className="title">{title}</div>
          </div>
          {matches && <SearchIcon className="search-icon" onClick={() => handleSearch(title)} />}
        </Card>
      ))}
    </div>
  );
};

export default List;
