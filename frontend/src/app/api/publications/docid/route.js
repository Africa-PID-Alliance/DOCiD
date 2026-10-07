import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const docid = searchParams.get('docid');

    if (!docid) {
      return NextResponse.json(
        { error: 'docid parameter is required' },
        { status: 400 }
      );
    }

    console.log('Fetching publication with DOCiD:', docid);

    const baseUrl = getBackendApiV1BaseUrl();
    const response = await fetch(`${baseUrl}/publications/docid?docid=${encodeURIComponent(docid)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error(`External API error: ${response.status} ${response.statusText}`);

      // Try to get the error details from the response
      let errorDetails = 'Unknown error';
      try {
        const errorData = await response.json();
        errorDetails = errorData.error || errorData.message || 'Unknown error';
      } catch (e) {
        errorDetails = await response.text();
      }

      return NextResponse.json(
        {
          error: 'External API error',
          status: response.status,
          details: errorDetails,
          message: 'The external API is experiencing issues. This may be a temporary database problem.'
        },
        {
          status: response.status === 500 ? 502 : response.status, // Return 502 Bad Gateway for upstream 500 errors
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          },
        }
      );
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
    console.error('Error fetching publication by DOCiD:', error);
    return NextResponse.json(
      {
        error: 'Proxy error',
        details: error.message,
        message: 'An error occurred while fetching the publication data.'
      },
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

export async function POST(request) {
  try {
    const body = await request.json();
    const response = await fetch(`${getBackendApiV1BaseUrl()}/docids`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization') }
          : {}),
      },
      body: JSON.stringify(body),
    });

    const data = await response.json().catch(() => ({}));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Proxy error', details: error.message },
      { status: 500 },
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
