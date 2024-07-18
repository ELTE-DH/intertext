import { FormattedMessage } from 'react-intl';

const NoResults = () => (
  <div className="no-results-message">
    <FormattedMessage id="results.noMatches" />
  </div>
);

export default NoResults;
