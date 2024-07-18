import { api } from '../rest';

const getJSONFile = ({ path, path2 }) =>
  api.get(`/${path}/${path2}.json`).then(response => response.data);

const getMatchIdsBySort = filterName =>
  getJSONFile({ path: 'indices', path2: `match-ids-by-${filterName}` });

const getMatchFile = matchFileId => getJSONFile({ path: 'matches', path2: matchFileId.toString() });

const getFilesFromMatches = matchFileIds =>
  Promise.all(matchFileIds.map(matchFileId => getMatchFile(matchFileId)));

const getTextFromJSON = fileId => getJSONFile({ path: 'texts', path2: fileId.toString() });

const getConfig = () => api.get('/config.json').then(response => response.data);

const getAboutPageContent = currentLanguage =>
  api.get(`/about/about_${currentLanguage.toUpperCase()}.html`).then(response => response.data);

export {
  getMatchIdsBySort,
  getMatchFile,
  getFilesFromMatches,
  getTextFromJSON,
  getConfig,
  getAboutPageContent,
};
