'use client'

import { useState, useEffect, useCallback } from 'react'
import Script from 'next/script'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { useRouter } from 'next/navigation'
import { PaymentModal } from '@/components/payment-modal'
import { Mail, Phone, User, Lock, CreditCard } from 'lucide-react'
import { api } from '@/lib/api'

type Role = 'normal' | 'premium'

declare global {
  interface Window {
    google?: any
  }
}

export default function AuthPage() {
  const [activeTab, setActiveTab] = useState('login')
  const [showPayment, setShowPayment] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState<{
    username: string
    email: string
    password: string
    phone: string
    role: Role
  }>({
    username: '',
    email: '',
    password: '',
    phone: '',
    role: 'normal',
  })
  const router = useRouter()

  const handleGoogleCredential = useCallback(async (credentialResponse: { credential?: string }) => {
    const credential = credentialResponse?.credential

    if (!credential) {
      setError('Google authentication failed. Missing credential.')
      return
    }

    try {
      setLoading(true)
      setError(null)
      await api.googleLogin(credential)
      const user = await api.me()
      if (user) {
        router.push('/chat')
      }
    } catch (err: any) {
      setError(err?.message || 'Google login failed. Please try again later.')
    } finally {
      setLoading(false)
    }
  }, [router])

  const initializeGoogle = useCallback(() => {
    if (typeof window === 'undefined') return

    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
    if (!clientId) {
      console.warn('NEXT_PUBLIC_GOOGLE_CLIENT_ID is not configured.')
      return
    }

    const google = window.google
    if (!google?.accounts?.id) {
      return
    }

    google.accounts.id.initialize({
      client_id: clientId,
      callback: handleGoogleCredential,
    })

    const target = document.getElementById('googleSignInButton')
    if (target) {
      target.innerHTML = ''
      google.accounts.id.renderButton(target, {
        theme: 'outline',
        size: 'large',
        type: 'standard',
      })
    }
  }, [handleGoogleCredential])

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      // First attempt to log in
      await api.login({ 
        username: formData.username, 
        password: formData.password 
      })
      
      // Verify authentication by fetching user data
      const user = await api.me()
      if (user) {
        router.push('/chat')
      } else {
        throw new Error('Authentication verification failed')
      }
    } catch (err: any) {
      setError(err?.message || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    
    try {
      if (formData.role === 'premium') {
        setShowPayment(true)
        setLoading(false)
        return
      }
      
      // First register the user
      await api.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        phone: formData.phone,
        role: formData.role,
      })
      
      // Then log in to get the auth cookie
      await api.login({ 
        username: formData.username, 
        password: formData.password 
      })
      
      // Verify authentication before navigation
      const user = await api.me()
      if (user) {
        router.push('/chat')
      } else {
        setError('Authentication failed after registration')
      }
    } catch (err: any) {
      setError(err?.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const handlePaymentSuccess = async () => {
    // After successful payment, create the user in backend with premium role
    try {
      setLoading(true)
      setShowPayment(false)
      
      // First register the user with premium role
      const registrationResponse = await api.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        phone: formData.phone,
        role: 'premium', // Explicitly set premium role after payment
      })
      
      if (!registrationResponse) {
        throw new Error('Registration failed after payment')
      }
      
      // Then log in to get the auth cookie
      await api.login({ 
        username: formData.username, 
        password: formData.password 
      })
      
      // Verify authentication before navigation
      const user = await api.me()
      if (user) {
        setShowPayment(false)
        router.push('/chat')
      } else {
        throw new Error('Authentication failed after premium registration')
      }
    } catch (err: any) {
      setError(err?.message || 'Registration failed after payment')
      setShowPayment(false)
    } finally {
      setLoading(false)
    }
  }

  const isValidEmail = (email: string) => {
    return email.includes('@gmail.com') || email.includes('@yahoo.com')
  }

  useEffect(() => {
    initializeGoogle()
  }, [initializeGoogle])

  useEffect(() => {
    // Check for upgrade parameter
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.get('upgrade') === 'true') {
      setActiveTab('register')
      setFormData(prev => ({ ...prev, role: 'premium' }))
    }
  }, [])

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-100 flex items-center justify-center p-4 overflow-hidden">
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        async
        defer
        onLoad={initializeGoogle}
      />
      {/* Decorative background */}
      <div className="pointer-events-none absolute -top-24 -left-24 h-[24rem] w-[24rem] rounded-full bg-blue-200/40 blur-3xl -z-10" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-[24rem] w-[24rem] rounded-full bg-purple-200/40 blur-3xl -z-10" />
      <Card className="w-full max-w-md rounded-xl border shadow-xl bg-white/95 backdrop-blur">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-blue-600">VilaiMathi AI</CardTitle>
          <CardDescription>Your Business Quotation Expert</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="register">Register</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                {error && activeTab === 'login' && (
                  <p className="text-sm text-red-600">{error}</p>
                )}
                <div className="space-y-2">
                  <Label htmlFor="login-username">Username</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="login-username"
                      type="text"
                      placeholder="Enter username"
                      className="pl-10"
                      value={formData.username}
                      onChange={(e) => handleInputChange('username', e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="login-password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="Enter password"
                      className="pl-10"
                      value={formData.password}
                      onChange={(e) => handleInputChange('password', e.target.value)}
                      required
                    />
                  </div>
                </div>

                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? 'Logging in...' : 'Login'}
                </Button>
                <div className="flex items-center gap-2 text-xs uppercase text-gray-400">
                  <div className="h-px flex-1 bg-gray-200" />
                  <span>Or</span>
                  <div className="h-px flex-1 bg-gray-200" />
                </div>
                <div className="flex justify-center">
                  <div id="googleSignInButton" className="flex justify-center" />
                </div>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4">
                {error && activeTab === 'register' && (
                  <p className="text-sm text-red-600">{error}</p>
                )}
                <div className="space-y-2">
                  <Label htmlFor="register-username">Username</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="register-username"
                      type="text"
                      placeholder="Choose username"
                      className="pl-10"
                      value={formData.username}
                      onChange={(e) => handleInputChange('username', e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-email">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="Gmail or Yahoo only"
                      className="pl-10"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      required
                    />
                  </div>
                  {formData.email && !isValidEmail(formData.email) && (
                    <p className="text-sm text-red-500">Please use Gmail or Yahoo email</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="Create password"
                      className="pl-10"
                      value={formData.password}
                      onChange={(e) => handleInputChange('password', e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-phone">Phone</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="register-phone"
                      type="tel"
                      placeholder="Phone number"
                      className="pl-10"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <Label>Choose Role</Label>
                  <RadioGroup
                    value={formData.role}
                    onValueChange={(value) =>
                      setFormData(prev => ({ ...prev, role: value as Role }))
                    }
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="normal" id="normal" />
                      <Label htmlFor="normal">Normal (Free - 5 quotes max)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="premium" id="premium" />
                      <Label htmlFor="premium" className="flex items-center gap-2">
                        Premium (Unlimited + No Watermark)
                        <CreditCard className="h-4 w-4" />
                      </Label>
                    </div>
                  </RadioGroup>
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={loading || (!!formData.email && !isValidEmail(formData.email))}
                >
                  {loading ? 'Processing...' : formData.role === 'premium' ? 'Continue to Payment' : 'Register'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <PaymentModal
        isOpen={showPayment}
        onClose={() => setShowPayment(false)}
        onSuccess={handlePaymentSuccess}
        userEmail={formData.email}
      />
    </div>
  )
}
