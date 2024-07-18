import { CHANGE_LANGUAGE } from './actionTypes';

export const changeLanguage = currentLanguage => ({
  type: CHANGE_LANGUAGE,
  payload: { currentLanguage },
});
