import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const queryString = searchParams.toString();

    const backendUrl = `${API_BASE_URL}/rrid/resolve?${queryString}`;

    const headers = {
      'Content-Type': 'application/json',
    };
    const authorizationHeader = request.headers.get('Authorization');
    if (authorizationHeader) {
      headers['Authorization'] = authorizationHeader;
    }

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    });

    let data;
    try {
      data = await response.json();
    } catch (parseError) {
      return NextResponse.json(
        { error: 'Invalid response from RRID resolve service' },
        { status: 502 }
      );
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('RRID resolve proxy error:', error);
    return NextResponse.json(
      { error: 'RRID resolve service unavailable' },
      { status: 503 }
    );
  }
}
