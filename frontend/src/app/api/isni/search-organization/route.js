import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const name = searchParams.get('name');
  const country = searchParams.get('country');

  if (!name) {
    return NextResponse.json(
      { error: 'Organization name is required' },
      { status: 400 }
    );
  }

  try {
    const params = new URLSearchParams({ name });
    if (country) params.append('country', country);

    const response = await fetch(`${API_BASE_URL}/isni/search-organization?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error searching ISNI organization:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
