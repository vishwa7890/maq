import { MetadataRoute } from 'next'

// This route should be statically generated
export const dynamic = 'force-static'
export const revalidate = 3600 // Revalidate every hour

const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://vilaimathi.mindapt.in';

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ['', '/auth', '/chat', '/dashboard', '/pricing', '/about', '/contact'].map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date().toISOString().split('T')[0],
    changeFrequency: 'weekly' as const,
    priority: route === '' ? 1 : 0.8,
  }));

  return routes;
}
