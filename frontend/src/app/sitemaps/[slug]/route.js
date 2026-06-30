import { getBackendApiV1BaseUrl } from '@/lib/apiBase';
import { canonicalDocidUrl } from '@/lib/highwire';

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

function parseSlug(slug) {
  // Expected form: docid-YYYY-MM.xml
  const m = /^docid-(\d{4})-(\d{2})\.xml$/.exec(slug || '');
  if (!m) return null;
  const year = Number(m[1]);
  const month = Number(m[2]);
  if (!year || month < 1 || month > 12) return null;
  return { year, month };
}

export async function GET(_req, { params }) {
  const awaited = typeof params?.then === 'function' ? await params : params;
  const parsed = parseSlug(awaited?.slug);
  if (!parsed) {
    return new Response('Invalid sitemap slug', { status: 404 });
  }

  let rows = [];
  try {
    const url = `${getBackendApiV1BaseUrl()}/publications/sitemap?year=${parsed.year}&month=${parsed.month}`;
    const res = await fetch(url, { cache: 'no-store' });
    if (res.ok) rows = await res.json();
  } catch (err) {
    console.error('sitemap feed: backend fetch failed', err);
  }

  const urls = (Array.isArray(rows) ? rows : [])
    .map((r) => {
      const loc = canonicalDocidUrl(r.docid);
      if (!loc) return null;
      // W3C datetime requires timezone. Backend returns bare ISO (no Z/offset);
      // append Z so sitemaps pass Google's validator.
      const updatedAtUtc = r.updated_at
        ? r.updated_at.replace(/(\.\d+)?$/, 'Z').replace(/Z+$/, 'Z')
        : null;
      const lastmod = updatedAtUtc ? `    <lastmod>${xmlEscape(updatedAtUtc)}</lastmod>\n` : '';
      return `  <url>\n    <loc>${xmlEscape(loc)}</loc>\n${lastmod}  </url>`;
    })
    .filter(Boolean);

  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    urls.join('\n') +
    (urls.length ? '\n' : '') +
    `</urlset>\n`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
