import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

const empty = { total: 0, offset: 0, limit: 0, source: 'none', institutions: [] };

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const q = (searchParams.get('q') || '').trim();
    const country = (searchParams.get('country') || '').trim();
    const limit = searchParams.get('limit') || '10';

    // Guard: don't fan out to the backend for 0 or 1-character queries.
    if (q.length < 2) {
      return NextResponse.json(empty, { status: 200, headers: corsHeaders });
    }

    const baseUrl = getBackendApiV1BaseUrl();
    const qs = new URLSearchParams({ q, limit });
    if (country) qs.set('country', country);

    const response = await fetch(`${baseUrl}/ringgold/search?${qs.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });

    if (!response.ok) {
      return NextResponse.json(empty, { status: 200, headers: corsHeaders });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200, headers: corsHeaders });
  } catch (error) {
    console.error('Error searching Ringgold institutions:', error);
    return NextResponse.json(empty, { status: 200, headers: corsHeaders });
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 200, headers: corsHeaders });
}
