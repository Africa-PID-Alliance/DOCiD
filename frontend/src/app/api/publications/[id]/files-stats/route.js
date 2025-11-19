import { NextResponse } from 'next/server';
import axios from 'axios';

const ANALYTICS_API_URL = process.env.BACKEND_API_URL || 'http://localhost:5001/api';

export async function GET(request, { params }) {
  const { id } = (await params);

  try {
    const response = await axios.get(
      `${ANALYTICS_API_URL}/publications/${id}/files-stats`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    return NextResponse.json(response.data);
  } catch (error) {
    console.error('Error fetching files statistics:', error);

    if (error.response) {
      return NextResponse.json(
        { error: 'Failed to fetch files statistics' },
        { status: error.response.status }
      );
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
