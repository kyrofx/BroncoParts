// frontend/src/components/UserSettings.js
import React, { useContext } from 'react';
import { Container, Typography, Switch, FormControlLabel, Box } from '@mui/material';
import { ThemeModeContext } from '../services/ThemeModeContext';

const UserSettings = () => {
  const { mode, toggleThemeMode } = useContext(ThemeModeContext);

  return (
    <Container>
      <Typography variant="h4" gutterBottom sx={{ mt: 2, mb: 3 }}>
        User Settings
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <FormControlLabel
          control={
            <Switch
              checked={mode === 'dark'}
              onChange={toggleThemeMode}
              name="darkModeSwitch"
            />
          }
          label="Dark Mode"
        />
        {/* Other settings can be added here in the future */}
      </Box>
    </Container>
  );
};

export default UserSettings;
