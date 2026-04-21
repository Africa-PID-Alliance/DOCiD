import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

/**
 * GET - Fetch user publications with pagination
 */
export async function GET(request, { params }) {
  try {
    const { id } = params;
    const { searchParams } = new URL(request.url);

    // Get pagination and sorting parameters
    const page = searchParams.get('page') || '1';
    const pageSize = searchParams.get('page_size') || '10';
    const sort = searchParams.get('sort') || 'published';
    const order = searchParams.get('order') || 'desc';

    const baseUrl = getBackendApiV1BaseUrl();
    const queryParams = new URLSearchParams({
      page,
      page_size: pageSize,
      sort,
      order
    });

    const apiUrl = `${baseUrl}/user-profile/${id}/publications?${queryParams.toString()}`;

    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.message || 'Failed to fetch user publications' },
        { status: response.status }
      );
    }

    const publicationsData = await response.json();

    return NextResponse.json(publicationsData, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('Error fetching user publications:', error);
    return NextResponse.json(
      { error: 'Internal server error while fetching user publications' },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
