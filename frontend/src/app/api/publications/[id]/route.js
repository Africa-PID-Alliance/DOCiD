import { NextResponse } from 'next/server';

const ANALYTICS_API_URL = process.env.BACKEND_API_URL || 'http://127.0.0.1:6000/api';

export async function GET(request, { params }) {
  const { id } = (await params);

  try {
    const response = await fetch(`${ANALYTICS_API_URL}/publications/${id}/files-stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch files statistics' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching files statistics:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
