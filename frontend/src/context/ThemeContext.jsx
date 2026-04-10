'use client';

import { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { ThemeProvider as MUIThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '@/theme/theme';
import { useTenant } from '@/context/TenantContext';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const tenant = useTenant();
  const [mode, setMode] = useState('light');
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Check if there's a saved theme preference
    const savedMode = localStorage.getItem('themeMode');
    if (savedMode) {
      setMode(savedMode);
    }
    setIsHydrated(true);
  }, []);

  const toggleTheme = () => {
    const newMode = mode === 'light' ? 'dark' : 'light';
    setMode(newMode);
    localStorage.setItem('themeMode', newMode);
  };

  // Rebuild the MUI theme only when mode or tenant changes — not on
  // every render of every child component.
  const theme = useMemo(
    () => createAppTheme(isHydrated ? mode : 'light', tenant),
    [mode, isHydrated, tenant],
  );

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme }}>
      <MUIThemeProvider theme={theme}>
        {children}
      </MUIThemeProvider>
    </ThemeContext.Provider>
  );
};

export const useThemeContext = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeContext must be used within a ThemeProvider');
  }
  return context;
}; 