// Browse-by-year index. Server-rendered. Exists primarily to give Google
// Scholar a crawl path into every DOCiD landing page via plain HTML links.

import Link from 'next/link';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export const dynamic = 'force-dynamic';
export const revalidate = 3600;

export const metadata = {
  title: 'Browse DOCiD records by date',
  description: 'Archive index of scholarly records registered on the Africa PID Alliance DOCiD platform.',
};

async function fetchMonths() {
  try {
    const res = await fetch(`${getBackendApiV1BaseUrl()}/publications/sitemap/months`, {
      cache: 'no-store',
    });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export default async function BrowseRoot() {
  const months = await fetchMonths();
  const byYear = new Map();
  for (const m of months) {
    const y = Number(m.year);
    if (!byYear.has(y)) byYear.set(y, 0);
    byYear.set(y, byYear.get(y) + Number(m.count || 0));
  }
  const years = Array.from(byYear.entries()).sort((a, b) => b[0] - a[0]);

  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <h1>Browse DOCiD records</h1>
      <p>
        <Link href="/docid/recent">Recently registered records</Link>
      </p>
      <h2>By year</h2>
      {years.length === 0 ? (
        <p>No records available.</p>
      ) : (
        <ul>
          {years.map(([y, count]) => (
            <li key={y}>
              <Link href={`/docid/browse/${y}`}>{y}</Link>{' '}
              <span style={{ color: '#666' }}>({count})</span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
