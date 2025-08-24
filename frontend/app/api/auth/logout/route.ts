import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        Cookie: request.headers.get('cookie') || '',
      },
      credentials: 'include',
    })

    const contentType = res.headers.get('content-type') || ''
    const data = contentType.includes('application/json') ? await res.json() : await res.text()
    const response = NextResponse.json(
      typeof data === 'string' ? { message: data } : data,
      { status: res.status }
    )
    // Proactively clear the cookie on Next.js domain as well
    response.cookies.delete('access_token')
    return response
  } catch (e) {
    return NextResponse.json({ error: 'Failed to logout' }, { status: 500 })
  }
}

// Optional: allow GET to logout as well for convenience
export async function GET(request: NextRequest) {
  return POST(request)
}

