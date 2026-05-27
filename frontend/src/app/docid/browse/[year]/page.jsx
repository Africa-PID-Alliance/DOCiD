import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export const dynamic = 'force-dynamic';
export const revalidate = 3600;

export async function generateMetadata({ params }) {
  const awaited = typeof params?.then === 'function' ? await params : params;
  return {
    title: `DOCiD records: ${awaited?.year}`,
    description: `Scholarly records registered in ${awaited?.year} on the DOCiD platform.`,
  };
}

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

const MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

export default async function BrowseYear({ params }) {
  const awaited = typeof params?.then === 'function' ? await params : params;
  const year = Number(awaited?.year);
  if (!year || year < 1900 || year > 9999) notFound();

  const months = (await fetchMonths()).filter((m) => Number(m.year) === year);
  months.sort((a, b) => Number(b.month) - Number(a.month));

  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <p>
        <Link href="/docid/browse">All years</Link>
      </p>
      <h1>DOCiD records: {year}</h1>
      {months.length === 0 ? (
        <p>No records for {year}.</p>
      ) : (
        <ul>
          {months.map((m) => (
            <li key={`${m.year}-${m.month}`}>
              <Link href={`/docid/browse/${year}/${String(m.month).padStart(2, '0')}`}>
                {MONTH_NAMES[Number(m.month)] || `Month ${m.month}`}
              </Link>{' '}
              <span style={{ color: '#666' }}>({m.count})</span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
