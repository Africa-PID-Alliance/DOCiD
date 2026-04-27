import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function PUT(request) {
  try {
    const body = await request.json();
    const authorization = request.headers.get('authorization');

    if (!authorization) {
      return NextResponse.json(
        { error: 'Authorization header is required' },
        { status: 401 }
      );
    }

    const baseUrl = getBackendApiV1BaseUrl();
    const apiUrl = `${baseUrl}/user-profile/me/logo`;

    const response = await fetch(apiUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authorization,
      },
      body: JSON.stringify(body),
    });

    const responseData = await response.json().catch(() => ({}));
    if (!response.ok) {
      return NextResponse.json(
        { error: responseData.message || responseData.error || 'Failed to update logo' },
        { status: response.status }
      );
    }

    return NextResponse.json(responseData, { status: 200 });
  } catch (error) {
    console.error('Error updating user logo:', error);
    return NextResponse.json(
      { error: 'Internal server error while updating user logo' },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
