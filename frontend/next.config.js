/** @type {import('next').NextConfig} */
const remoteImageHosts = (process.env.NEXT_IMAGE_REMOTE_HOSTS || 'localhost')
  .split(',')
  .map((host) => host.trim())
  .filter(Boolean);

const nextConfig = {
  output: 'standalone',
  distDir: '.next',
  reactStrictMode: true,
  // For these bot user-agents, render <head> metadata BLOCKING (no streaming
  // via RSC). Default Next 15.4+ behavior is to stream metadata, which means
  // crawlers that don't run JS see an empty <head>. Google Scholar's crawler
  // and many academic indexers fall in that bucket. The regex matches their
  // UAs; for everyone else (real browsers) metadata still streams.
  // See https://nextjs.org/docs/app/api-reference/config/next-config-js/htmlLimitedBots
  htmlLimitedBots:
    /Mediapartners-Google|Googlebot|Googlebot-Mobile|Googlebot-Image|Googlebot-News|Googlebot-Video|AdsBot-Google|AdsBot-Google-Mobile|Mediapartners|Storebot-Google|Google-Site-Verification|Google-InspectionTool|GoogleOther|Google-Read-Aloud|Google-CloudVertexBot|Bingbot|Slurp|DuckDuckBot|Baiduspider|YandexBot|Sogou|Exabot|facebot|facebookexternalhit|LinkedInBot|Discordbot|TwitterBot|Twitterbot|Applebot|Bot|bot|spider|crawler|Scholar/i,
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