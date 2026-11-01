import axios from 'axios';
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api/v1', withCredentials: true });
let accessToken = '';
let company = sessionStorage.getItem('company_id') || '';
export const setToken = (token: string) => { accessToken = token; };
export const setCompany = (id: number) => { company = String(id); sessionStorage.setItem('company_id', company); };
api.interceptors.request.use(config => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  if (company) config.headers['X-Company-ID'] = company;
  return config;
});
let refreshing: Promise<string> | null = null;
api.interceptors.response.use(r => r, async error => {
  const config = error.config;
  if (error.response?.status === 401 && !config._retry && !config.url.startsWith('/auth/')) {
    config._retry = true;
    refreshing ??= api.post('/auth/refresh').then(r => {setToken(r.data.access_token); return r.data.access_token;}).finally(() => {refreshing = null;});
    await refreshing;
    return api(config);
  }
  return Promise.reject(error);
});
export function errorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return 'Something went wrong. Please try again.';
  const detail = error.response?.data?.detail;
  return typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => `${d.loc.slice(1).join('.')}: ${d.msg}`).join('; ') : 'Cannot reach the server. Check the backend connection.';
}
