import { NextResponse } from 'next/server';

const ANALYTICS_API_URL = process.env.BACKEND_API_URL || 'http://localhost:5001/api';

export async function POST(request, { params }) {
  const { id } = (await params);
  const body = await request.json();

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/publications/${id}/views`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error('Error tracking view:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request, { params }) {
  const { id } = (await params);

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/publications/${id}/views/count`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch view count' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching view count:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
