import { SITE_ORIGIN } from '@/lib/highwire';

export const dynamic = 'force-static';

export function GET() {
  const body = [
    'User-agent: Googlebot',
    'Allow: /',
    '',
    'User-agent: Googlebot-Scholar',
    'Allow: /',
    '',
    'User-agent: *',
    'Allow: /',
    '',
    `Sitemap: ${SITE_ORIGIN.replace(/\/+$/, '')}/sitemap.xml`,
    '',
  ].join('\n');
  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
