import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navigation } from '@/components/navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'VilaiMathi AI - Business Quotation Assistant',
    template: '%s | VilaiMathi AI'
  },
  description: 'Generate professional business quotations in seconds with AI. Export to PDF/Word, customize templates, and impress your clients with VilaiMathi AI.',
  keywords: ['business quotation', 'AI quotation generator', 'professional quotes', 'PDF export', 'business proposals', 'invoice generator'],
  authors: [{ name: 'VilaiMathi AI Team' }],
  creator: 'VilaiMathi AI',
  publisher: 'VilaiMathi AI',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://vilaimathi.mindapt.in'),
  openGraph: {
    title: 'VilaiMathi AI - Business Quotation Assistant',
    description: 'Generate professional business quotations in seconds with AI. Export to PDF/Word and impress your clients.',
    url: 'https://vilaimathi.mindapt.in',
    siteName: 'VilaiMathi AI',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'VilaiMathi AI - Business Quotation Assistant',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'VilaiMathi AI - Business Quotation Assistant',
    description: 'Generate professional business quotations in seconds with AI',
    creator: '@VilaiMathiAI',
    images: ['/twitter-image.jpg'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  alternates: {
    canonical: '/',
  },
  generator: 'Next.js',
  applicationName: 'VilaiMathi AI',
  referrer: 'origin-when-cross-origin',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        {/* Basic meta tags */}
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        
        {/* Theme color */}
        <meta name="theme-color" content="#ffffff" />
        
        {/* Icons */}
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" type="image/png" sizes="32x32" href="/icons/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/icons/favicon-16x16.png" />
      </head>
      <body className={`${inter.className} flex flex-col min-h-screen`}>
        <Navigation />
        <main className="flex-grow">
          {children}
        </main>
      </body>
    </html>
  )
}
