import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const { username, password } = await request.json()
    
    if (!username || !password) {
      return NextResponse.json(
        { error: 'Username and password are required' },
        { status: 400 }
      )
    }

    const form = new URLSearchParams()
    form.set('username', username)
    form.set('password', password)

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      credentials: 'include',
      body: form.toString(),
    })

    const data = await res.json()
    const response = NextResponse.json(data, { status: res.status })

    // Extract access_token from backend Set-Cookie and set it on Next.js domain
    const setCookie = res.headers.get('set-cookie') || ''
    const match = /access_token=([^;]+);/i.exec(setCookie)
    if (match && match[1]) {
      response.cookies.set('access_token', decodeURIComponent(match[1]), {
        httpOnly: true,
        sameSite: 'lax', // works on same-origin (Next.js domain)
        path: '/',
        // secure: true, // enable in production over HTTPS
        maxAge: 3600,
      })
    }

    return response

  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { error: 'An unexpected error occurred during login' },
      { status: 500 }
    )
  }
}

