import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function POST(request) {
  try {
    const body = await request.json();
    const backendLoginUrl = `${getBackendApiV1BaseUrl()}/auth/login`;
    const backendResponse = await fetch(backendLoginUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const rawResponseBody = await backendResponse.text();
    let parsedResponseBody;
    try {
      parsedResponseBody = rawResponseBody ? JSON.parse(rawResponseBody) : {};
    } catch {
      // Backend returned non-JSON (nginx 502 page, proxy timeout, ...).
      // Pass the real status through instead of masking it as a 500.
      console.error(
        `[login] non-JSON response from backend (status ${backendResponse.status})`,
      );
      parsedResponseBody = { error: 'Login service is unavailable' };
    }

    if (!backendResponse.ok) {
      console.error(`[login] backend rejected login with status ${backendResponse.status}`);
    }

    return NextResponse.json(parsedResponseBody, { status: backendResponse.status });
  } catch (error) {
    console.error('[login] request failed:', error.message);
    return NextResponse.json(
      { error: 'Failed to login', details: error.message },
      { status: 500 },
    );
  }
}
