/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: '.next',
  reactStrictMode: true,
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
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