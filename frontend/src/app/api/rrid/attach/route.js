import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

export async function POST(request) {
  try {
    const body = await request.json();

    const backendUrl = `${API_BASE_URL}/rrid/attach`;

    const headers = {
      'Content-Type': 'application/json',
    };
    const authorizationHeader = request.headers.get('Authorization');
    if (authorizationHeader) {
      headers['Authorization'] = authorizationHeader;
    }

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    let data;
    try {
      data = await response.json();
    } catch (parseError) {
      return NextResponse.json(
        { error: 'Invalid response from RRID attach service' },
        { status: 502 }
      );
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('RRID attach proxy error:', error);
    return NextResponse.json(
      { error: 'RRID attach service unavailable' },
      { status: 503 }
    );
  }
}
