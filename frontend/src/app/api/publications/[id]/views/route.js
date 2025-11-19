import { NextResponse } from 'next/server';
import axios from 'axios';

const ANALYTICS_API_URL = process.env.BACKEND_API_URL || 'http://localhost:5001/api';

export async function POST(request, { params }) {
  const { id } = (await params);
  const body = await request.json();

  try {
    const response = await axios.post(
      `${ANALYTICS_API_URL}/publications/${id}/views`,
      body,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    return NextResponse.json(response.data, { status: 201 });
  } catch (error) {
    console.error('Error tracking view:', error);

    if (error.response) {
      return NextResponse.json(
        error.response.data || { error: 'Failed to track view' },
        { status: error.response.status }
      );
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request, { params }) {
  const { id } = (await params);

  try {
    const response = await axios.get(
      `${ANALYTICS_API_URL}/publications/${id}/views/count`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    return NextResponse.json(response.data);
  } catch (error) {
    console.error('Error fetching view count:', error);

    if (error.response) {
      return NextResponse.json(
        { error: 'Failed to fetch view count' },
        { status: error.response.status }
      );
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
