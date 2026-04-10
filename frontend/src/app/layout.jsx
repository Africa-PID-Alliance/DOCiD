import { headers } from 'next/headers';
import { cache } from 'react';

import ClientWrapper from './ClientWrapper';
import { getDefaultTenant, resolveTenantSlugFromHost } from '@/lib/tenant';

/**
 * Server-side tenant resolution.
 *
 * Reads the Host header from the incoming request, parses the
 * subdomain slug (e.g. `stellenbosch.africapidalliance.test` →
 * `stellenbosch`), and fetches the branding config from the backend.
 *
 * Wrapped in React.cache so it's deduped across `generateMetadata`
 * and the RootLayout render within a single request (cheap either way
 * thanks to Next.js fetch cache, but `cache()` removes the double
 * invocation entirely).
 *
 * Falls back to `getDefaultTenant()` on any failure — the site must
 * NEVER break because of tenant resolution. Worst case: wrong logo
 * for a few seconds until the cache warms or the backend recovers.
 */
const resolveTenant = cache(async () => {
  const headerList = await headers();
  const hostHeader = headerList.get('host') || '';
  const slug = resolveTenantSlugFromHost(hostHeader);
  if (!slug) {
    return getDefaultTenant();
  }

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!apiBaseUrl) {
    console.warn('[tenant] NEXT_PUBLIC_API_BASE_URL not set, using default');
    return getDefaultTenant();
  }

  try {
    const response = await fetch(
      `${apiBaseUrl}/tenants/${encodeURIComponent(slug)}`,
      { next: { revalidate: 300 } },
    );
    if (!response.ok) {
      // 404 is the expected path for unknown slugs — silently fall back.
      if (response.status !== 404) {
        console.warn(
          `[tenant] backend returned ${response.status} for slug=${slug}`,
        );
      }
      return getDefaultTenant();
    }
    return await response.json();
  } catch (error) {
    console.error(`[tenant] failed to resolve slug=${slug}:`, error);
    return getDefaultTenant();
  }
});

export async function generateMetadata() {
  const tenant = await resolveTenant();
  return {
    title: {
      default: tenant.page_title || 'DOCiD™ APP',
      template: `%s | ${tenant.display_name || 'DOCiD™ APP'}`,
    },
    description:
      tenant.page_description ||
      'DOCiD™ is a Document Identification System for managing and tracking digital objects',
    keywords:
      'DOCiD, document management, digital objects, identification system',
    authors: [{ name: 'Africa PID Alliance' }],
    openGraph: {
      title: tenant.page_title || 'DOCiD™ APP',
      description:
        tenant.page_description ||
        'DOCiD™ is a Document Identification System for managing and tracking digital objects',
      type: 'website',
      siteName: tenant.display_name || 'DOCiD™',
      locale: 'en_US',
      images: tenant.og_image_url ? [tenant.og_image_url] : undefined,
    },
    robots: {
      index: true,
      follow: true,
    },
    viewport: {
      width: 'device-width',
      initialScale: 1,
    },
    icons: {
      icon: tenant.favicon_url || '/favicon.ico',
    },
    verification: {
      google: 'google-site-verification',
    },
    alternates: {
      canonical: 'https://docid.africa',
    },
  };
}

export default async function RootLayout({ children }) {
  const tenant = await resolveTenant();
  return (
    <html lang="en">
      <body suppressHydrationWarning={true}>
        <ClientWrapper tenant={tenant}>
          {children}
        </ClientWrapper>
      </body>
    </html>
  );
}
