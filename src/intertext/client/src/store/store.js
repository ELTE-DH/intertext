import { applyMiddleware, combineReducers, createStore } from 'redux';
import { composeWithDevTools } from '@redux-devtools/extension';
import { createHashHistory } from 'history';
import { routerMiddleware, connectRouter } from 'connected-react-router';
import thunkMiddleware from 'redux-thunk';

import searchReducer from './reducers/searchReducer';
import visualizationReducer from './reducers/visualizationReducer';
import localeReducer from './reducers/localeReducer';

const history = createHashHistory();

const rootReducer = combineReducers({
  search: searchReducer,
  visualization: visualizationReducer,
  locale: localeReducer,
  router: connectRouter(history),
});

let middlewares = [thunkMiddleware, routerMiddleware(history)];

const store = createStore(
  connectRouter(history)(rootReducer),
  composeWithDevTools(applyMiddleware(...middlewares))
);

export { store, history };
