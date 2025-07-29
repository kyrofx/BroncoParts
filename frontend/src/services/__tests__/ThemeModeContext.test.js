import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeModeProvider, useThemeMode } from '../ThemeModeContext';

// Test component to access theme context
const TestComponent = () => {
  const { mode, toggleTheme } = useThemeMode();
  
  return (
    <div>
      <div data-testid="theme-mode">{mode}</div>
      <button data-testid="toggle-btn" onClick={toggleTheme}>
        Toggle Theme
      </button>
    </div>
  );
};

const renderWithTheme = () => {
  return render(
    <ThemeModeProvider>
      <TestComponent />
    </ThemeModeProvider>
  );
};

describe('ThemeModeContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('provides initial theme mode as light', () => {
    renderWithTheme();
    
    expect(screen.getByTestId('theme-mode')).toHaveTextContent('light');
  });

  test('loads theme from localStorage if available', () => {
    localStorage.setItem('themeMode', 'dark');
    
    renderWithTheme();
    
    expect(screen.getByTestId('theme-mode')).toHaveTextContent('dark');
  });

  test('toggles theme from light to dark', () => {
    renderWithTheme();
    
    expect(screen.getByTestId('theme-mode')).toHaveTextContent('light');
    
    fireEvent.click(screen.getByTestId('toggle-btn'));
    
    expect(screen.getByTestId('theme-mode')).toHaveTextContent('dark');
    expect(localStorage.getItem('themeMode')).toBe('dark');
  });

  test('toggles theme from dark to light', () => {
    localStorage.setItem('themeMode', 'dark');
    
    renderWithTheme();
    
    expect(screen.getByTestId('theme-mode')).toHaveTextContent('dark');
    
    fireEvent.click(screen.getByTestId('toggle-btn'));
    
    expect(screen.getByTestId('theme-mode')).toHaveTextContent('light');
    expect(localStorage.getItem('themeMode')).toBe('light');
  });

  test('persists theme mode in localStorage', () => {
    renderWithTheme();
    
    // Toggle to dark
    fireEvent.click(screen.getByTestId('toggle-btn'));
    expect(localStorage.getItem('themeMode')).toBe('dark');
    
    // Toggle back to light
    fireEvent.click(screen.getByTestId('toggle-btn'));
    expect(localStorage.getItem('themeMode')).toBe('light');
  });

  test('handles invalid localStorage value gracefully', () => {
    localStorage.setItem('themeMode', 'invalid-mode');
    
    renderWithTheme();
    
    // Should default to light mode
    expect(screen.getByTestId('theme-mode')).toHaveTextContent('light');
  });

  test('works without localStorage (e.g., in incognito mode)', () => {
    // Mock localStorage to throw errors
    const originalSetItem = localStorage.setItem;
    const originalGetItem = localStorage.getItem;
    
    localStorage.setItem = jest.fn(() => {
      throw new Error('localStorage not available');
    });
    localStorage.getItem = jest.fn(() => {
      throw new Error('localStorage not available');
    });
    
    try {
      renderWithTheme();
      
      // Should still work with default light mode
      expect(screen.getByTestId('theme-mode')).toHaveTextContent('light');
      
      // Should still be able to toggle
      fireEvent.click(screen.getByTestId('toggle-btn'));
      expect(screen.getByTestId('theme-mode')).toHaveTextContent('dark');
      
    } finally {
      // Restore localStorage
      localStorage.setItem = originalSetItem;
      localStorage.getItem = originalGetItem;
    }
  });
});