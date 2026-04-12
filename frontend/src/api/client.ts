import axios from 'axios';
import { useAuthStore } from '../store/auth.store';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
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
