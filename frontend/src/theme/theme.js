import { createTheme } from '@mui/material/styles';

const getTheme = (mode) => ({
  palette: {
    mode,
    ...(mode === 'light' 
      ? {
          // Light mode
          primary: {
            main: '#1565c0',
            light: '#cce1f7',
            dark: '#141a3b',
          },
          text: {
            primary: '#141a3b',
            secondary: '#1565c0',
            light: '#ffffff',
          },
          background: {
            default: '#ffffff',
            paper: '#ffffff',
            content: '#cce1f7',
            footer: '#141a3b',
            navbar: '#1565c0'
          },
          divider: '#cce1f7',
        }
      : {
          // Dark mode - reversed colors
          primary: {
            main: '#cce1f7',
            light: '#ffffff',
            dark: '#ffffff',
          },
          text: {
            primary: '#ffffff',
            secondary: '#cce1f7',
            light: '#ffffff',
          },
          background: {
            default: '#141a3b',
            paper: '#1565c0',
            content: '#141a3b',
            footer: '#1565c0',
            navbar: '#141a3b'
          },
          divider: '#1565c0',
        }),
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '3.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      '@media (max-width:600px)': {
        fontSize: '2.5rem',
      },
    },
    h2: {
      fontSize: '2.8rem',
      fontWeight: 600,
      lineHeight: 1.3,
      '@media (max-width:600px)': {
        fontSize: '2rem',
      },
    },
    h3: {
      fontSize: '2.2rem',
      fontWeight: 600,
      lineHeight: 1.3,
      '@media (max-width:600px)': {
        fontSize: '1.8rem',
      },
    },
    h4: {
      fontSize: '1.8rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.5rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1.2rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.95rem',
      lineHeight: 1.6,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
      fontSize: '1rem',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          transition: 'background-color 0.3s ease, color 0.3s ease',
          backgroundColor: mode === 'light' ? '#ffffff' : '#141a3b',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? '#1565c0' : '#141a3b',
          transition: 'background-color 0.3s ease',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '8px',
          padding: '8px 24px',
          transition: 'all 0.3s ease',
        },
        contained: {
          backgroundColor: mode === 'light' ? '#1565c0' : '#cce1f7',
          color: mode === 'light' ? '#ffffff' : '#141a3b',
          '&:hover': {
            backgroundColor: mode === 'light' ? '#141a3b' : '#ffffff',
            transform: 'translateY(-2px)',
            boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
          },
        },
        outlined: {
          borderColor: mode === 'light' ? '#1565c0' : '#cce1f7',
          color: mode === 'light' ? '#1565c0' : '#cce1f7',
          '&:hover': {
            borderColor: mode === 'light' ? '#141a3b' : '#ffffff',
            backgroundColor: mode === 'light' ? 'rgba(21, 101, 192, 0.04)' : 'rgba(204, 225, 247, 0.04)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: mode === 'light' 
            ? '0 4px 12px rgba(21, 101, 192, 0.1)' 
            : '0 4px 12px rgba(204, 225, 247, 0.1)',
          backgroundColor: mode === 'light' ? '#ffffff' : '#1565c0',
          transition: 'all 0.3s ease',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? '#ffffff' : '#1565c0',
          transition: 'background-color 0.3s ease',
        },
      },
    },
  },
});

export const createAppTheme = (mode) => {
  return createTheme(getTheme(mode));
}; 