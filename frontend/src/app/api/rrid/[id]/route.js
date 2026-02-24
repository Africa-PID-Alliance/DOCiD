import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

export async function DELETE(request, { params }) {
  try {
    const { id } = await params;

    const backendUrl = `${API_BASE_URL}/rrid/${id}`;

    const headers = {
      'Content-Type': 'application/json',
    };
    const authorizationHeader = request.headers.get('Authorization');
    if (authorizationHeader) {
      headers['Authorization'] = authorizationHeader;
    }

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers,
    });

    let data;
    try {
      data = await response.json();
    } catch (parseError) {
      return NextResponse.json(
        { error: 'Invalid response from RRID delete service' },
        { status: 502 }
      );
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('RRID delete proxy error:', error);
    return NextResponse.json(
      { error: 'RRID delete service unavailable' },
      { status: 503 }
    );
  }
}
