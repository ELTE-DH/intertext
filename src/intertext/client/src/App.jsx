import { Provider } from 'react-redux';
import { ConnectedRouter } from 'connected-react-router';

import { history, store } from './store/store';

import Header from './containers/Layout/Header';
import Main from './containers/Layout/Main';
import TranslationProvider from './containers/TranslationProvider/TranslationProvider';

const App = () => (
  <Provider store={store}>
    <TranslationProvider>
      <ConnectedRouter history={history}>
        <Header />
        <Main />
      </ConnectedRouter>
    </TranslationProvider>
  </Provider>
);

export default App;
