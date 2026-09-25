import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

async function getUserId(params) {
  const resolvedParams = await params;
  return resolvedParams.id;
}

/**
 * GET - Fetch user profile by user ID
 */
export async function GET(request, { params }) {
  try {
    const id = await getUserId(params);
    const baseUrl = getBackendApiV1BaseUrl();
    const apiUrl = `${baseUrl}/user-profile/${id}`;

    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('authorization') || '',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.message || 'Failed to fetch user profile' },
        { status: response.status }
      );
    }

    const userData = await response.json();

    return NextResponse.json(userData, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, PUT, PATCH, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return NextResponse.json(
      { error: 'Internal server error while fetching user profile' },
      { status: 500 }
    );
  }
}

/**
 * PUT/PATCH - Update user profile fields and/or avatar file
 */
export async function PUT(request, { params }) {
  try {
    const id = await getUserId(params);
    const contentType = request.headers.get('content-type') || '';
    const isMultipart = contentType.includes('multipart/form-data');

    const baseUrl = getBackendApiV1BaseUrl();
    const apiUrl = `${baseUrl}/user-profile/${id}`;
    const headers = {
      Authorization: request.headers.get('authorization') || '',
    };

    let body;
    if (isMultipart) {
      body = await request.formData();
    } else {
      const updateData = await request.json();
      body = JSON.stringify(updateData);
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(apiUrl, {
      method: 'PUT',
      headers,
      body,
    });

    const responseData = await response.json().catch(() => ({}));
    if (!response.ok) {
      return NextResponse.json(
        { error: responseData.message || responseData.error || 'Failed to update user profile' },
        { status: response.status }
      );
    }

    return NextResponse.json(responseData, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, PUT, PATCH, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('Error updating user profile:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error while updating user profile' },
      { status: 500 }
    );
  }
}

export async function PATCH(request, context) {
  return PUT(request, context);
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, PUT, PATCH, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
