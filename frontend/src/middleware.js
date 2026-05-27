import { NextResponse } from 'next/server';

export function middleware(request) {
  const url = request.nextUrl.clone();
  const { pathname } = url;

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
  ],
};
