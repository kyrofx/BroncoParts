import React, { createContext, useState, useContext, useEffect } from 'react';
import api from './api'; // Assuming api.js is in the same services folder or adjust path

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // To check initial auth status

  useEffect(() => {
    // Check if user is already logged in (e.g., from localStorage)
    const token = localStorage.getItem('accessToken');
    const storedUser = localStorage.getItem('user');
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
        // You might want to verify the token with the backend here for more security
        // For now, we assume if a token and user info exist, they are valid.
      } catch (error) {
        console.error("Failed to parse stored user:", error);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await api.post('/login', { email, password });
      console.log('Login API response.data:', response.data); // <-- ADD THIS LINE
      localStorage.setItem('accessToken', response.data.access_token);
      // Assuming the backend returns user details in response.data.user
      // Adjust according to your actual API response structure for user details
      const userData = {
        id: response.data.user?.id, // Access nested property
        username: response.data.user?.username, // Access nested property
        permission: response.data.user?.permission, // Access nested property
        enabled: response.data.user?.enabled, // Access nested property
        is_approved: response.data.user?.is_approved // Access nested property for approval status
      };
      console.log('Constructed userData:', userData); // <-- ADD THIS LINE
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      return userData; // Return user data on successful login
    } catch (error) {
      console.error("Login failed:", error);
      throw error; // Rethrow error to be caught by the Login component
    }
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    setUser(null);
    // Optionally, call a backend logout endpoint if you have one
  };

  // The value provided to the context consumers
  const value = {
    user,
    isAuthenticated: !!user,
    isLoading: loading, // Expose loading state for initial auth check
    login,
    logout,
    setUser // Allow manual setting of user if needed (e.g. after registration confirmation)
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use the auth context
export const useAuth = () => {
  return useContext(AuthContext);
};
