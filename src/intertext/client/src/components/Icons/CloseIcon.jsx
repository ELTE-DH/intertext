import { IconButton } from '@mui/material';
import { Close } from '@mui/icons-material';

const ClearIcon = ({ onClick }) => (
  <IconButton size="small">
    <Close fontSize="small" className="close-icon" onClick={onClick} />
  </IconButton>
);

export default ClearIcon;
