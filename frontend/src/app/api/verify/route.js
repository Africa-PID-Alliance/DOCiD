import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

// Proxy for the public integrity-verification endpoint. Forwards the DOCiD as a
// query parameter so identifiers containing slashes are preserved safely.
export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const identifier = searchParams.get('identifier');

    if (!identifier) {
      return NextResponse.json({ error: 'identifier is required' }, { status: 400 });
    }

    const backendUrl = `${API_BASE_URL}/verify?identifier=${encodeURIComponent(identifier)}`;
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error fetching checksum verification:', error);
    return NextResponse.json(
      {
        error: 'Verification service is temporarily unavailable. Please try again later.',
        code: 'VERIFY_FAILED',
        details: error.message,
      },
      { status: 503 }
    );
  }
}
