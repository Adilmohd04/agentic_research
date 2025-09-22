// Load environment variables from root .env file
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Disable static generation completely
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: path.join(__dirname, '../'),
    missingSuspenseWithCSRBailout: false,
  },
  // Force dynamic rendering
  generateStaticParams: false,
  dynamicParams: true,
  // Performance optimizations
  experimental: {
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },
  // Simple webpack config
  webpack: (config) => {
    return config;
  },
}

module.exports = nextConfig