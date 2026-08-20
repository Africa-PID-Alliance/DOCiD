import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function POST(request) {
  try {
    const body = await request.json();
    const targetUrl = `${getBackendApiV1BaseUrl()}/auth/login`;
    console.log('[login-debug] target URL:', targetUrl);
    console.log('[login-debug] request email:', body.email, 'password length:', (body.password || '').length);
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const rawText = await response.text();
    console.log('[login-debug] backend status:', response.status);
    console.log('[login-debug] backend raw body:', rawText);
    const data = rawText ? JSON.parse(rawText) : {};
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('[login-debug] error:', error);
    return NextResponse.json(
      { error: 'Failed to login', details: error.message },
      { status: 500 },
    );
  }
}
