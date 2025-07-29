import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import * as api from '../api';

// Mock the API
jest.mock('../api');
const mockApi = api;

// Test component to access auth context
const TestComponent = () => {
  const { user, login, logout, loading } = useAuth();
  
  return (
    <div>
      <div data-testid="user">{user ? user.username : 'Not logged in'}</div>
      <div data-testid="loading">{loading ? 'Loading' : 'Not loading'}</div>
      <button 
        data-testid="login-btn" 
        onClick={() => login('test@example.com', 'password')}
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
    </div>
  );
};

const renderWithAuth = () => {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  test('provides initial state when not authenticated', () => {
    renderWithAuth();
    
    expect(screen.getByTestId('user')).toHaveTextContent('Not logged in');
    expect(screen.getByTestId('loading')).toHaveTextContent('Not loading');
  });

  test('loads user from localStorage on mount', () => {
    const mockUser = { 
      id: 1, 
      username: 'testuser', 
      email: 'test@example.com',
      permission: 'editor'
    };
    const mockToken = 'mock-token';
    
    localStorage.setItem('user', JSON.stringify(mockUser));
    localStorage.setItem('token', mockToken);
    
    renderWithAuth();
    
    expect(screen.getByTestId('user')).toHaveTextContent('testuser');
  });

  test('handles successful login', async () => {
    const mockResponse = {
      user: { 
        id: 1, 
        username: 'testuser', 
        email: 'test@example.com',
        permission: 'editor'
      },
      access_token: 'new-token'
    };
    
    mockApi.post.mockResolvedValueOnce({ data: mockResponse });
    
    renderWithAuth();
    
    fireEvent.click(screen.getByTestId('login-btn'));
    
    // Should show loading during login
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading');
    
    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
      expect(screen.getByTestId('loading')).toHaveTextContent('Not loading');
    });
    
    // Should store in localStorage
    expect(localStorage.getItem('user')).toBe(JSON.stringify(mockResponse.user));
    expect(localStorage.getItem('token')).toBe(mockResponse.access_token);
  });

  test('handles login failure', async () => {
    const mockError = {
      response: {
        data: { message: 'Invalid credentials' }
      }
    };
    
    mockApi.post.mockRejectedValueOnce(mockError);
    
    // Mock console.error to avoid test output noise
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    renderWithAuth();
    
    fireEvent.click(screen.getByTestId('login-btn'));
    
    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('Not logged in');
      expect(screen.getByTestId('loading')).toHaveTextContent('Not loading');
    });
    
    // Should not store anything in localStorage
    expect(localStorage.getItem('user')).toBeNull();
    expect(localStorage.getItem('token')).toBeNull();
    
    consoleSpy.mockRestore();
  });

  test('handles logout', () => {
    // Set up initial authenticated state
    const mockUser = { 
      id: 1, 
      username: 'testuser', 
      email: 'test@example.com',
      permission: 'editor'
    };
    localStorage.setItem('user', JSON.stringify(mockUser));
    localStorage.setItem('token', 'mock-token');
    
    renderWithAuth();
    
    // Should be logged in initially
    expect(screen.getByTestId('user')).toHaveTextContent('testuser');
    
    fireEvent.click(screen.getByTestId('logout-btn'));
    
    // Should clear user state
    expect(screen.getByTestId('user')).toHaveTextContent('Not logged in');
    
    // Should clear localStorage
    expect(localStorage.getItem('user')).toBeNull();
    expect(localStorage.getItem('token')).toBeNull();
  });

  test('handles network error during login', async () => {
    mockApi.post.mockRejectedValueOnce(new Error('Network error'));
    
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    renderWithAuth();
    
    fireEvent.click(screen.getByTestId('login-btn'));
    
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not loading');
    });
    
    expect(screen.getByTestId('user')).toHaveTextContent('Not logged in');
    
    consoleSpy.mockRestore();
  });

  test('sets loading state correctly during login', async () => {
    let resolveLogin;
    const loginPromise = new Promise((resolve) => {
      resolveLogin = resolve;
    });
    
    mockApi.post.mockReturnValueOnce(loginPromise);
    
    renderWithAuth();
    
    expect(screen.getByTestId('loading')).toHaveTextContent('Not loading');
    
    fireEvent.click(screen.getByTestId('login-btn'));
    
    // Should be loading immediately after click
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading');
    
    // Resolve the login
    resolveLogin({ 
      data: { 
        user: { id: 1, username: 'test' }, 
        access_token: 'token' 
      } 
    });
    
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not loading');
    });
  });

  test('preserves user permission information', () => {
    const mockUser = { 
      id: 1, 
      username: 'admin', 
      email: 'admin@example.com',
      permission: 'admin'
    };
    localStorage.setItem('user', JSON.stringify(mockUser));
    localStorage.setItem('token', 'mock-token');
    
    renderWithAuth();
    
    expect(screen.getByTestId('user')).toHaveTextContent('admin');
  });
});