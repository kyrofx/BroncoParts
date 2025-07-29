import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './services/AuthContext';
import { ThemeModeProvider } from './services/ThemeModeContext';

// Mock components that might cause issues in testing
jest.mock('./components/Projects', () => {
  return function MockProjects() {
    return <div data-testid="projects">Projects Component</div>;
  };
});

jest.mock('./components/Login', () => {
  return function MockLogin() {
    return <div data-testid="login">Login Component</div>;
  };
});

const renderApp = () => {
  return render(
    <BrowserRouter>
      <ThemeModeProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ThemeModeProvider>
    </BrowserRouter>
  );
};

describe('App Component', () => {
  test('renders without crashing', () => {
    renderApp();
    // The app should render without throwing any errors
  });

  test('renders login page when not authenticated', () => {
    renderApp();
    // Should show login page by default when not authenticated
    expect(screen.getByTestId('login')).toBeInTheDocument();
  });
});
