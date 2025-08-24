import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/api'

export async function GET(request: NextRequest) {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        // Forward cookies to backend for auth
        Cookie: request.headers.get('cookie') || '',
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
