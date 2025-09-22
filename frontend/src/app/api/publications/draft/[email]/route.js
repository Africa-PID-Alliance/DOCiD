import { NextResponse } from 'next/server';

export async function GET(request, { params }) {
  try {
    const { email } = params;
    
    console.log('=== DRAFT GET REQUEST ===');
    console.log('Email:', email);
    
    // Use environment variable for base URL
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const response = await fetch(`${baseUrl}/publications/draft/${encodeURIComponent(email)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('=== EXTERNAL API RESPONSE ===');
    console.log('Status:', response.status);
    console.log('Status Text:', response.statusText);

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
          error: 'Draft retrieval failed',
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
    let responseData;
    try {
      responseData = JSON.parse(responseText);
      console.log('=== SUCCESS RESPONSE ===');
      console.log('Parsed JSON:', responseData);
    } catch (e) {
      console.log('Response is not JSON, returning as text');
      responseData = { message: responseText };
    }
    
    return NextResponse.json(responseData, {
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('=== DRAFT GET ERROR ===');
    console.error('Error type:', error.constructor.name);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    
    return NextResponse.json(
      { 
        error: 'Draft retrieval failed',
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

export async function DELETE(request, { params }) {
  try {
    const { email } = params;
    
    console.log('=== DRAFT DELETE REQUEST ===');
    console.log('Email:', email);
    
    // Use environment variable for base URL
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const response = await fetch(`${baseUrl}/publications/draft/${encodeURIComponent(email)}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('=== EXTERNAL API RESPONSE ===');
    console.log('Status:', response.status);
    console.log('Status Text:', response.statusText);

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
          error: 'Draft deletion failed',
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
    let responseData;
    try {
      responseData = JSON.parse(responseText);
      console.log('=== SUCCESS RESPONSE ===');
      console.log('Parsed JSON:', responseData);
    } catch (e) {
      console.log('Response is not JSON, returning as text');
      responseData = { message: responseText };
    }
    
    return NextResponse.json(responseData, {
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('=== DRAFT DELETE ERROR ===');
    console.error('Error type:', error.constructor.name);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    
    return NextResponse.json(
      { 
        error: 'Draft deletion failed',
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