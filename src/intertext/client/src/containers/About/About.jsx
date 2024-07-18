import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { FormattedMessage } from 'react-intl';
import { Card } from '@mui/material';

import { getAboutPageContent } from '../../rest/resource/resource';

import SubheaderCard from '../../components/SubheaderCard/SubheaderCard';
import LoadingIndicator from '../../components/LoadingIndicator/LoadingIndicator';

const FALLBACK_LANGUAGE = 'en';

const About = () => {
  const [pageContent, setPageContent] = useState();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const { currentLanguage } = useSelector(reduxState => reduxState.locale);

  useEffect(() => {
    getAboutPageContent(currentLanguage)
      .then(data => {
        setPageContent(data);
      })
      .catch(() => {
        getAboutPageContent(FALLBACK_LANGUAGE)
          .then(data => {
            setPageContent(data);
          })
          .catch(() => {
            setError(true);
          });
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [currentLanguage]);

  return (
    <div className="about-page content-page">
      <SubheaderCard>
        <span>
          <FormattedMessage id="about.title" />
        </span>
      </SubheaderCard>
      <Card className="about-card">
        {isLoading && <LoadingIndicator />}
        {!isLoading && pageContent && (
          <div dangerouslySetInnerHTML={{ __html: pageContent }} className="content" />
        )}
        {!isLoading && error && (
          <div className="error-message">
            <FormattedMessage id="about.errorMessage" />
          </div>
        )}
      </Card>
    </div>
  );
};

export default About;
