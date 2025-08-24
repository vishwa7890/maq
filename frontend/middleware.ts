import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Get user data from localStorage would be handled client-side
  // This middleware would typically check JWT tokens or session cookies
  
  const { pathname } = request.nextUrl

  // Protect dashboard route - only for premium users
  if (pathname.startsWith('/dashboard')) {
    // In a real app, you'd verify the user's role from a secure token
    // For now, we'll let the client-side handle this redirect
    return NextResponse.next()
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*']
}
