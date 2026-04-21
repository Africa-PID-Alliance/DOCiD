/** @type {import('next').NextConfig} */
const remoteImageHosts = (process.env.NEXT_IMAGE_REMOTE_HOSTS || 'localhost')
  .split(',')
  .map((host) => host.trim())
  .filter(Boolean);

const nextConfig = {
  output: 'standalone',
  distDir: '.next',
  reactStrictMode: true,
  images: {
    remotePatterns: remoteImageHosts.flatMap((hostname) => ([
      { protocol: 'https', hostname },
      { protocol: 'http', hostname },
    ])),
  },
  async rewrites() {
    return [
      {
        // Keep browser traffic same-origin while serving backend uploads.
        source: '/uploads/:path*',
        destination: `${process.env.BACKEND_UPLOAD_ORIGIN || 'http://backend:5001'}/uploads/:path*`,
      },
      {
        // Properly handle DOCiD identifiers with slashes
        source: '/docid/:slug*',
        destination: '/docid/:slug*',
      },
    ];
  },
  // Use this to handle special characters in URL paths
  trailingSlash: false,
};

module.exports = nextConfig;