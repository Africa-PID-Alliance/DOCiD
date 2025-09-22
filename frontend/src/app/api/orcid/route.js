import { NextResponse } from 'next/server';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const orcidId = searchParams.get('orcidId');
  const accessToken = searchParams.get('accessToken');

  if (!orcidId || !accessToken) {
    return NextResponse.json({ error: 'Missing required parameters' }, { status: 400 });
  }

  try {
    const response = await fetch(`https://sandbox.orcid.org/v3.0/${orcidId}/person`, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch ORCID data');
    }

    const data = await response.json();
    console.log("ORCID DATA", data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching ORCID data:', error);
    return NextResponse.json({ error: 'Failed to fetch ORCID data' }, { status: 500 });
  }
} 