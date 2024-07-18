import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { Redirect, Route, Switch } from 'react-router-dom';

import { getConfig, getMatchIdsBySort } from '../../rest/resource/resource';
import {
  getSearchResults,
  setFileIdsByField,
  setIsLoading,
  setMatchIdsBySort,
  setMetadata,
} from '../../store/actions/searchAction';

import Cards from '../Cards/Cards';
import SankeyChart from '../SankeyChart/SankeyChart';
import List from '../List/List';
import About from '../About/About';
import Read from '../Read/Read';
import WaffleVisualization from '../WaffleChart/WaffleVisualization';

const Main = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(setIsLoading({ isLoading: true }));
    getConfig()
      .then(({ metadata }) => {
        dispatch(setMetadata(metadata));
        dispatch(setFileIdsByField(metadata));
      })
      .then(() => {
        getMatchIdsBySort('length').then(matchIds => {
          dispatch(setMatchIdsBySort(matchIds));
          dispatch(getSearchResults(matchIds));
        });
      });
  }, []);

  return (
    <main>
      <Switch>
        <Route path="/home" component={Cards} />
        <Route path="/sankey-chart" component={SankeyChart} />
        <Route path="/list" component={List} />
        <Route path="/about" component={About} />
        <Route path="/read/:id" component={Read} />
        <Route path="/waffle-chart/:id" component={WaffleVisualization} />
        <Redirect exact from="/" to="/home" />
        <Redirect to="/home" />
      </Switch>
    </main>
  );
};

export default Main;
