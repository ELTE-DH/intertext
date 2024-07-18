import { useDispatch } from 'react-redux';
import { Autocomplete, TextField } from '@mui/material';

import { setSearchQuery } from '../../store/actions/searchAction';

const AutocompleteInput = ({ options, value, handleChange }) => {
  const dispatch = useDispatch();

  const handleSearchStringChange = (_, newValue) => {
    handleChange(newValue);
    dispatch(setSearchQuery(newValue));
  };

  return (
    <Autocomplete
      disablePortal
      size="small"
      value={value}
      options={options}
      renderInput={params => <TextField {...params} />}
      className="autocomplete-input"
      onChange={handleSearchStringChange}
    />
  );
};

export default AutocompleteInput;
