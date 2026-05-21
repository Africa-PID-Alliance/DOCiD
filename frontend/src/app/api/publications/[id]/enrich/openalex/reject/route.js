import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

export async function POST(request, { params }) {
  try {
    const { id } = await params;
    const targetUrl = `${API_BASE_URL}/publications/${id}/enrich/openalex/reject`;

    const forwardHeaders = { 'Content-Type': 'application/json' };
    const authorizationHeader = request.headers.get('Authorization');
    if (authorizationHeader) forwardHeaders['Authorization'] = authorizationHeader;

    const body = await request.text();

    const backendResponse = await fetch(targetUrl, {
      method: 'POST',
      headers: forwardHeaders,
      body: body || undefined,
    });

    const responseText = await backendResponse.text();
    let parsed;
    try { parsed = JSON.parse(responseText); }
    catch { return new NextResponse(responseText, { status: backendResponse.status }); }
    return NextResponse.json(parsed, { status: backendResponse.status });
  } catch (error) {
    console.error('enrich/openalex/reject proxy error:', error);
    return NextResponse.json({ error: 'Proxy error', message: error.message }, { status: 500 });
  }
}
