export const API_BASE =
  (typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_BACKEND_URL as string | undefined)
    : process.env.BACKEND_URL) || 'http://localhost:8000'

export type FetchOptions = RequestInit & {
  json?: any
  // When true, bypasses the in-memory GET cache and forces a fresh request
  noCache?: boolean
}

const cache = new Map();
const CACHE_TIME = 5 * 60 * 1000; // 5 minutes

export async function apiFetch(path: string, opts: FetchOptions = {}) {
  // If calling Next.js internal API route, do not prefix with backend URL
  const isExternal = path.startsWith('http')
  const isInternalApi = path.startsWith('/api/')
  const url = isExternal ? path : isInternalApi ? path : `${API_BASE}${path}`
  const { json, headers, ...rest } = opts
  // Identify auth endpoints to avoid recursive logout on expected 401s
  const isAuthMe = path === '/api/auth/me' || path.endsWith('/auth/me')
  const isAuthEndpoint =
    path.startsWith('/api/auth/') ||
    path.includes('/auth/login') ||
    path.includes('/auth/logout') ||
    path.includes('/auth/register') ||
    path.includes('/auth/me')
  
  // Check cache for GET requests unless explicitly disabled
  if ((rest.method === 'GET' || !rest.method) && !opts.noCache) {
    const cached = cache.get(url);
    if (cached && Date.now() - cached.timestamp < CACHE_TIME) {
      return cached.data;
    }
  }

  // Ensure we include credentials for all requests to maintain session
  const fetchOptions: RequestInit = {
    ...rest,
    credentials: 'include', // This will handle sending/receiving cookies automatically
    headers: {
      'Accept': 'application/json',
      'Cache-Control': 'no-cache',
      ...(json ? { 'Content-Type': 'application/json' } : {}),
      ...(headers || {}),
    },
    body: json ? JSON.stringify(json) : opts.body,
  }

  // If noCache, ensure we purge any stale entry before fetching
  if (opts.noCache) {
    cache.delete(url)
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
      // Do not auto-logout for auth endpoints like /auth/me where 401 is expected
      shouldLogout = !isAuthMe && !isAuthEndpoint
    } else if (res.status === 403) {
      message = 'You do not have permission to perform this action.'
      // Avoid recursive logout for auth routes
      shouldLogout = !isAuthEndpoint
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

  // Populate cache for GET responses (only when not disabled)
  if ((rest.method === 'GET' || !rest.method) && !opts.noCache) {
    cache.set(url, { data, timestamp: Date.now() })
  }

  return data
}

export const api = {
  // Route through Next.js API to handle cookies and CORS
  login: (payload: { username: string; password: string }) =>
    apiFetch('/api/auth/login', { method: 'POST', json: payload }),
  register: (payload: { username: string; email: string; password: string; phone_number?: string; phone?: string; role?: 'normal' | 'premium' }) =>
    apiFetch('/api/auth/register', { method: 'POST', json: payload }),
  // Always bypass cache for user info to keep usage counts fresh
  me: () => apiFetch('/api/auth/me', { method: 'GET', noCache: true }),
  generateQuote: async (payload: any) => {
    const result = await apiFetch('/api/quotes/generate', { method: 'POST', json: payload })
    // Invalidate user info cache and notify listeners so UI can refresh counts
    try {
      cache.delete('/api/auth/me')
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('user-updated'))
      }
    } catch {}
    return result
  },
  logout: async () => {
    const result = await apiFetch('/api/auth/logout', { method: 'POST' })
    try {
      cache.delete('/api/auth/me')
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('user-updated'))
      }
    } catch {}
    return result
  },
  // Chat APIs (proxying to backend via Next.js API routes)
  listChatSessions: () => apiFetch('/api/chat/sessions', { method: 'GET' }),
  createChatSession: (payload: { title?: string; metadata?: any }) =>
    apiFetch('/api/chat/sessions', { method: 'POST', json: payload }),
  getSessionMessages: (session_uuid: string) =>
    apiFetch(`/api/chat/sessions/${encodeURIComponent(session_uuid)}/messages`, { method: 'GET' }),
  sendChat: async (payload: { content: string; chat_id?: string; role?: 'user' | 'assistant' }) => {
    const result = await apiFetch('/api/chat/chat', { method: 'POST', json: payload })
    try {
      if (result && result.user_info) {
        cache.delete('/api/auth/me')
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new Event('user-updated'))
        }
      }
    } catch {}
    return result
  },
}
