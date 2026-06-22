import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Anexa o token JWT em toda requisição, se existir
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('mediary_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Se o token expirar/for inválido, limpa e força novo login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('mediary_token');
    }
    return Promise.reject(error);
  }
);

export default api;
