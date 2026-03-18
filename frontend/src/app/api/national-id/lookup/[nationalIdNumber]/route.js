import { NextResponse } from 'next/server';

export async function GET(request, { params }) {
  try {
    const { nationalIdNumber } = await params;

    if (!nationalIdNumber) {
      return NextResponse.json(
        { error: 'National ID Number is required' },
        { status: 400 }
      );
    }

    const { searchParams } = new URL(request.url);
    const country = searchParams.get('country') || '';

    const baseUrl = process.env.REACT_APP_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

    let apiUrl = `${baseUrl}/national-id/researchers/lookup/${encodeURIComponent(nationalIdNumber)}`;
    if (country) {
      apiUrl += `?country=${encodeURIComponent(country)}`;
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
    console.error('Error looking up National ID researcher:', error);
    return NextResponse.json(
      { error: 'Failed to lookup researcher', message: error.message },
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
