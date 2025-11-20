import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request, { params }) {
  const { documentId } = (await params);
  const body = await request.json();

  const baseUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:5001/api';
  const fullUrl = `${baseUrl}/publications/documents/${documentId}/downloads`;

  console.log('[DEBUG] Using axios - Base URL:', baseUrl);
  console.log('[DEBUG] Using axios - Full URL:', fullUrl);

  try {
    const response = await axios.post(fullUrl, body, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return NextResponse.json(response.data, { status: response.status });
  } catch (error) {
    console.error('Error tracking document download:', error.message);
    if (error.response) {
      return NextResponse.json(error.response.data, { status: error.response.status });
    }
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
