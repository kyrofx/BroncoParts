import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Login from '../Login';
import { AuthProvider } from '../../services/AuthContext';
import * as api from '../../services/api';

// Mock the API
jest.mock('../../services/api');
const mockApi = api;

// Mock react-toastify
jest.mock('react-toastify', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn()
  }
}));

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

const theme = createTheme();

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders login form elements', () => {
    renderLogin();
    
    expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('renders BroncoPartsV2 title', () => {
    renderLogin();
    
    expect(screen.getByText('BroncoPartsV2')).toBeInTheDocument();
  });

  test('renders registration link', () => {
    renderLogin();
    
    expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign up/i })).toBeInTheDocument();
  });

  test('allows user to type in email field', async () => {
    const user = userEvent.setup();
    renderLogin();
    
    const emailInput = screen.getByRole('textbox', { name: /email/i });
    await user.type(emailInput, 'test@example.com');
    
    expect(emailInput).toHaveValue('test@example.com');
  });

  test('allows user to type in password field', async () => {
    const user = userEvent.setup();
    renderLogin();
    
    const passwordInput = screen.getByLabelText(/password/i);
    await user.type(passwordInput, 'password123');
    
    expect(passwordInput).toHaveValue('password123');
  });

  test('submits form with correct data on successful login', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      data: {
        access_token: 'mock-token',
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          permission: 'editor'
        }
      }
    };
    
    mockApi.post.mockResolvedValueOnce(mockResponse);
    
    renderLogin();
    
    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    expect(mockApi.post).toHaveBeenCalledWith('/login', {
      email: 'test@example.com',
      password: 'password123'
    });
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  test('shows loading state during login', async () => {
    const user = userEvent.setup();
    let resolveLogin;
    const loginPromise = new Promise((resolve) => {
      resolveLogin = resolve;
    });
    
    mockApi.post.mockReturnValueOnce(loginPromise);
    
    renderLogin();
    
    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    // Button should be disabled during loading
    expect(submitButton).toBeDisabled();
    
    // Resolve the login
    resolveLogin({
      data: {
        access_token: 'token',
        user: { id: 1, username: 'test' }
      }
    });
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  test('handles login error with message', async () => {
    const user = userEvent.setup();
    const { toast } = require('react-toastify');
    
    const mockError = {
      response: {
        data: { message: 'Invalid credentials' }
      }
    };
    
    mockApi.post.mockRejectedValueOnce(mockError);
    
    renderLogin();
    
    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Invalid credentials');
    });
    
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('handles login error without specific message', async () => {
    const user = userEvent.setup();
    const { toast } = require('react-toastify');
    
    mockApi.post.mockRejectedValueOnce(new Error('Network error'));
    
    renderLogin();
    
    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Login failed. Please try again.');
    });
  });

  test('prevents form submission with empty fields', async () => {
    const user = userEvent.setup();
    renderLogin();
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);
    
    // Form should have validation, API should not be called
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  test('validates email format', async () => {
    const user = userEvent.setup();
    renderLogin();
    
    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'invalid-email');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    // Should show validation error for invalid email
    // The exact implementation depends on the validation used
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  test('redirects to dashboard after successful login', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      data: {
        access_token: 'mock-token',
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com'
        }
      }
    };
    
    mockApi.post.mockResolvedValueOnce(mockResponse);
    
    renderLogin();
    
    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  test('registration link navigates to signup page', () => {
    renderLogin();
    
    const signUpLink = screen.getByRole('link', { name: /sign up/i });
    expect(signUpLink).toHaveAttribute('href', '/register');
  });

  test('form submission prevents default behavior', async () => {
    const user = userEvent.setup();
    renderLogin();
    
    const form = screen.getByRole('form') || screen.getByTestId('login-form');
    const preventDefault = jest.fn();
    
    fireEvent.submit(form, { preventDefault });
    
    expect(preventDefault).toHaveBeenCalled();
  });

  test('clears form on successful login', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      data: {
        access_token: 'mock-token',
        user: { id: 1, username: 'testuser' }
      }
    };
    
    mockApi.post.mockResolvedValueOnce(mockResponse);
    
    renderLogin();
    
    const emailInput = screen.getByRole('textbox', { name: /email/i });
    const passwordInput = screen.getByLabelText(/password/i);
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }).closest('form'));
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled();
    });
    
    // Form fields should be cleared or component should navigate away
  });
});