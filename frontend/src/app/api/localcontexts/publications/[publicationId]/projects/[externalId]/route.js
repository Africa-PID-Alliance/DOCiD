import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

// Detach an LC project from a publication.
// JWT-required upstream — proxy forwards Authorization header.
export async function DELETE(request, { params }) {
  try {
    const { publicationId, externalId } = await params;

    const headers = {};
    const authorizationHeader = request.headers.get('Authorization');
    if (authorizationHeader) {
      headers['Authorization'] = authorizationHeader;
    }

    const response = await fetch(
      `${API_BASE_URL}/localcontexts/publications/${publicationId}/projects/${externalId}`,
      { method: 'DELETE', headers }
    );

    const data = await response.json().catch(() => ({ error: 'invalid backend response' }));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('LC project detach proxy error:', error);
    return NextResponse.json({ error: 'Service unavailable' }, { status: 503 });
  }
}
