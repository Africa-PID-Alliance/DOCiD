import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function GET(request) {
  try {
    const baseUrl = getBackendApiV1BaseUrl();

    // Forward the caller's Authorization only when present, so the backend can
    // filter the list to the account's category. Do not send a null-valued header.
    const upstreamHeaders = { 'Content-Type': 'application/json' };
    const authorization = request.headers.get('authorization');
    if (authorization) {
      upstreamHeaders['Authorization'] = authorization;
    }

    const response = await fetch(`${baseUrl}/publications/get-list-resource-types`, {
      method: 'GET',
      headers: upstreamHeaders,
      // The response is per-account (filtered by category), so it must never be
      // reused across users by any framework/CDN cache.
      cache: 'no-store',
    });

    if (!response.ok) {
      // Forward the upstream status and message. Collapsing every failure
      // into a generic 500 hides actionable causes (401 expired token,
      // 403 not authorized, 429 rate limited) and, on mint routes, invites
      // retries that each create a real PID.
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
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        // Per-account response: prevent cross-category cache reuse.
        'Cache-Control': 'no-store',
        'Vary': 'Authorization',
      },
    });
  } catch (error) {
    console.error('Error fetching resource types:', error);
    return NextResponse.json(
      { error: 'Failed to fetch resource types' },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
} 