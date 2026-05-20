import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

// Attach an LC project (all its labels + notices) to a publication.
// JWT-required upstream — proxy forwards Authorization header.
export async function POST(request, { params }) {
  try {
    const { publicationId } = await params;
    const body = await request.text();

    const headers = { 'Content-Type': 'application/json' };
    const authorizationHeader = request.headers.get('Authorization');
    if (authorizationHeader) {
      headers['Authorization'] = authorizationHeader;
    }

    const response = await fetch(
      `${API_BASE_URL}/localcontexts/publications/${publicationId}/projects`,
      { method: 'POST', headers, body }
    );

    const data = await response.json().catch(() => ({ error: 'invalid backend response' }));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('LC project attach proxy error:', error);
    return NextResponse.json({ error: 'Service unavailable' }, { status: 503 });
  }
}
