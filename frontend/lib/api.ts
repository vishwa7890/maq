// Ensure the base URL ends with a single slash
const getBaseUrl = () => {
  let base = (typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_BACKEND_URL as string | undefined)
    : process.env.BACKEND_URL) || 'https://lumina-nbzx.onrender.com';
  
  // Ensure the base URL ends with exactly one slash
  return base.endsWith('/') ? base : `${base}/`;
};

export const API_BASE = getBaseUrl();

export type FetchOptions = RequestInit & {
  json?: any
  // When true, bypasses the in-memory GET cache and forces a fresh request
  noCache?: boolean
}

const cache = new Map();
const CACHE_TIME = 5 * 60 * 1000; // 5 minutes

export async function apiFetch(path: string, opts: FetchOptions = {}) {
  // Always route to backend unless an absolute URL is provided
  const isExternal = path.startsWith('http')
  // Remove any leading slashes from path to prevent double slashes after API_BASE
  const cleanPath = path.replace(/^\/+/, '')
  const url = isExternal ? path : new URL(cleanPath, API_BASE).toString()
  const { json, headers, ...rest } = opts
  // Identify auth endpoints to avoid recursive logout on expected 401s
  const isAuthMe = path === '/auth/me' || path.endsWith('/auth/me')
  const isAuthEndpoint =
    path.startsWith('/auth/') ||
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
    credentials: 'include',
    headers: {
      ...(json ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
    body: json ? JSON.stringify(json) : rest.body,   // 👈 fix
    ...rest,
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
    
    // Extract error message from response first
    if (typeof data === 'string') {
      message = data
    } else if (data) {
      message = data.detail || data.error?.message || data.message || res.statusText
    }
    
    // Handle specific error cases
    if (res.status === 401) {
      // For login/register endpoints, show the actual error (e.g., "Incorrect username or password")
      // For other endpoints, show session expired message
      if (!isAuthEndpoint || isAuthMe) {
        // Only override message if it's generic
        if (!message || message === 'Unauthorized') {
          message = 'Your session has expired. Please log in again to continue.'
        }
      }
      // Do not auto-logout for auth endpoints like /auth/me or /auth/login where 401 is expected
      shouldLogout = !isAuthMe && !isAuthEndpoint
    } else if (res.status === 403) {
      if (!message || message === 'Forbidden') {
        message = 'You do not have permission to perform this action.'
      }
      // Avoid recursive logout for auth routes
      shouldLogout = !isAuthEndpoint
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
  // Directly call FastAPI backend endpoints
  login: (payload: { username: string; password: string }) => {
    // FastAPI's OAuth2PasswordRequestForm expects form-encoded body: username, password
    const form = new URLSearchParams()
    form.append('username', payload.username)
    form.append('password', payload.password)
    return apiFetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form as any,
    })
  },
  register: (payload: { username: string; email: string; password: string; phone_number?: string; phone?: string; role?: 'normal' | 'premium' }) =>
    apiFetch('/auth/register', { method: 'POST', json: payload }),
  googleLogin: (idToken: string) =>
    apiFetch('/auth/google', {
      method: 'POST',
      json: { id_token: idToken },
      noCache: true,
    }).then(result => {
      try {
        cache.delete('/auth/me')
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new Event('user-updated'))
        }
      } catch {}
      return result
    }),
  // Always bypass cache for user info to keep usage counts fresh
  me: () => apiFetch('/auth/me', { method: 'GET', noCache: true }),
  generateQuote: async (payload: any) => {
    const result = await apiFetch('/api/quotes/generate', { method: 'POST', json: payload })
    // Invalidate user info cache and notify listeners so UI can refresh counts
    try {
      cache.delete('/auth/me')
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('user-updated'))
      }
    } catch {}
    return result
  },
  generateAnalysisPrompt: (payload: { topic: string; context?: string; tone?: string }) =>
    apiFetch('/api/chat/analysis/prompt', { method: 'POST', json: payload }),
  logout: async () => {
    const result = await apiFetch('/auth/logout', { method: 'POST' })
    try {
      cache.delete('/auth/me')
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('user-updated'))
      }
    } catch {}
    return result
  },
  // Chat APIs (proxying to backend via Next.js API routes)
  listChatSessions: () => apiFetch('/api/chat/sessions/', { method: 'GET' }),
  createChatSession: (payload: { title?: string; metadata?: any }) =>
    apiFetch('/api/chat/sessions/', { method: 'POST', json: payload }),
  getSessionMessages: (session_uuid: string) =>
    apiFetch(`/api/chat/sessions/${encodeURIComponent(session_uuid)}/messages`, { method: 'GET' }),
  sendChat: async (payload: { content: string; chat_id?: string; role?: 'user' | 'assistant' }) => {
    const result = await apiFetch('/api/chat/chat', { method: 'POST', json: payload })
    try {
      if (result && result.user_info) {
        cache.delete('/auth/me')
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new Event('user-updated'))
        }
      }
    } catch {}
    return result
  },
}
