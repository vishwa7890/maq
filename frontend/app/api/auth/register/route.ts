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

    // Forward any set-cookie headers from the backend
    const setCookie = res.headers.get('set-cookie')
    if (setCookie) {
      response.headers.set('set-cookie', setCookie)
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

