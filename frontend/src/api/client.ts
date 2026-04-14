import axios from 'axios';
import { useAuthStore } from '../store/auth.store';

// In production (Netlify), VITE_API_BASE_URL is set to the Render backend URL.
// In local dev, it is undefined and we fall back to '/api' which Vite proxies
// to http://localhost:8000.
const baseURL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : '/api';

const apiClient = axios.create({
  baseURL,
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (window.location.pathname !== '/login') {
        useAuthStore.getState().setUser(null);
        window.location.href = '/login';
      }
    }

    const apiError = error.response?.data?.error;
    if (apiError) {
      return Promise.reject(new Error(apiError));
    }

    return Promise.reject(error);
  }
);

export default apiClient;
