'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Menu, X, Crown, User, LogOut } from 'lucide-react'
import { api } from '@/lib/api'
import { useRouter } from 'next/navigation'
import Image from 'next/image'

export function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await api.me()
        setUser(userData)
        // Save user data to localStorage for dashboard access
        localStorage.setItem('user', JSON.stringify(userData))
      } catch {
        setUser(null)
        localStorage.removeItem('user')
      } finally {
        setIsLoading(false)
      }
    }

    fetchUser()

    // Listen for user updates (e.g., after quote generation)
    const handleUserUpdate = () => {
      fetchUser()
    }

    window.addEventListener('user-updated', handleUserUpdate)
    return () => window.removeEventListener('user-updated', handleUserUpdate)
  }, [])

  const handleLogout = async () => {
    try {
      await api.logout()
      setUser(null)
      router.push('/')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <header className="sticky top-0 z-50 border-b bg-white/95 backdrop-blur-sm shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <Image
              src="/lumina_qou_png.png"
              alt="VilaiMathi AI"
              width={52}
              height={52}
              priority
            />
            <span className="text-xl font-bold text-gray-900">VilaiMathi AI</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            {user ? (
              <Link 
                href="/chat" 
                className="text-gray-700 hover:text-blue-600 font-medium transition-colors"
              >
                Chat
              </Link>
            ) : (
              <button 
                onClick={() => {
                  // Redirect to auth page with a message
                  window.location.href = '/auth?message=Please sign in to access the chat feature.';
                }}
                className="text-gray-400 cursor-not-allowed font-medium"
              >
                Chat
              </button>
            )}
            <Link 
              href="#features" 
              className="text-gray-700 hover:text-blue-600 font-medium transition-colors"
            >
              Features
            </Link>
            <Link 
              href="#pricing" 
              className="text-gray-700 hover:text-blue-600 font-medium transition-colors"
            >
              Pricing
            </Link>
            
            {/* User Section */}
            {isLoading ? (
              <div className="w-20 h-9 bg-gray-200 animate-pulse rounded-md"></div>
            ) : user ? (
              <div className="flex items-center gap-3">
                <Badge variant={user.role === 'premium' ? 'default' : 'secondary'} className="text-xs">
                  {user.role === 'premium' ? (
                    <>
                      <Crown className="h-3 w-3 mr-1" />
                      Premium
                    </>
                  ) : (
                    `Free (${user.quotes_used || 0}/5)`
                  )}
                </Badge>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gradient-to-r from-gray-400 to-gray-600 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={handleLogout}
                    className="text-gray-600 hover:text-gray-900"
                  >
                    <LogOut className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link href="/auth">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link href="/auth">
                  <Button size="sm" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                    Get Started
                  </Button>
                </Link>
              </div>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden border-t bg-white/95 backdrop-blur-sm">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {user ? (
                <Link 
                  href="/chat" 
                  className="block px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-md font-medium"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Chat
                </Link>
              ) : (
                <button 
                  className="block w-full text-left px-3 py-2 text-gray-400 cursor-not-allowed rounded-md font-medium"
                  onClick={() => {
                    setIsMenuOpen(false);
                    window.location.href = '/auth?message=Please sign in to access the chat feature.';
                  }}
                >
                  Chat
                </button>
              )}
              <Link 
                href="#features" 
                className="block px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-md font-medium"
                onClick={() => setIsMenuOpen(false)}
              >
                Features
              </Link>
              <Link 
                href="#pricing" 
                className="block px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-md font-medium"
                onClick={() => setIsMenuOpen(false)}
              >
                Pricing
              </Link>
              
              {user ? (
                <div className="px-3 py-2 space-y-2">
                  <Badge variant={user.role === 'premium' ? 'default' : 'secondary'} className="text-xs">
                    {user.role === 'premium' ? (
                      <>
                        <Crown className="h-3 w-3 mr-1" />
                        Premium
                      </>
                    ) : (
                      `Free (${user.quotes_used || 0}/5)`
                    )}
                  </Badge>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={handleLogout}
                    className="w-full justify-start text-gray-600 hover:text-gray-900"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign Out
                  </Button>
                </div>
              ) : (
                <div className="px-3 py-2 space-y-2">
                  <Link href="/auth" className="block">
                    <Button variant="ghost" size="sm" className="w-full justify-start">
                      Sign In
                    </Button>
                  </Link>
                  <Link href="/auth" className="block">
                    <Button size="sm" className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                      Get Started
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
