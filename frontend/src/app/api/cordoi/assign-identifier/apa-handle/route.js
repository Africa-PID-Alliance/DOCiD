import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    // Get the request body (though it might be empty for APA Handle)
    const body = await request.text();
    const requestBody = body ? JSON.parse(body) : {};
    
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const response = await fetch(`${baseUrl}/cordoi/assign-identifier/apa-handle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('authorization'),
        'Idempotency-Key': request.headers.get('idempotency-key'),
      },
      body: JSON.stringify(requestBody),
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
      },
    });
  } catch (error) {
    console.error('Error generating APA Handle ID:', error);
    return NextResponse.json(
      { error: 'Failed to generate APA Handle ID' },
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
