import apiClient from '../api/client';
import { ApiResponse, User } from '../types/auth.types';

export const authService = {
  async login(email: string, password: string): Promise<User> {
    const response = await apiClient.post<ApiResponse<User>>('/auth/login', {
      email,
      password,
    });
    return response.data.data;
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
  },

  async me(): Promise<User> {
    const response = await apiClient.get<ApiResponse<User>>('/auth/me');
    return response.data.data;
  },
};
