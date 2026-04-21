import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function GET(_request, { params }) {
  try {
    const { email } = params;
    const response = await fetch(
      `${getBackendApiV1BaseUrl()}/auth/user/email/${encodeURIComponent(email)}`,
      { method: 'GET', headers: { 'Content-Type': 'application/json' } },
    );

    const data = await response.json().catch(() => ({}));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch user by email', details: error.message },
      { status: 500 },
    );
  }
}
