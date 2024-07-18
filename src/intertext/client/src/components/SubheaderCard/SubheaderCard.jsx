import { Card } from '@mui/material';
import classNames from 'classnames';

const SubheaderCard = ({ className, children }) => (
  <Card className={classNames('subheader-card', className)}>{children}</Card>
);

export default SubheaderCard;
