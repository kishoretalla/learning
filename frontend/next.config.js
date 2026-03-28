/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    return [
      {
        source: '/api/auth/:path*',
        destination: `${backendUrl}/api/auth/:path*`,
      },
      {
        source: '/api/history/:path*',
        destination: `${backendUrl}/api/history/:path*`,
      },
      {
        source: '/api/extract-text',
        destination: `${backendUrl}/api/extract-text`,
      },
      {
        source: '/api/generate-notebook',
        destination: `${backendUrl}/api/generate-notebook`,
      },
      {
        source: '/api/export-markdown',
        destination: `${backendUrl}/api/export-markdown`,
      },
      {
        source: '/api/create-colab-link',
        destination: `${backendUrl}/api/create-colab-link`,
      },
      {
        source: '/api/arxiv-url',
        destination: `${backendUrl}/api/arxiv-url`,
      },
      {
        source: '/api/demo-papers',
        destination: `${backendUrl}/api/demo-papers`,
      },
      {
        source: '/api/demo-papers/:path*',
        destination: `${backendUrl}/api/demo-papers/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
