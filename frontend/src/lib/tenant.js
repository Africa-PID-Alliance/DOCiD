/**
 * Default tenant config — used when:
 *  - no tenant slug resolves from the Host header (localhost, bare IP, docid.*)
 *  - backend /api/v1/tenants/:slug returns 404
 *  - backend is unreachable
 *
 * These values match the current production DOCiD/APA branding so
 * existing users see zero change when visiting the default hostname.
 */
export function getDefaultTenant() {
  return {
    slug: 'default',
    display_name: 'DOCiD™ APP',
    logo_url: '/assets/images/logo2.png',
    logo_dark_url: null,
    favicon_url: '/favicon.ico',
    og_image_url: '/assets/images/logo2.png',
    primary_color: '#1565c0',
    primary_color_dark: '#141a3b',
    accent_color: '#cce1f7',
    page_title: 'DOCiD™ APP',
    page_description:
      'DOCiD is a unique persistent identifier for African research outputs.',
    hero_tagline: null, // null = let the Hero component use its own hardcoded copy
    footer_copyright: '© DOCiD™',
    contact_email: 'info@africapidalliance.org',
    email_from_name: 'AFRICA PID Alliance',
    feature_flags: {},
    is_active: true,
  };
}

/**
 * Parse the tenant slug from an incoming Host header.
 *
 * Handles both:
 *   - `.africapidalliance.test`  (LOCAL DEV — IANA reserved TLD, no DNS leakage)
 *   - `.africapidalliance.org`   (PRODUCTION)
 *
 * Returns `null` for:
 *   - the default hostnames (`docid.*`, `www.*`, bare `africapidalliance.*`)
 *   - localhost / 127.0.0.1 / bare IPs
 *   - any hostname that doesn't match the expected pattern
 *
 * Strips any `:port` suffix before parsing.
 *
 * Examples:
 *   stellenbosch.africapidalliance.test:8080 → "stellenbosch"
 *   unilag.africapidalliance.org            → "unilag"
 *   docid.africapidalliance.test:8080       → null (default)
 *   www.africapidalliance.org               → null (default)
 *   localhost:3000                          → null (default)
 *   127.0.0.1                               → null (default)
 */
export function resolveTenantSlugFromHost(hostHeader) {
  if (!hostHeader) return null;

  const hostNoPort = hostHeader.split(':')[0].toLowerCase();

  // Match both .test (local dev) and .org (prod)
  const suffixes = ['.africapidalliance.test', '.africapidalliance.org'];
  const matchingSuffix = suffixes.find((s) => hostNoPort.endsWith(s));
  if (!matchingSuffix) return null;

  const firstSegment = hostNoPort.slice(
    0,
    hostNoPort.length - matchingSuffix.length,
  );
  if (!firstSegment) return null;
  // Must be a single dot-free segment (stellenbosch, unilag, etc.)
  if (firstSegment.includes('.')) return null;

  // Reserved / default slugs — fall through to default tenant
  const reserved = new Set(['docid', 'www', 'api', 'admin', 'blog']);
  if (reserved.has(firstSegment)) return null;

  return firstSegment;
}
