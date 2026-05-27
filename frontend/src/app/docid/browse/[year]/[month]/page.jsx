import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export const dynamic = 'force-dynamic';
export const revalidate = 3600;

const MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

export async function generateMetadata({ params }) {
  const awaited = typeof params?.then === 'function' ? await params : params;
  const y = awaited?.year;
  const m = Number(awaited?.month);
  return {
    title: `DOCiD records: ${MONTH_NAMES[m] || ''} ${y}`,
    description: `Scholarly records registered in ${MONTH_NAMES[m] || ''} ${y} on the DOCiD platform.`,
  };
}

async function fetchMonth(year, month) {
  try {
    const url = `${getBackendApiV1BaseUrl()}/publications/sitemap?year=${year}&month=${month}`;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export default async function BrowseMonth({ params }) {
  const awaited = typeof params?.then === 'function' ? await params : params;
  const year = Number(awaited?.year);
  const month = Number(awaited?.month);
  if (!year || !month || month < 1 || month > 12) notFound();

  const rows = await fetchMonth(year, month);

  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <p>
        <Link href="/docid/browse">All years</Link>{' › '}
        <Link href={`/docid/browse/${year}`}>{year}</Link>
      </p>
      <h1>{MONTH_NAMES[month]} {year}</h1>
      {rows.length === 0 ? (
        <p>No records for {MONTH_NAMES[month]} {year}.</p>
      ) : (
        <ul>
          {rows.map((r) => (
            <li key={r.docid}>
              <a href={`/docid/${r.docid}`}>
                {r.title || r.docid}
              </a>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
