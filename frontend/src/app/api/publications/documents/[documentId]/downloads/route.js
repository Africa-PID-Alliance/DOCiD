import { NextResponse } from 'next/server';
import axios from 'axios';
import { BACKEND_API_URL } from '@/lib/backendUrl';

export async function POST(request, { params }) {
  const { documentId } = (await params);
  const body = await request.json();

  const fullUrl = `${BACKEND_API_URL}/publications/documents/${documentId}/downloads`;

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
