'use client';

import { createContext, useContext } from 'react';
import { getDefaultTenant } from '@/lib/tenant';

/**
 * Tenant branding context.
 *
 * Populated server-side in app/layout.jsx via `generateMetadata` /
 * async RootLayout, which resolves the tenant slug from the
 * `x-tenant-slug` request header (set by middleware.js) and fetches
 * the config from `GET /api/v1/tenants/:slug`. Falls back to
 * `getDefaultTenant()` (APA/DOCiD branding) when no slug is present
 * or the backend returns 404.
 *
 * Consumed by Navbar, Hero, Footer, PreFooter, AboutDocid, and the
 * MUI ThemeContext (which passes tenant colors into getTheme()).
 */
const TenantContext = createContext(getDefaultTenant());

export function TenantProvider({ value, children }) {
  return (
    <TenantContext.Provider value={value || getDefaultTenant()}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
