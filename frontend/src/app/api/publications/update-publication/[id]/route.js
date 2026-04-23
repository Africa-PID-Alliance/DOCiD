import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

export async function PUT(request, { params }) {
  try {
    const { id } = await params;
    const targetUrl = `${API_BASE_URL}/publications/update-publication/${id}`;

    const forwardHeaders = {};
    const authorizationHeader = request.headers.get('Authorization');
    if (authorizationHeader) forwardHeaders['Authorization'] = authorizationHeader;

    const contentType = request.headers.get('Content-Type') || '';
    let fetchBody;
    if (contentType.includes('multipart/form-data')) {
      fetchBody = await request.formData();
      // Don't set Content-Type; fetch sets it with the right boundary
    } else {
      const raw = await request.text();
      fetchBody = raw;
      forwardHeaders['Content-Type'] = contentType || 'application/json';
    }

    const backendResponse = await fetch(targetUrl, {
      method: 'PUT',
      headers: forwardHeaders,
      body: fetchBody,
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
    console.error('update-publication proxy error:', error);
    return NextResponse.json({ error: 'Proxy error', message: error.message }, { status: 500 });
  }
}
