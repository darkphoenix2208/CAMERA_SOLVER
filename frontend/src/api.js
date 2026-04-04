import axios from 'axios';

/** Dev: proxied via Vite to backend. Prod: set VITE_API_BASE (e.g. http://127.0.0.1:8000). */
const baseURL =
  import.meta.env.VITE_API_BASE ??
  (import.meta.env.DEV ? '/api' : 'http://127.0.0.1:8000');

export const api = axios.create({ baseURL });
