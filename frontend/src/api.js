import axios from 'axios';

// Hugging Face Space backend URL
const isDev = import.meta.env.DEV;
const baseURL = isDev ? 'http://127.0.0.1:8000' : 'https://darkphoenix2208-camerasolver.hf.space';

export const api = axios.create({ baseURL });
