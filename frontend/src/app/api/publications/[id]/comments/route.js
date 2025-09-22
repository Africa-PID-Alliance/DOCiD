import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://docid.africapidalliance.org/api/v1';

// Comments endpoint doesn't use /v1 in Flask backend, so we need to handle it specially
const COMMENTS_API_URL = API_BASE_URL.replace('/api/v1', '/api');

export async function GET(request, { params }) {
  try {
    const { id } = (await params);

    console.log('Comments API - Using API_BASE_URL:', API_BASE_URL);
    console.log('Comments API - Fetching from:', `${COMMENTS_API_URL}/publications/${id}/comments`);

    // Forward the request to Flask backend
    const response = await fetch(`${COMMENTS_API_URL}/publications/${id}/comments`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.error || 'Failed to fetch comments' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching comments:', error);
    return NextResponse.json(
      {
        error: 'Comments service is temporarily unavailable. Please try again later.',
        code: 'GET_FAILED',
        details: error.message
      },
      { status: 503 }
    );
  }
}

export async function POST(request, { params }) {
  try {
    const { id } = (await params);
    const body = await request.json();

    console.log('Proxying comment POST to:', `${COMMENTS_API_URL}/publications/${id}/comments`);
    console.log('Request body:', body);

    // Forward the request to Flask backend
    const response = await fetch(`${COMMENTS_API_URL}/publications/${id}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('Flask API error:', data);
      return NextResponse.json(
        { error: data.error || 'Failed to post comment' },
        { status: response.status }
      );
    }

    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error('Error posting comment:', error);
    return NextResponse.json(
      {
        error: 'Comments service is temporarily unavailable. Please try again later.',
        code: 'POST_FAILED',
        details: error.message
      },
      { status: 503 }
    );
  }
}