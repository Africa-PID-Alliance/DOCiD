import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

// Public search endpoint backing the LC picker. Does NOT forward Authorization
// (the upstream is public; forwarding browser tokens through unrelated proxies
// expands the credential-exposure surface for no benefit).
export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const q = searchParams.get('q') || '';
    const limit = searchParams.get('limit') || '20';

    const backendUrl = `${API_BASE_URL}/localcontexts/projects/search?q=${encodeURIComponent(q)}&limit=${encodeURIComponent(limit)}`;

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await response.json().catch(() => ({ error: 'invalid backend response' }));
    return NextResponse.json(data, {
      status: response.status,
      headers: { 'Cache-Control': 'public, max-age=300' },
    });
  } catch (error) {
    console.error('Local Contexts search proxy error:', error);
    return NextResponse.json({ error: 'Search unavailable' }, { status: 503 });
  }
}
