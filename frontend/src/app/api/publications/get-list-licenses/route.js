import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

// Proxy for the licence catalogue and the current rights declaration text.
// GET <API_BASE>/publications/get-list-licenses
// -> { licenses: [{ id, code, short_name, name, url, ... }], rights_declaration: { version, text } }
export async function GET(request) {
  try {
    const baseUrl = getBackendApiV1BaseUrl();

    // Forward the caller's Authorization only when present.
    const upstreamHeaders = { 'Content-Type': 'application/json' };
    const authorization = request.headers.get('authorization');
    if (authorization) {
      upstreamHeaders['Authorization'] = authorization;
    }

    const response = await fetch(`${baseUrl}/publications/get-list-licenses`, {
      method: 'GET',
      headers: upstreamHeaders,
      cache: 'no-store',
    });

    if (!response.ok) {
      // Forward the upstream status and message rather than a generic 500.
      const upstreamText = await response.text();
      let upstreamBody;
      try {
        upstreamBody = JSON.parse(upstreamText);
      } catch {
        upstreamBody = { error: upstreamText || response.statusText };
      }
      return NextResponse.json(upstreamBody, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, {
      status: 200,
      headers: { 'Cache-Control': 'no-store' },
    });
  } catch (error) {
    console.error('Error fetching licences:', error);
    return NextResponse.json(
      { error: 'Failed to fetch licences', detail: String(error?.message || error) },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
