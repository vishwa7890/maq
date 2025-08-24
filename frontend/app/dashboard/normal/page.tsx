'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ArrowLeft, FileText, Crown, AlertTriangle, TrendingUp, Download, Calendar, Target, Zap, Lock } from 'lucide-react'

export default function NormalDashboardPage() {
  const [user, setUser] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (!userData) {
      router.push('/')
      return
    }
    
    const parsedUser = JSON.parse(userData)
    if (parsedUser.role !== 'normal') {
      router.push('/dashboard')
      return
    }
    
    setUser(parsedUser)
  }, [router])

  const handleUpgrade = () => {
    router.push('/?upgrade=true')
  }

  // Mock data for normal user
  const quotesUsed = user?.quotesUsed || 0
  const quotesRemaining = 5 - quotesUsed
  const usagePercentage = (quotesUsed / 5) * 100

  const recentQuotes = [
    { id: '1', client: 'Local Business', value: 25000, status: 'Approved', date: '2024-01-15' },
    { id: '2', client: 'Startup ABC', value: 35000, status: 'Pending', date: '2024-01-14' },
    { id: '3', client: 'Small Corp', value: 18000, status: 'Approved', date: '2024-01-12' }
  ].slice(0, quotesUsed)

  if (!user) return null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/chat')}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Chat
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">My Dashboard</h1>
                <p className="text-gray-600">Track your quotation activity</p>
              </div>
            </div>
            
            <Badge variant="secondary">
              Normal Plan
            </Badge>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Usage Alert */}
        {quotesUsed >= 4 && (
          <Alert className="mb-6 border-orange-200 bg-orange-50">
            <AlertTriangle className="h-4 w-4 text-orange-600" />
            <AlertDescription className="text-orange-800">
              You're running low on quotes! You have {quotesRemaining} quote{quotesRemaining !== 1 ? 's' : ''} remaining.
              <Button 
                variant="link" 
                className="p-0 ml-2 text-orange-600 underline"
                onClick={handleUpgrade}
              >
                Upgrade to Premium
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Quotes Used</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{quotesUsed}/5</div>
              <Progress value={usagePercentage} className="mt-2" />
              <p className="text-xs text-muted-foreground mt-2">
                {quotesRemaining} remaining this month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Value</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ₹{recentQuotes.reduce((sum, quote) => sum + quote.value, 0).toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                From {quotesUsed} quotes
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {quotesUsed > 0 ? Math.round((recentQuotes.filter(q => q.status === 'Approved').length / quotesUsed) * 100) : 0}%
              </div>
              <p className="text-xs text-muted-foreground">
                Approval rate
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Quotes */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Quotes</CardTitle>
              <CardDescription>Your latest quotation activity</CardDescription>
            </CardHeader>
            <CardContent>
              {recentQuotes.length > 0 ? (
                <div className="space-y-4">
                  {recentQuotes.map((quote) => (
                    <div key={quote.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="h-6 w-6 text-blue-600" />
                        <div>
                          <div className="font-medium text-sm">{quote.client}</div>
                          <div className="text-xs text-gray-500">{quote.date}</div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="font-medium text-sm">₹{quote.value.toLocaleString()}</div>
                        <Badge 
                          variant={
                            quote.status === 'Approved' ? 'default' : 
                            quote.status === 'Pending' ? 'secondary' : 'destructive'
                          }
                          className="text-xs"
                        >
                          {quote.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>No quotes generated yet</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="mt-2"
                    onClick={() => router.push('/chat')}
                  >
                    Create Your First Quote
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Premium Features */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Crown className="h-5 w-5 text-yellow-500" />
                Upgrade to Premium
              </CardTitle>
              <CardDescription>Unlock advanced features and unlimited access</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                  <Zap className="h-4 w-4 text-green-500" />
                  <span>Unlimited quote generation</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <Download className="h-4 w-4 text-green-500" />
                  <span>No watermark on PDFs</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <FileText className="h-4 w-4 text-green-500" />
                  <span>Edit quote functionality</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span>Advanced analytics dashboard</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <Calendar className="h-4 w-4 text-green-500" />
                  <span>Quote history & management</span>
                </div>
              </div>
              
              <div className="pt-4 border-t">
                <div className="text-center mb-4">
                  <div className="text-2xl font-bold text-blue-600">₹999/month</div>
                  <div className="text-sm text-gray-500">Billed monthly</div>
                </div>
                
                <Button onClick={handleUpgrade} className="w-full">
                  <Crown className="h-4 w-4 mr-2" />
                  Upgrade Now
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Limitations Notice */}
        <Card className="mt-6 border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <Lock className="h-5 w-5" />
              Current Plan Limitations
            </CardTitle>
          </CardHeader>
          <CardContent className="text-orange-700">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <span>Limited to 5 quotes per month</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <span>Watermark on all PDF exports</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <span>No quote editing capability</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <span>Basic analytics only</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
