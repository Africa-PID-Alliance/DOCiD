import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;

// Catch-all proxy for publication edit routes.
// Maps /api/publications/<id>/edit/<...slug> → <API_BASE>/publications/<id>/<...slug>
async function handle(request, { params }) {
  const resolvedParams = await params;
  const publicationId = resolvedParams.id;
  const slugParts = Array.isArray(resolvedParams.slug) ? resolvedParams.slug : [resolvedParams.slug];
  const targetUrl = `${API_BASE_URL}/publications/${publicationId}/${slugParts.join('/')}`;

  const requestHeaders = {};
  const authorizationHeader = request.headers.get('Authorization');
  if (authorizationHeader) requestHeaders['Authorization'] = authorizationHeader;

  const contentType = request.headers.get('Content-Type') || '';
  let fetchBody = undefined;

  if (!['GET', 'DELETE'].includes(request.method)) {
    if (contentType.includes('multipart/form-data')) {
      // For multipart uploads, pass through the original FormData
      fetchBody = await request.formData();
      // Let fetch set the boundary
    } else {
      const rawBody = await request.text();
      if (rawBody) {
        fetchBody = rawBody;
        requestHeaders['Content-Type'] = contentType || 'application/json';
      }
    }
  }

  // DELETE with body support (frontend sends user_id in JSON body)
  if (request.method === 'DELETE') {
    const rawBody = await request.text().catch(() => '');
    if (rawBody) {
      fetchBody = rawBody;
      requestHeaders['Content-Type'] = contentType || 'application/json';
    }
  }

  const backendResponse = await fetch(targetUrl, {
    method: request.method,
    headers: requestHeaders,
    body: fetchBody,
  });

  const responseText = await backendResponse.text();
  let parsedJson;
  try {
    parsedJson = JSON.parse(responseText);
  } catch {
    return new NextResponse(responseText, {
      status: backendResponse.status,
      headers: { 'Content-Type': backendResponse.headers.get('Content-Type') || 'text/plain' },
    });
  }
  return NextResponse.json(parsedJson, { status: backendResponse.status });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const DELETE = handle;
