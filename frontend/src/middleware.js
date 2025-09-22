import { NextResponse } from 'next/server';

export function middleware(request) {
  const url = request.nextUrl.clone();
  const { pathname } = url;

  // Check if the URL is a DOCiD URL pattern (matches the pattern used by DOCiD)
  if (pathname.startsWith('/docid/')) {
    // Regular expression to match DOCiD patterns with unencoded forward slashes
    // This handles both 20.500.14351/ pattern and any potential future patterns
    const docidRegex = /\/docid\/(\d+(?:\.\d+)+)\/([^\/]+)/;
    
    if (docidRegex.test(pathname)) {
      // Replace unencoded forward slash with encoded one
      const encodedPathname = pathname.replace(docidRegex, '/docid/$1%2F$2');

      // Only redirect if the URL was actually changed
      if (encodedPathname !== pathname) {
        console.log(`Redirecting from ${pathname} to ${encodedPathname}`);
        url.pathname = encodedPathname;
        return NextResponse.redirect(url);
      }
    }
  }

  return NextResponse.next();
}

// Only run middleware on specific paths
export const config = {
  matcher: [
    '/docid/:path*',
  ],
};
