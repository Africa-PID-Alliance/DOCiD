import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    
    // Build the query string from the search parameters
    const queryString = searchParams.toString();
    const baseUrl = getBackendApiV1BaseUrl();
    const apiUrl = `${baseUrl}/publications/get-publications${queryString ? `?${queryString}` : ''}`;
    
    const forwardedHeaders = {
      'Content-Type': 'application/json',
    };
    const incomingAuth = request.headers.get('authorization');
    if (incomingAuth) {
      forwardedHeaders['Authorization'] = incomingAuth;
    }

    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: forwardedHeaders,
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
    console.error('Error fetching publications:', error);
    return NextResponse.json(
      { error: 'Failed to fetch publications' },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
} 