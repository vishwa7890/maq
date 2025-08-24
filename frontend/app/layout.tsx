import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Lumina Quo - Business Quotation Assistant',
  description: 'AI-powered business quotation generator with role-based features',
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <header className="sticky top-0 z-40 border-b bg-white/70 backdrop-blur">
          <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
            <Link href="/" className="font-semibold tracking-tight text-blue-600">Lumina Quo</Link>
            <nav className="flex items-center gap-3">
              <Link href="/chat" className="text-sm text-gray-700 hover:text-gray-900">Chat</Link>
              <Link href="/auth">
                <Button size="sm" className="px-3">Sign in</Button>
              </Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  )
}
