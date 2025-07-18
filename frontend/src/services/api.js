import axios from 'axios';

// Define the base URL for the API. 
// You might want to make this configurable based on environment (dev/prod)
const API_URL = 'https://partsapi.kyro.dog/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    // You can add other default headers here, like Authorization for JWT tokens
  },
});

// Optional: Interceptor to add JWT token to requests
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken'); // Or however you store your token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

export default apiClient;
