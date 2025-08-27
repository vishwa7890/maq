import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/api'

export async function GET(request: NextRequest) {
  try {
    // Ensure we forward the access_token cookie even if not present in raw header
    const incomingCookieHeader = request.headers.get('cookie') || ''
    const token = request.cookies.get('access_token')?.value
    let forwardCookie = incomingCookieHeader
    if (token && !incomingCookieHeader.includes('access_token=')) {
      forwardCookie = forwardCookie
        ? `${forwardCookie}; access_token=${token}`
        : `access_token=${token}`
    }

    const res = await fetch(`${API_BASE}/auth/me`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        // Forward cookies to backend for auth
        Cookie: forwardCookie,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: 'include',
    })

    const contentType = res.headers.get('content-type') || ''
    const data = contentType.includes('application/json') ? await res.json() : await res.text()

    return NextResponse.json(data, { status: res.status })
  } catch (e) {
    return NextResponse.json({ error: 'Failed to fetch user' }, { status: 500 })
  }
}
