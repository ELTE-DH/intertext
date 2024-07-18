import axios from 'axios';

const baseUrl = '/api';

const newInstance = url => axios.create({ baseURL: url });

const api = newInstance(baseUrl);

export { api };
