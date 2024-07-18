import { useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import { Button, Divider } from '@mui/material';

import {
  setAutocompleteDropdownOptions,
  setSearchField,
  setIsLoading,
  getSearchResults,
} from '../../store/actions/searchAction';

import SelectInput from '../../components/Select/SelectInput';
import AutocompleteInput from '../../components/Autocomplete/AutocompleteInput';
import SubheaderCard from '../../components/SubheaderCard/SubheaderCard';

const searchByOptions = [
  { label: 'Author', value: 'author', translationKey: 'author' },
  { label: 'Title', value: 'title', translationKey: 'title' },
];

const SearchBar = ({ sortByOptions, sortByValue, handleSortByChange }) => {
  const [searchBy, setSearchBy] = useState(searchByOptions[1].value);
  const {
    data: { matchIds, autocompleteOptions },
    results: { totalResults },
    searchParams,
  } = useSelector(reduxState => reduxState.search);
  const [autocompleteValue, setAutocompleteValue] = useState(searchParams.query);
  const dispatch = useDispatch();

  const handleSearchByChange = ({ target: { value } }) => {
    setSearchBy(value);
    dispatch(setSearchField(value));
    dispatch(setAutocompleteDropdownOptions(value));
  };

  const handleSearch = () => {
    dispatch(setIsLoading({ isLoading: true }));
    dispatch(getSearchResults(matchIds));
  };

  return (
    <SubheaderCard className="search-bar">
      <div className="results-number">
        <FormattedMessage id="searchBar.results" /> ({totalResults})
      </div>
      <Divider orientation="vertical" className="results-number-divider" />
      <div className="search">
        <div className="search-input-container">
          <SelectInput
            title={<FormattedMessage id="searchBar.searchBy" />}
            value={searchBy}
            menuItems={searchByOptions}
            className="search-by"
            handleChange={handleSearchByChange}
          />
          <AutocompleteInput
            options={autocompleteOptions}
            value={autocompleteValue}
            handleChange={setAutocompleteValue}
          />
        </div>
        <Button variant="contained" className="search-button" onClick={handleSearch}>
          <FormattedMessage id="buttons.search" />
        </Button>
      </div>
      <Divider orientation="vertical" />
      <div className="sort-container">
        <SelectInput
          title={<FormattedMessage id="searchBar.sortBy" />}
          value={sortByValue}
          menuItems={sortByOptions}
          className="sort-by"
          handleChange={handleSortByChange}
        />
      </div>
    </SubheaderCard>
  );
};

export default SearchBar;
