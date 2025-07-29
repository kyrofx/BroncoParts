import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { AuthProvider } from './services/AuthContext';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles'; // Renamed for clarity
import CssBaseline from '@mui/material/CssBaseline';
import { lightTheme, darkTheme } from './theme'; // Import both themes
import { ThemeModeProvider, ThemeModeContext } from './services/ThemeModeContext'; // Import context

const root = ReactDOM.createRoot(document.getElementById('root'));

// Helper component to consume context and select theme
const AppWithTheme = () => {
  const { mode } = React.useContext(ThemeModeContext);
  const activeTheme = mode === 'light' ? lightTheme : darkTheme;

  return (
    <MuiThemeProvider theme={activeTheme}>
      <CssBaseline />
      <AuthProvider>
        <App />
      </AuthProvider>
    </MuiThemeProvider>
  );
};

root.render(
  <React.StrictMode>
    <ThemeModeProvider> { /* Wrap with our theme mode provider */ }
      <AppWithTheme /> { /* Use helper component */ }
    </ThemeModeProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
