import { IconButton } from '@mui/material';
import { Replay as Clear } from '@mui/icons-material';

const ClearIcon = ({ onClick }) => (
  <IconButton size="small">
    <Clear fontSize="small" className="clear-icon" onClick={onClick} />
  </IconButton>
);

export default ClearIcon;
