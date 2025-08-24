const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

function getTokenFromCookieHeader(cookieHeader: string | null): string | null {
  if (!cookieHeader) return null
  const parts = cookieHeader.split(';').map(p => p.trim())
  for (const p of parts) {
    if (p.startsWith('access_token=')) {
      const val = decodeURIComponent(p.substring('access_token='.length))
      return val || null
    }
  }
  return null
}

export async function POST(req: Request) {
  const cookieHeader = req.headers.get('cookie')
  const token = getTokenFromCookieHeader(cookieHeader)
  const headers: HeadersInit = { 'Content-Type': 'application/json', Accept: 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (cookieHeader) headers['Cookie'] = cookieHeader

  const body = await req.json().catch(() => ({}))
  const res = await fetch(`${BACKEND_URL}/api/chat/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  const contentType = res.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await res.json() : await res.text()
  return new Response(JSON.stringify(data), { status: res.status, headers: { 'Content-Type': 'application/json' } })
}
