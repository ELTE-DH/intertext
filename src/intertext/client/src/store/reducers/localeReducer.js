import { CHANGE_LANGUAGE } from '../actions/actionTypes';

const initialState = {
  supportedLanguages: ['en', 'hu'],
  currentLanguage: 'en',
};

const localeReducer = (state = initialState, { type, payload }) => {
  switch (type) {
    case CHANGE_LANGUAGE:
      return { ...state, currentLanguage: payload.currentLanguage };
    default:
      return state;
  }
};

export default localeReducer;
