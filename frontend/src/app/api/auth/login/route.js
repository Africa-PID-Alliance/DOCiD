import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function POST(request) {
  try {
    const body = await request.json();
    const response = await fetch(`${getBackendApiV1BaseUrl()}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await response.json().catch(() => ({}));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to login', details: error.message },
      { status: 500 },
    );
  }
}
