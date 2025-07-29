import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Register from '../Register';
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

const renderRegister = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <Register />
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Register Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders registration form elements', () => {
    renderRegister();
    
    expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /first name/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /last name/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
  });

  test('renders page title', () => {
    renderRegister();
    
    expect(screen.getByText('Register for BroncoPartsV2')).toBeInTheDocument();
  });

  test('renders login link', () => {
    renderRegister();
    
    expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
  });

  test('allows user to fill all form fields', async () => {
    const user = userEvent.setup();
    renderRegister();
    
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser');
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByRole('textbox', { name: /first name/i }), 'Test');
    await user.type(screen.getByRole('textbox', { name: /last name/i }), 'User');
    
    expect(screen.getByRole('textbox', { name: /username/i })).toHaveValue('testuser');
    expect(screen.getByRole('textbox', { name: /email/i })).toHaveValue('test@example.com');
    expect(screen.getByLabelText(/^password$/i)).toHaveValue('password123');
    expect(screen.getByLabelText(/confirm password/i)).toHaveValue('password123');
    expect(screen.getByRole('textbox', { name: /first name/i })).toHaveValue('Test');
    expect(screen.getByRole('textbox', { name: /last name/i })).toHaveValue('User');
  });

  test('submits registration with correct data', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      data: { message: 'User registered successfully' }
    };
    
    mockApi.post.mockResolvedValueOnce(mockResponse);
    
    renderRegister();
    
    // Fill form
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser');
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByRole('textbox', { name: /first name/i }), 'Test');
    await user.type(screen.getByRole('textbox', { name: /last name/i }), 'User');
    
    // Submit
    await user.click(screen.getByRole('button', { name: /register/i }));
    
    expect(mockApi.post).toHaveBeenCalledWith('/register', {
      username: 'testuser',
      email: 'test@example.com',
      password: 'password123',
      first_name: 'Test',
      last_name: 'User'
    });
  });

  test('shows success message and redirects on successful registration', async () => {
    const user = userEvent.setup();
    const { toast } = require('react-toastify');
    const mockResponse = {
      data: { message: 'User registered successfully' }
    };
    
    mockApi.post.mockResolvedValueOnce(mockResponse);
    
    renderRegister();
    
    // Fill and submit form
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser');
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByRole('textbox', { name: /first name/i }), 'Test');
    await user.type(screen.getByRole('textbox', { name: /last name/i }), 'User');
    await user.click(screen.getByRole('button', { name: /register/i }));
    
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('User registered successfully');
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  test('shows loading state during registration', async () => {
    const user = userEvent.setup();
    let resolveRegistration;
    const registrationPromise = new Promise((resolve) => {
      resolveRegistration = resolve;
    });
    
    mockApi.post.mockReturnValueOnce(registrationPromise);
    
    renderRegister();
    
    // Fill form
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser');
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByRole('textbox', { name: /first name/i }), 'Test');
    await user.type(screen.getByRole('textbox', { name: /last name/i }), 'User');
    
    const submitButton = screen.getByRole('button', { name: /register/i });
    await user.click(submitButton);
    
    // Button should be disabled during loading
    expect(submitButton).toBeDisabled();
    
    // Resolve registration
    resolveRegistration({ data: { message: 'Success' } });
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  test('validates password confirmation', async () => {
    const user = userEvent.setup();
    renderRegister();
    
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'differentpassword');
    
    const submitButton = screen.getByRole('button', { name: /register/i });
    await user.click(submitButton);
    
    // Should show validation error and not submit
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  test('handles registration error with specific message', async () => {
    const user = userEvent.setup();
    const { toast } = require('react-toastify');
    
    const mockError = {
      response: {
        data: { message: 'Username already exists' }
      }
    };
    
    mockApi.post.mockRejectedValueOnce(mockError);
    
    renderRegister();
    
    // Fill and submit form
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'existinguser');
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByRole('textbox', { name: /first name/i }), 'Test');
    await user.type(screen.getByRole('textbox', { name: /last name/i }), 'User');
    await user.click(screen.getByRole('button', { name: /register/i }));
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Username already exists');
    });
    
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('handles registration error without specific message', async () => {
    const user = userEvent.setup();
    const { toast } = require('react-toastify');
    
    mockApi.post.mockRejectedValueOnce(new Error('Network error'));
    
    renderRegister();
    
    // Fill and submit form
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser');
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByRole('textbox', { name: /first name/i }), 'Test');
    await user.type(screen.getByRole('textbox', { name: /last name/i }), 'User');
    await user.click(screen.getByRole('button', { name: /register/i }));
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Registration failed. Please try again.');
    });
  });

  test('validates required fields', async () => {
    const user = userEvent.setup();
    renderRegister();
    
    const submitButton = screen.getByRole('button', { name: /register/i });
    await user.click(submitButton);
    
    // Should not submit with empty required fields
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  test('validates email format', async () => {
    const user = userEvent.setup();
    renderRegister();
    
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'invalid-email');
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    
    const submitButton = screen.getByRole('button', { name: /register/i });
    await user.click(submitButton);
    
    // Should show validation error for invalid email
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  test('login link navigates to login page', () => {
    renderRegister();
    
    const loginLink = screen.getByRole('link', { name: /sign in/i });
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  test('prevents form submission with mismatched passwords', async () => {
    const user = userEvent.setup();
    renderRegister();
    
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser');
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password456');
    await user.type(screen.getByRole('textbox', { name: /first name/i }), 'Test');
    await user.type(screen.getByRole('textbox', { name: /last name/i }), 'User');
    
    const submitButton = screen.getByRole('button', { name: /register/i });
    await user.click(submitButton);
    
    expect(mockApi.post).not.toHaveBeenCalled();
  });

  test('shows approval message in success notification', async () => {
    const user = userEvent.setup();
    const { toast } = require('react-toastify');
    const mockResponse = {
      data: { message: 'Registration successful. Your account is pending approval.' }
    };
    
    mockApi.post.mockResolvedValueOnce(mockResponse);
    
    renderRegister();
    
    // Fill and submit form
    await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser');
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.type(screen.getByRole('textbox', { name: /first name/i }), 'Test');
    await user.type(screen.getByRole('textbox', { name: /last name/i }), 'User');
    await user.click(screen.getByRole('button', { name: /register/i }));
    
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('Registration successful. Your account is pending approval.');
    });
  });
});