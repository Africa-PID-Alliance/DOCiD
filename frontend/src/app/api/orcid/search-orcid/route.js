import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const firstName = searchParams.get('first_name');
    const lastName = searchParams.get('last_name');
    const affiliations = searchParams.get('affiliations');
    
    if (!firstName || !lastName) {
      return NextResponse.json(
        { error: 'Both first_name and last_name parameters are required' },
        { status: 400 }
      );
    }

    // Use environment variable for base URL
    const baseUrl = getBackendApiV1BaseUrl();
    
    // Build the external API URL with parameters
    let apiUrl = `${baseUrl}/orcid/search-orcid?first_name=${encodeURIComponent(firstName)}&last_name=${encodeURIComponent(lastName)}`;
    
    if (affiliations) {
      apiUrl += `&affiliations=${encodeURIComponent(affiliations)}`;
    }

    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      // Forward the upstream status and message. Collapsing every failure
      // into a generic 500 hides actionable causes (401 expired token,
      // 403 not authorized, 429 rate limited) and, on mint routes, invites
      // retries that each create a real PID.
      const upstreamText = await response.text();
      let upstreamBody;
      try {
        upstreamBody = JSON.parse(upstreamText);
      } catch {
        upstreamBody = { error: upstreamText || response.statusText };
      }
      return NextResponse.json(upstreamBody, { status: response.status });
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
    console.error('Error searching ORCID:', error);
    return NextResponse.json(
      { error: 'Failed to search ORCID', message: error.message },
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