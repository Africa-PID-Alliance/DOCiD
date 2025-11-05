import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q');
  const offset = searchParams.get('offset') || '0';
  const limit = searchParams.get('limit') || '10';

  if (!q) {
    return NextResponse.json(
      { error: 'Search query (q) is required' },
      { status: 400 }
    );
  }

  try {
    const params = new URLSearchParams({ q, offset, limit });
    const response = await fetch(`${API_BASE_URL}/isni/search?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error searching ISNI:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
