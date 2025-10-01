import { MetadataRoute } from 'next'

// This route should be statically generated
export const dynamic = 'force-static'
export const revalidate = 3600 // Revalidate every hour

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://vilaimathi.mindapt.in';
  
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/api/', '/_next/', '/*/edit/', '/*?*'],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
