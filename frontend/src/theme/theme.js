import { createTheme } from '@mui/material/styles';
import { getDefaultTenant } from '@/lib/tenant';

/**
 * Build the MUI theme object, parameterized by color mode AND by
 * per-tenant branding colors.
 *
 * Tenant config provides:
 *   - primary_color        → light-mode primary (navbar, buttons, links)
 *   - primary_color_dark   → light-mode primary.dark (hover, footer bg)
 *   - accent_color         → primary.light / dividers / accent fills
 *
 * If a tenant is not supplied or any color is null/missing, the
 * DOCiD default palette is used (blue #1565c0, navy #141a3b,
 * light-blue #cce1f7). This guarantees the site never looks broken
 * when tenant resolution fails.
 */
const getTheme = (mode, tenant = null) => {
  const t = tenant || getDefaultTenant();

  // Resolve the three core brand colors with safe fallbacks.
  const tenantPrimary = t.primary_color || '#1565c0';
  const tenantPrimaryDark = t.primary_color_dark || '#141a3b';
  const tenantAccent = t.accent_color || '#cce1f7';

  // Light mode uses the tenant colors directly.
  // Dark mode keeps the existing inverted scheme but swaps the
  // "color" slot to the tenant accent so branded accents stay visible
  // on the dark navbar/footer background.
  const palette =
    mode === 'light'
      ? {
          mode,
          primary: {
            main: tenantPrimary,
            light: tenantAccent,
            dark: tenantPrimaryDark,
          },
          text: {
            primary: tenantPrimaryDark,
            secondary: tenantPrimary,
            light: '#ffffff',
          },
          background: {
            default: '#ffffff',
            paper: '#ffffff',
            content: tenantAccent,
            footer: tenantPrimaryDark,
            navbar: tenantPrimary,
          },
          divider: tenantAccent,
        }
      : {
          mode,
          primary: {
            main: tenantAccent,
            light: '#ffffff',
            dark: '#ffffff',
          },
          text: {
            primary: '#ffffff',
            secondary: tenantAccent,
            light: '#ffffff',
          },
          background: {
            default: tenantPrimaryDark,
            paper: tenantPrimary,
            content: tenantPrimaryDark,
            footer: tenantPrimary,
            navbar: tenantPrimaryDark,
          },
          divider: tenantPrimary,
        };

  // Shared color tokens used inside `components` style overrides below.
  const appBarBg = mode === 'light' ? tenantPrimary : tenantPrimaryDark;
  const containedBg = mode === 'light' ? tenantPrimary : tenantAccent;
  const containedColor = mode === 'light' ? '#ffffff' : tenantPrimaryDark;
  const containedHoverBg = mode === 'light' ? tenantPrimaryDark : '#ffffff';
  const outlinedBorder = mode === 'light' ? tenantPrimary : tenantAccent;
  const outlinedHoverBorder = mode === 'light' ? tenantPrimaryDark : '#ffffff';
  const cardBg = mode === 'light' ? '#ffffff' : tenantPrimary;
  const paperBg = mode === 'light' ? '#ffffff' : tenantPrimary;
  const bodyBg = mode === 'light' ? '#ffffff' : tenantPrimaryDark;

  return {
    palette,
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
            backgroundColor: bodyBg,
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: appBarBg,
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
            backgroundColor: containedBg,
            color: containedColor,
            '&:hover': {
              backgroundColor: containedHoverBg,
              transform: 'translateY(-2px)',
              boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
            },
          },
          outlined: {
            borderColor: outlinedBorder,
            color: outlinedBorder,
            '&:hover': {
              borderColor: outlinedHoverBorder,
              backgroundColor:
                mode === 'light'
                  ? 'rgba(21, 101, 192, 0.04)'
                  : 'rgba(204, 225, 247, 0.04)',
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: '12px',
            boxShadow:
              mode === 'light'
                ? '0 4px 12px rgba(21, 101, 192, 0.1)'
                : '0 4px 12px rgba(204, 225, 247, 0.1)',
            backgroundColor: cardBg,
            transition: 'all 0.3s ease',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundColor: paperBg,
            transition: 'background-color 0.3s ease',
          },
        },
      },
    },
  };
};

export const createAppTheme = (mode, tenant = null) => {
  return createTheme(getTheme(mode, tenant));
};
