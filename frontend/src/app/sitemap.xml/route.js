import { getBackendApiV1BaseUrl } from '@/lib/apiBase';
import { SITE_ORIGIN } from '@/lib/highwire';

export const dynamic = 'force-dynamic';
export const revalidate = 3600;

function xmlEscape(value) {
  return String(value).replace(/[<>&'"]/g, (c) => ({
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    "'": '&apos;',
    '"': '&quot;',
  }[c]));
}

export async function GET() {
  const origin = SITE_ORIGIN.replace(/\/+$/, '');
  let months = [];
  try {
    const res = await fetch(`${getBackendApiV1BaseUrl()}/publications/sitemap/months`, {
      cache: 'no-store',
    });
    if (res.ok) months = await res.json();
  } catch (err) {
    console.error('sitemap index: failed to fetch months', err);
  }

  const entries = (Array.isArray(months) ? months : []).map((m) => {
    const slug = `docid-${m.year}-${String(m.month).padStart(2, '0')}.xml`;
    const loc = `${origin}/sitemaps/${slug}`;
    return `  <sitemap><loc>${xmlEscape(loc)}</loc></sitemap>`;
  });

  // Always include the browse-by-date root so Google can crawl it even before
  // any monthly chunk exists.
  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    entries.join('\n') +
    (entries.length ? '\n' : '') +
    `</sitemapindex>\n`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
