'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'

export function Navigation() {
  return (
    <header className="sticky top-0 z-40 border-b bg-white/70 backdrop-blur">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" prefetch={true} className="font-semibold tracking-tight text-blue-600">Lumina Quo</Link>
        <nav className="flex items-center gap-3">
          <Link href="/chat" prefetch={true} className="text-sm text-gray-700 hover:text-gray-900">Chat</Link>
          <Link href="/auth" prefetch={true}>
            <Button size="sm" className="px-3">Sign in</Button>
          </Link>
        </nav>
      </div>
    </header>
  )
}
