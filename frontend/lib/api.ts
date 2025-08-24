export const API_BASE =
  (typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_BACKEND_URL as string | undefined)
    : process.env.BACKEND_URL) || 'http://localhost:8000'

export type FetchOptions = RequestInit & {
  json?: any
}

export async function apiFetch(path: string, opts: FetchOptions = {}) {
  // If calling Next.js internal API route, do not prefix with backend URL
  const isExternal = path.startsWith('http')
  const isInternalApi = path.startsWith('/api/')
  const url = isExternal ? path : isInternalApi ? path : `${API_BASE}${path}`
  const { json, headers, ...rest } = opts

  // Ensure we include credentials for all requests to maintain session
  const fetchOptions: RequestInit = {
    ...rest,
    credentials: 'include', // This will handle sending/receiving cookies automatically
    headers: {
      'Accept': 'application/json',
      ...(json ? { 'Content-Type': 'application/json' } : {}),
      ...(headers || {}),
    },
    body: json ? JSON.stringify(json) : opts.body,
  }

  const res = await fetch(url, fetchOptions)

  const contentType = res.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await res.json() : await res.text()

  if (!res.ok) {
    let message = res.statusText
    let shouldLogout = false
    
    // Handle specific error cases
    if (res.status === 401) {
      message = 'Your session has expired. Please log in again.'
      shouldLogout = true
    } else if (res.status === 403) {
      message = 'You do not have permission to perform this action.'
      shouldLogout = true
    } else if (typeof data === 'string') {
      message = data
    } else if (data) {
      message = data.detail || data.error?.message || data.message || res.statusText
    }
    
    // Clear auth state if needed
    if (shouldLogout && typeof window !== 'undefined') {
      try {
        await api.logout()
      } catch (e) {
        console.error('Error during logout:', e)
      }
    }
    
    const error = new Error(message || 'API request failed')
    // @ts-ignore
    error.status = res.status
    throw error
  }

  return data
}

export const api = {
  // Route through Next.js API to handle cookies and CORS
  login: (payload: { username: string; password: string }) =>
    apiFetch('/api/auth/login', { method: 'POST', json: payload }),
  register: (payload: { username: string; email: string; password: string; phone_number?: string; phone?: string; role?: 'normal' | 'premium' }) =>
    apiFetch('/api/auth/register', { method: 'POST', json: payload }),
  me: () => apiFetch('/api/auth/me', { method: 'GET' }),
  generateQuote: (payload: any) => apiFetch('/api/quotes/generate', { method: 'POST', json: payload }),
  logout: () => apiFetch('/api/auth/logout', { method: 'POST' }),
  // Chat APIs (proxying to backend via Next.js API routes)
  listChatSessions: () => apiFetch('/api/chat/sessions', { method: 'GET' }),
  createChatSession: (payload: { title?: string; metadata?: any }) =>
    apiFetch('/api/chat/sessions', { method: 'POST', json: payload }),
  getSessionMessages: (session_uuid: string) =>
    apiFetch(`/api/chat/sessions/${encodeURIComponent(session_uuid)}/messages`, { method: 'GET' }),
  sendChat: (payload: { content: string; chat_id?: string; role?: 'user' | 'assistant' }) =>
    apiFetch('/api/chat/chat', { method: 'POST', json: payload }),
}
