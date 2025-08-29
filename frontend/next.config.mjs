/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export for drag-and-drop deployments (generates `out/`)
  output: 'export',
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  experimental: {
    optimizeCss: true
  },
  images: {
    domains: ['localhost'],
    unoptimized: true
  },
  // Enable gzip compression
  compress: true
}

export default nextConfig
