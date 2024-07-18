import { Divider } from '@mui/material';
import { BubbleChart as BubbleIcon } from '@mui/icons-material';

const CustomDivider = ({ withIcon, orientation, variant }) => (
  <Divider orientation={orientation} variant={variant} flexItem>
    {withIcon && <BubbleIcon />}
  </Divider>
);

export default CustomDivider;
