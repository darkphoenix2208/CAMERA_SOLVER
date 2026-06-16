import axios from 'axios';

let baseURL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
if (baseURL && !baseURL.startsWith('http')) {
    baseURL = `https://${baseURL}`;
}

export const api = axios.create({ baseURL });
