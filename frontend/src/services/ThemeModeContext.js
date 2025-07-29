import React, { createContext, useState, useMemo } from 'react';

export const ThemeModeContext = createContext({
  toggleThemeMode: () => {},
  mode: 'light',
});

export const ThemeModeProvider = ({ children }) => {
  const [mode, setMode] = useState('light');

  const themeMode = useMemo(
    () => ({
      toggleThemeMode: () => {
        setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
      },
      mode,
    }),
    [mode]
  );

  return (
    <ThemeModeContext.Provider value={themeMode}>
      {children}
    </ThemeModeContext.Provider>
  );
};
