import axios from 'axios';

// Hardcode the production backend URL for Render static deployments
const isDev = import.meta.env.DEV;
const baseURL = isDev ? 'http://127.0.0.1:8000' : 'https://puzzle-vision-backend.onrender.com';

export const api = axios.create({ baseURL });
