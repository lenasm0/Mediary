import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

const api = axios.create({
  baseURL: "https://mediaryapp.onrender.com/api",
  withCredentials: true,

  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;