import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

/**
 * GET /api/orcid/record/{orcidId}
 *
 * Returns the researcher's full PUBLIC ORCID record (person + activities: employments,
 * educations, works, fundings). No OAuth token is needed for public data.
 *
 * Source order:
 *   1. ORCID public API configured in NEXT_PUBLIC_ORCID_PUB_API_URL (sandbox in dev)
 *   2. ORCID production public API (https://pub.orcid.org) if the iD isn't on (1)
 *   3. DOCiD API /orcid/get-orcid/{id} (person section only) as a last resort
 */

const ORCID_ID_RE = /^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/i;
const PROD_PUB_API = 'https://pub.orcid.org';

async function fetchRecord(pubApiUrl, orcidId) {
  const res = await fetch(`${pubApiUrl.replace(/\/$/, '')}/v3.0/${orcidId}/record`, {
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) return null;
  return res.json();
}

export async function GET(request, { params }) {
  const { id } = await params;
  const orcidId = String(id || '').trim().replace(/^https?:\/\/(sandbox\.)?orcid\.org\//i, '');

  if (!ORCID_ID_RE.test(orcidId)) {
    return NextResponse.json({ error: 'Invalid ORCID iD format' }, { status: 400 });
  }

  const hosts = [process.env.NEXT_PUBLIC_ORCID_PUB_API_URL, PROD_PUB_API].filter(Boolean);
  for (const host of [...new Set(hosts)]) {
    try {
      const record = await fetchRecord(host, orcidId);
      if (record) {
        return NextResponse.json({ source: host, orcid_id: orcidId, record });
      }
    } catch (e) {
      console.warn(`ORCID record fetch failed on ${host}:`, e.message);
    }
  }

  // Fallback: DOCiD API (person section only)
  try {
    const res = await fetch(`${getBackendApiV1BaseUrl()}/orcid/get-orcid/${encodeURIComponent(orcidId)}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });
    if (res.ok) {
      const person = await res.json();
      return NextResponse.json({ source: 'docid-api', orcid_id: orcidId, record: { person } });
    }
    return NextResponse.json({ error: 'ORCID record not found' }, { status: res.status });
  } catch (e) {
    return NextResponse.json({ error: 'Failed to fetch ORCID record', message: e.message }, { status: 502 });
  }
}
