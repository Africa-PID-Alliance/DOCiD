import { NextResponse } from 'next/server';
import { BACKEND_API_URL as ANALYTICS_API_URL } from '@/lib/backendUrl';

const PUBLICATIONS_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

export async function GET(request, { params }) {
  const { id } = (await params);

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/publications/${id}/files-stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch files statistics' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching files statistics:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// DELETE retires (soft-deletes) the publication: Flask keeps the row so the
// DOCiD handle still resolves, and the public page shows a retired notice.
export async function DELETE(request, { params }) {
  const { id } = (await params);

  const requestHeaders = {};
  const authorizationHeader = request.headers.get('Authorization');
  if (authorizationHeader) requestHeaders['Authorization'] = authorizationHeader;

  // Optional JSON body, e.g. { "reason": "..." }
  const rawBody = await request.text().catch(() => '');
  if (rawBody) requestHeaders['Content-Type'] = 'application/json';

  try {
    const backendResponse = await fetch(`${PUBLICATIONS_API_URL}/publications/${id}`, {
      method: 'DELETE',
      headers: requestHeaders,
      body: rawBody || undefined,
    });

    const responseData = await backendResponse.json().catch(() => ({}));
    return NextResponse.json(responseData, { status: backendResponse.status });
  } catch (error) {
    console.error('Error retiring publication:', error);
    return NextResponse.json(
      { error: 'Internal server error while retiring publication' },
      { status: 500 }
    );
  }
}
