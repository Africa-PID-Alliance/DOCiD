import { NextResponse } from 'next/server';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const token = searchParams.get('token');

    if (!token) {
      return NextResponse.json(
        { status: false, message: 'Token is required' },
        { status: 400 }
      );
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const response = await fetch(`${baseUrl}/auth/verify-registration-token/${token}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error verifying registration token:', error);
    return NextResponse.json(
      { status: false, message: 'Failed to verify token' },
      { status: 500 }
    );
  }
}
