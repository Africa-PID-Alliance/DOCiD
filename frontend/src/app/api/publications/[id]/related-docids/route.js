import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

// Related DOCiDs for a publication. Flask asks URAAS (keyword overlap) and
// returns the matching DOCiD records; the URAAS key never reaches the browser.
export async function GET(request, { params }) {
  const { id } = await params;
  if (!/^\d+$/.test(String(id))) {
    return NextResponse.json({ error: 'Invalid publication id', related: [] }, { status: 400 });
  }

  try {
    const response = await fetch(
      `${getBackendApiV1BaseUrl()}/publications/${id}/related-docids`,
      { headers: { Accept: 'application/json' }, cache: 'no-store' }
    );
    const data = await response.json().catch(() => ({}));
    return NextResponse.json(
      { related: [], ...data },
      { status: response.status }
    );
  } catch (error) {
    console.error('Related DOCiDs proxy failed:', error);
    return NextResponse.json(
      { error: 'Related DOCiDs are unavailable right now', related: [] },
      { status: 503 }
    );
  }
}
