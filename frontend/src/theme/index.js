import { createTheme } from '@mui/material/styles';

const colors = {
  primary: {
    main: '#1976d2',
    light: '#5F8BB920',
    dark: '#141a3b',
  },
  secondary: {
    main: '#ffffff',
    dark: '#f5f5f5',
  },
  text: {
    primary: '#1a1a1a',
    secondary: '#666666',
    light: '#ffffff',
  },
};

const theme = createTheme({
  palette: {
    primary: {
      main: colors.primary.main,
      light: colors.primary.light,
      dark: colors.primary.dark,
    },
    background: {
      default: '#ffffff',
      paper: colors.secondary.dark,
      content: colors.primary.light,
      footer: colors.primary.dark,
      navbar: colors.primary.main,
    },
    text: {
      primary: colors.text.primary,
      secondary: colors.text.secondary,
      light: colors.text.light,
    },
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
    subtitle1: {
      fontSize: '1.1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    subtitle2: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
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
          backgroundColor: colors.primary.light,
          minHeight: '100vh',
        },
        '#__next': {
          minHeight: '100vh',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          padding: '8px 24px',
          transition: 'all 0.3s ease',
        },
        contained: {
          backgroundColor: colors.primary.dark,
          color: colors.text.light,
          '&:hover': {
            backgroundColor: colors.primary.main,
            transform: 'translateY(-2px)',
            boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
          },
        },
        outlined: {
          borderColor: colors.primary.dark,
          color: colors.primary.dark,
          '&:hover': {
            borderColor: colors.primary.main,
            backgroundColor: 'rgba(25, 118, 210, 0.04)',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: colors.primary.main,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        },
      },
    },
  },
});

export default theme; 