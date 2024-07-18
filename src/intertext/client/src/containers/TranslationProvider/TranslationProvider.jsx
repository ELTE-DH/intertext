import { useSelector } from 'react-redux';
import { IntlProvider } from 'react-intl';

import EnTranslations from '../../assets/locale/en.json';
import HuTranslations from '../../assets/locale/hu.json';

const translations = {
  en: EnTranslations,
  hu: HuTranslations,
};

const TranslationProvider = ({ children }) => {
  const { currentLanguage } = useSelector(reduxState => reduxState.locale);

  return (
    <IntlProvider locale={currentLanguage} messages={translations[currentLanguage]}>
      {children}
    </IntlProvider>
  );
};

export default TranslationProvider;
