import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const searchQuery = searchParams.get('q') || '';
    const country = searchParams.get('country') || '';
    const page = searchParams.get('page') || '1';
    const perPage = searchParams.get('per_page') || '20';

    const baseUrl = getBackendApiV1BaseUrl();

    let apiUrl = `${baseUrl}/national-id/researchers/search?q=${encodeURIComponent(searchQuery)}&page=${encodeURIComponent(page)}&per_page=${encodeURIComponent(perPage)}`;

    if (country) {
      apiUrl += `&country=${encodeURIComponent(country)}`;
    }

    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
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
    console.error('Error searching National ID researchers:', error);
    return NextResponse.json(
      { error: 'Failed to search National ID researchers', message: error.message },
      {
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      }
    );
  }
}

export async function OPTIONS(request) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
