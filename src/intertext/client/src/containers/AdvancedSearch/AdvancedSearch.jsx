import { useEffect, useMemo, useState } from 'react';
import { FormattedMessage, useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import { Button, Card, CardActions, CardContent, Slider, TextField } from '@mui/material';
import classNames from 'classnames';

import { getSearchResults, setFilters } from '../../store/actions/searchAction';

import ClearIcon from '../../components/Icons/ClearIcon';

const textFilters = [
  { fieldName: 'earlierText', className: 'earlier-text' },
  { fieldName: 'laterText', className: 'later-text' },
];

const AdvancedSearch = ({ largestMatchLength }) => {
  const defaultValues = useMemo(
    () => ({
      matchLength: [1, largestMatchLength],
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
    }),
    [largestMatchLength]
  );

  const [advancedSearch, setAdvancedSearch] = useState(defaultValues);
  const {
    data: { matchIds },
    advancedSearchParams,
  } = useSelector(reduxState => reduxState.search);
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  useEffect(() => {
    if (!Object.keys(advancedSearchParams).length) {
      dispatch(setFilters(defaultValues));
    } else {
      setAdvancedSearch(advancedSearchParams);
    }
  }, []);

  const handleSliderChange = (field, newValue) => {
    setAdvancedSearch({ ...advancedSearch, [field]: newValue });
  };

  const handleTextFieldChange = (fieldName, field, value) => {
    setAdvancedSearch({
      ...advancedSearch,
      [fieldName]: { ...advancedSearch[fieldName], [field]: value },
    });
  };

  const handleApplyFilters = () => {
    dispatch(setFilters(advancedSearch));
    dispatch(getSearchResults(matchIds));
  };

  const handleClearFilters = () => {
    setAdvancedSearch(defaultValues);
  };

  const handleClearTextFiltersByField = fieldName => {
    setAdvancedSearch({ ...advancedSearch, [fieldName]: defaultValues[fieldName] });
  };

  const sliders = [
    {
      translationKey: 'matchLength',
      className: 'match-length',
      min: defaultValues.matchLength[0],
      max: defaultValues.matchLength[1],
      value: advancedSearch.matchLength,
      onChange: (_, newValue) => handleSliderChange('matchLength', newValue),
    },
    {
      translationKey: 'similarity',
      className: 'similarity',
      min: defaultValues.similarity[0],
      max: defaultValues.similarity[1],
      value: advancedSearch.similarity,
      onChange: (_, newValue) => handleSliderChange('similarity', newValue),
    },
  ];

  return (
    <Card className="advanced-search">
      <div className="title">
        <FormattedMessage id="advancedSearch.title" />
      </div>
      <CardContent>
        <div className="filter-container">
          {sliders.map(({ className, translationKey, min, max, value, onChange }) => (
            <div key={className} className={className}>
              <div>
                <FormattedMessage id={`advancedSearch.${translationKey}`} />
              </div>
              <div className="slider-container">
                <Slider
                  min={min}
                  max={max}
                  value={value}
                  onChange={onChange}
                  valueLabelDisplay="auto"
                  size="small"
                />
              </div>
            </div>
          ))}
        </div>
        {textFilters.map(({ fieldName, className }) => (
          <>
            <div key={className}>
              <div className={classNames('filter-container', className)}>
                <div className="label">
                  <div>
                    <FormattedMessage id={`advancedSearch.${fieldName}`} />
                  </div>
                  <div title={formatMessage({ id: 'popupTexts.clear' })}>
                    <ClearIcon onClick={() => handleClearTextFiltersByField(fieldName)} />
                  </div>
                </div>
                <div className="text-field-container">
                  <TextField
                    label={<FormattedMessage id="placeholders.author" />}
                    variant="outlined"
                    size="small"
                    value={advancedSearch[fieldName].author}
                    onChange={event =>
                      handleTextFieldChange(fieldName, 'author', event.target.value)
                    }
                  />
                  <TextField
                    label={<FormattedMessage id="placeholders.title" />}
                    variant="outlined"
                    size="small"
                    value={advancedSearch[fieldName].title}
                    onChange={event =>
                      handleTextFieldChange(fieldName, 'title', event.target.value)
                    }
                  />
                  <TextField
                    label={<FormattedMessage id="placeholders.fileId" />}
                    variant="outlined"
                    size="small"
                    type="number"
                    value={advancedSearch[fieldName].fileId}
                    onChange={event =>
                      handleTextFieldChange(fieldName, 'fileId', event.target.value)
                    }
                  />
                </div>
              </div>
            </div>
          </>
        ))}
      </CardContent>
      <CardActions>
        <Button variant="contained" onClick={handleClearFilters}>
          <FormattedMessage id="buttons.clearAll" />
        </Button>
        <Button variant="contained" onClick={handleApplyFilters}>
          <FormattedMessage id="buttons.apply" />
        </Button>
      </CardActions>
    </Card>
  );
};

export default AdvancedSearch;
