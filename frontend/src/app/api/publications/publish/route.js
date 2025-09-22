import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    console.log('=== PUBLICATIONS PUBLISH REQUEST ===');
    console.log('Request URL:', request.url);
    console.log('Content-Type:', request.headers.get('content-type'));
    
    // Get the FormData from the request
    const formData = await request.formData();
    
    console.log('=== FORM DATA ENTRIES ===');
    for (const [key, value] of formData.entries()) {
      if (value instanceof File) {
        console.log(`${key}: [File] ${value.name} (${value.size} bytes, ${value.type})`);
      } else {
        console.log(`${key}: ${value}`);
      }
    }

    // Use environment variable for base URL
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const response = await fetch(`${baseUrl}/publications/publish`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let fetch handle it for FormData
    });

    console.log('=== EXTERNAL API RESPONSE ===');
    console.log('Status:', response.status);
    console.log('Status Text:', response.statusText);
    console.log('Headers:', Object.fromEntries(response.headers.entries()));

    // Get response body
    const responseText = await response.text();
    console.log('Raw Response:', responseText);

    if (!response.ok) {
      console.error(`External API error! status: ${response.status}`);
      console.error('Error body:', responseText);
      
      // Try to parse as JSON for better error handling
      let errorData;
      try {
        errorData = JSON.parse(responseText);
      } catch (e) {
        errorData = { message: responseText };
      }
      
      return NextResponse.json(
        { 
          error: 'Publication submission failed',
          message: errorData.message || 'Unknown error occurred',
          details: errorData
        },
        { 
          status: response.status,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          },
        }
      );
    }

    // Try to parse successful response as JSON
    let data;
    try {
      data = JSON.parse(responseText);
      console.log('=== SUCCESS RESPONSE ===');
      console.log('Parsed JSON:', data);
    } catch (e) {
      console.log('Response is not JSON, returning as text');
      data = { message: responseText };
    }
    
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('=== PUBLICATIONS PUBLISH ERROR ===');
    console.error('Error type:', error.constructor.name);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    
    return NextResponse.json(
      { 
        error: 'Publication submission failed',
        message: 'Server error occurred while processing the request',
        details: error.message
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