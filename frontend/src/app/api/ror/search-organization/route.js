import { NextResponse } from 'next/server';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const name = searchParams.get('name');
    const country = searchParams.get('country');
    const page = searchParams.get('page') || '1';
    
    if (!name) {
      return NextResponse.json(
        { error: 'Organization name parameter (name) is required' },
        { status: 400 }
      );
    }

    // Use environment variable for base URL
    const baseUrl = process.env.REACT_APP_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

    // Build query parameters with separate name and country
    const queryParams = new URLSearchParams({
      name: name,
      page: page
    });

    // Only add country if provided
    if (country) {
      queryParams.append('country', country);
    }

    const response = await fetch(`${baseUrl}/ror/search-organization?${queryParams.toString()}`, {
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
    console.error('Error searching ROR organizations:', error);
    return NextResponse.json(
      { error: 'Failed to search organizations', message: error.message },
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