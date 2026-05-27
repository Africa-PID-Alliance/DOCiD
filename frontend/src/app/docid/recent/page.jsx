// Recent records — server-rendered plain HTML for Scholar / Googlebot crawl.

import Link from 'next/link';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export const dynamic = 'force-dynamic';
export const revalidate = 600;

export const metadata = {
  title: 'Recent DOCiD records',
  description: 'Most recently registered scholarly records on the Africa PID Alliance DOCiD platform.',
};

async function fetchRecent() {
  try {
    const res = await fetch(
      `${getBackendApiV1BaseUrl()}/publications?page=1&page_size=100&sort=published&order=desc`,
      { cache: 'no-store' },
    );
    if (!res.ok) return [];
    const data = await res.json();
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.publications)) return data.publications;
    if (Array.isArray(data?.data)) return data.data;
    return [];
  } catch {
    return [];
  }
}

export default async function Recent() {
  const rows = await fetchRecent();
  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <p>
        <Link href="/docid/browse">Browse by date</Link>
      </p>
      <h1>Recent DOCiD records</h1>
      {rows.length === 0 ? (
        <p>No records available.</p>
      ) : (
        <ul>
          {rows.map((r) => {
            const docid = r.document_docid || r.docid;
            if (!docid) return null;
            const title = r.document_title || r.title || docid;
            return (
              <li key={docid}>
                <a href={`/docid/${docid}`}>{title}</a>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
