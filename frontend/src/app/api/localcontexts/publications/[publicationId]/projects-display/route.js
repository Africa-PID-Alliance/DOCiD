import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

// Public aggregation endpoint feeding the DOCiD detail page LC panel.
// Returns { projects: [...], legacy: [...] } envelope. No Authorization
// forwarding — endpoint is public-by-design (display path).
export async function GET(request, { params }) {
  try {
    const { publicationId } = await params;

    const response = await fetch(
      `${API_BASE_URL}/localcontexts/publications/${publicationId}/projects-display`,
      { method: 'GET', headers: { 'Content-Type': 'application/json' } }
    );

    const data = await response.json().catch(() => ({ error: 'invalid backend response' }));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('LC projects-display proxy error:', error);
    return NextResponse.json({ error: 'Service unavailable' }, { status: 503 });
  }
}
