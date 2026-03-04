import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

export async function GET(request, { params }) {
  try {
    const { projectId } = await params;
    const backendUrl = `${API_BASE_URL}/localcontexts/projects/${projectId}`;

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
        { error: 'Invalid response from Local Contexts API' },
        { status: 502 }
      );
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Local Contexts project proxy error:', error);
    return NextResponse.json(
      { error: 'Local Contexts service unavailable' },
      { status: 503 }
    );
  }
}
