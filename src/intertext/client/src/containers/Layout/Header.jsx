import { NavLink } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { FormattedMessage } from 'react-intl';
import classNames from 'classnames';

import { changeLanguage } from '../../store/actions/localeAction';

import SelectInput from '../../components/Select/SelectInput';

const APP_NAME = 'INTERTEXT';

const MENU_ITEMS = [
  {
    label: 'Home',
    translationKey: 'home',
    path: '/home',
  },
  {
    label: 'Visualization',
    translationKey: 'visualization',
    path: '/sankey-chart',
  },
  {
    label: 'List',
    translationKey: 'list',
    path: '/list',
  },
  {
    label: 'About',
    translationKey: 'about',
    path: '/about',
  },
];

const Header = () => {
  const { supportedLanguages, currentLanguage } = useSelector(reduxState => reduxState.locale);
  const dispatch = useDispatch();

  const handleLanguageChange = ({ target: { value } }) => {
    dispatch(changeLanguage(value));
  };

  return (
    <header>
      <div className="header-container">
        <NavLink to="/home" className="logo">
          {APP_NAME}
        </NavLink>
        <div className="navbar-container">
          <div className="navbar">
            {MENU_ITEMS.map(({ path, translationKey }) => (
              <NavLink key={path} to={path} className={classNames('menu-item', path.substring(1))}>
                <FormattedMessage id={`header.${translationKey}`} />
              </NavLink>
            ))}
          </div>
          <SelectInput
            value={currentLanguage}
            menuItems={supportedLanguages.map(language => ({
              label: language.toUpperCase(),
              value: language,
            }))}
            className="language-selector"
            handleChange={handleLanguageChange}
          />
        </div>
      </div>
    </header>
  );
};

export default Header;
