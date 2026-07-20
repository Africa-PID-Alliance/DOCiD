import { NextResponse } from 'next/server';

const AUTHENTICATION_EXEMPT_POST_ROUTES = new Set([
  '/api/auth/login',
  '/api/auth/initiate-registration',
  '/api/auth/complete-registration',
  '/api/auth/request-reset-password',
  '/api/auth/reset-password',
  '/api/auth/refresh',
]);

const JWT_REQUIRED_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function hasBearerToken(request) {
  const authorization = request.headers.get('authorization');
  return /^Bearer\s+\S+$/i.test(authorization || '');
}

export function middleware(request) {
  const url = request.nextUrl.clone();
  const { pathname } = url;

  // All state-changing frontend API routes require the JWT issued at login.
  // Authentication bootstrap routes are the only exceptions because no login
  // token exists yet (refresh authenticates with its refresh JWT).
  if (
    pathname.startsWith('/api/') &&
    JWT_REQUIRED_METHODS.has(request.method) &&
    !AUTHENTICATION_EXEMPT_POST_ROUTES.has(pathname) &&
    !hasBearerToken(request)
  ) {
    return NextResponse.json(
      { error: 'Authentication required' },
      { status: 401 }
    );
  }

  // Canonicalize DOCiD URLs to the slash form for Google Scholar crawlability.
  // /docid/<prefix>%2F<suffix>  ->  /docid/<prefix>/<suffix>  (301)
  if (pathname.startsWith('/docid/') && pathname.includes('%2F')) {
    const decodedPathname = pathname.replace(/%2F/gi, '/');
    if (decodedPathname !== pathname) {
      url.pathname = decodedPathname;
      return NextResponse.redirect(url, 301);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/docid/:path*',
    '/api/:path*',
  ],
};
