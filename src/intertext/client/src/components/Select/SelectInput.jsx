import { FormattedMessage } from 'react-intl';
import { FormControl, MenuItem, Select } from '@mui/material';

const SelectInput = ({ title, value, menuItems, className, handleChange }) => (
  <div className={className}>
    {title && <div className="title">{title}</div>}
    <FormControl size="small">
      <Select value={value} onChange={handleChange}>
        {menuItems.map(({ label, value, translationKey }) => (
          <MenuItem key={value} value={value}>
            {translationKey ? <FormattedMessage id={`selectItem.${translationKey}`} /> : label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  </div>
);

export default SelectInput;
