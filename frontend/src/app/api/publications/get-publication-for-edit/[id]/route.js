import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

export async function GET(request, { params }) {
  try {
    const { id } = await params;
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('user_id');

    const targetUrl = `${API_BASE_URL}/publications/get-publication-for-edit/${id}${userId ? `?user_id=${userId}` : ''}`;

    const forwardHeaders = { 'Content-Type': 'application/json' };
    const authorizationHeader = request.headers.get('Authorization');
    if (authorizationHeader) forwardHeaders['Authorization'] = authorizationHeader;

    const backendResponse = await fetch(targetUrl, {
      method: 'GET',
      headers: forwardHeaders,
    });

    const responseText = await backendResponse.text();
    let parsed;
    try {
      parsed = JSON.parse(responseText);
    } catch {
      return new NextResponse(responseText, { status: backendResponse.status });
    }
    return NextResponse.json(parsed, { status: backendResponse.status });
  } catch (error) {
    console.error('get-publication-for-edit proxy error:', error);
    return NextResponse.json({ error: 'Proxy error', message: error.message }, { status: 500 });
  }
}
