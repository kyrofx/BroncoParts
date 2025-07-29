import axios from 'axios';
import api from '../api';

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    interceptors: {
      request: {
        use: jest.fn()
      },
      response: {
        use: jest.fn()
      }
    },
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn()
  }))
}));

describe('API Service', () => {
  let mockAxiosInstance;

  beforeEach(() => {
    mockAxiosInstance = axios.create();
    localStorage.clear();
  });

  test('creates axios instance with correct base URL', () => {
    expect(axios.create).toHaveBeenCalledWith({
      baseURL: 'http://localhost:8000/api'
    });
  });

  test('sets up request interceptor', () => {
    expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
  });

  test('request interceptor adds authorization header when token exists', () => {
    const token = 'test-token';
    localStorage.setItem('token', token);
    
    // Get the interceptor function
    const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    
    const config = { headers: {} };
    const result = requestInterceptor(config);
    
    expect(result.headers.Authorization).toBe(`Bearer ${token}`);
  });

  test('request interceptor does not add authorization header when no token', () => {
    // Ensure no token in localStorage
    localStorage.removeItem('token');
    
    const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    
    const config = { headers: {} };
    const result = requestInterceptor(config);
    
    expect(result.headers.Authorization).toBeUndefined();
  });

  test('request interceptor preserves existing headers', () => {
    const token = 'test-token';
    localStorage.setItem('token', token);
    
    const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    
    const config = { 
      headers: { 
        'Content-Type': 'application/json',
        'Custom-Header': 'custom-value'
      } 
    };
    const result = requestInterceptor(config);
    
    expect(result.headers.Authorization).toBe(`Bearer ${token}`);
    expect(result.headers['Content-Type']).toBe('application/json');
    expect(result.headers['Custom-Header']).toBe('custom-value');
  });

  test('request interceptor handles missing headers object', () => {
    const token = 'test-token';
    localStorage.setItem('token', token);
    
    const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    
    const config = {}; // No headers property
    const result = requestInterceptor(config);
    
    expect(result.headers).toBeDefined();
    expect(result.headers.Authorization).toBe(`Bearer ${token}`);
  });

  test('exports the axios instance', () => {
    expect(api).toBe(mockAxiosInstance);
  });

  test('handles localStorage errors gracefully', () => {
    // Mock localStorage to throw errors
    const originalGetItem = localStorage.getItem;
    localStorage.getItem = jest.fn(() => {
      throw new Error('localStorage not available');
    });
    
    try {
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      
      const config = { headers: {} };
      const result = requestInterceptor(config);
      
      // Should not add authorization header if localStorage fails
      expect(result.headers.Authorization).toBeUndefined();
      
    } finally {
      localStorage.getItem = originalGetItem;
    }
  });

  test('handles empty token gracefully', () => {
    localStorage.setItem('token', '');
    
    const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    
    const config = { headers: {} };
    const result = requestInterceptor(config);
    
    // Should not add authorization header for empty token
    expect(result.headers.Authorization).toBeUndefined();
  });

  test('handles null token gracefully', () => {
    localStorage.setItem('token', 'null');
    
    const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    
    const config = { headers: {} };
    const result = requestInterceptor(config);
    
    // Should add authorization header even for string 'null'
    expect(result.headers.Authorization).toBe('Bearer null');
  });
});