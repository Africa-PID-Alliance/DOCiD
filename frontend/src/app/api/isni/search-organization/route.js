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

    const backendUrl = `${API_BASE_URL}/isni/search-organization?${params}`;
    console.log('ISNI proxy request to:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('ISNI backend response status:', response.status);

    // Try to parse JSON response
    let data;
    try {
      data = await response.json();
    } catch (parseError) {
      console.error('Failed to parse ISNI response:', parseError);
      return NextResponse.json(
        { error: 'Invalid response from ISNI service' },
        { status: 502 }
      );
    }

    // Pass through the backend response with its status
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error searching ISNI organization:', error);
    return NextResponse.json(
      { error: `Failed to connect to ISNI service: ${error.message}` },
      { status: 503 }
    );
  }
}
