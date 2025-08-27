import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const { username, email, password, phone, phone_number, role } = await request.json()

    // Validate required fields
    if (!username || !email || !password) {
      return NextResponse.json(
        { error: 'Username, email, and password are required' },
        { status: 400 }
      )
    }

    // Normalize to backend schema
    const normalizedPhone = phone_number ?? phone ?? ''
    const normalizedRole = (role ?? 'normal').toLowerCase() as 'normal' | 'premium'

    const payload = {
      username,
      email,
      password,
      phone_number: normalizedPhone,
      role: normalizedRole,
    }

    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(payload),
    })

    const data = await res.json()
    const response = NextResponse.json(data, { status: res.status })

    // Extract access_token from backend Set-Cookie and set it on Next.js domain
    const setCookie = res.headers.get('set-cookie') || ''
    const match = /access_token=([^;]+);/i.exec(setCookie)
    if (match && match[1]) {
      response.cookies.set('access_token', decodeURIComponent(match[1]), {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        // secure: true,
        maxAge: 3600,
      })
    }

    return response

  } catch (error) {
    console.error('Registration error:', error)
    return NextResponse.json(
      { error: 'An unexpected error occurred during registration' },
      { status: 500 }
    )
  }
}

