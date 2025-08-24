'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { BarChart3, TrendingUp, FileText, Download, Edit3, ArrowLeft, Crown, Calendar, DollarSign, Users, Target } from 'lucide-react'

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (!userData) {
      router.push('/')
      return
    }
    
    const parsedUser = JSON.parse(userData)
    
    // Redirect normal users to their dashboard
    if (parsedUser.role === 'normal') {
      router.push('/dashboard/normal')
      return
    }
    
    if (parsedUser.role !== 'premium') {
      router.push('/chat')
      return
    }
    
    setUser(parsedUser)
  }, [router])

  // Mock data for dashboard
  const stats = {
    totalQuotes: 47,
    totalValue: 2450000,
    avgQuoteValue: 52127,
    conversionRate: 68
  }

  const recentQuotes = [
    { id: '1', client: 'Tech Corp', value: 125000, status: 'Approved', date: '2024-01-15' },
    { id: '2', client: 'StartupXYZ', value: 75000, status: 'Pending', date: '2024-01-14' },
    { id: '3', client: 'Enterprise Ltd', value: 200000, status: 'Approved', date: '2024-01-13' },
    { id: '4', client: 'SME Business', value: 45000, status: 'Rejected', date: '2024-01-12' },
    { id: '5', client: 'Global Inc', value: 180000, status: 'Pending', date: '2024-01-11' }
  ]

  const monthlyData = [
    { month: 'Jan', quotes: 12, value: 580000 },
    { month: 'Feb', quotes: 15, value: 720000 },
    { month: 'Mar', quotes: 20, value: 950000 },
    { month: 'Apr', quotes: 18, value: 840000 },
    { month: 'May', quotes: 25, value: 1200000 }
  ]

  if (!user) return null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
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
                <h1 className="text-2xl font-bold text-gray-900">Premium Dashboard</h1>
                <p className="text-gray-600">Analytics and insights for your quotations</p>
              </div>
            </div>
            
            <Badge className="bg-gradient-to-r from-purple-600 to-blue-600">
              <Crown className="h-4 w-4 mr-2" />
              Premium Account
            </Badge>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Quotes</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalQuotes}</div>
              <p className="text-xs text-muted-foreground">
                +12% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Value</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">₹{stats.totalValue.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                +18% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Quote Value</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">₹{stats.avgQuoteValue.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                +5% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.conversionRate}%</div>
              <p className="text-xs text-muted-foreground">
                +3% from last month
              </p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="quotes">Recent Quotes</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Monthly Performance */}
              <Card>
                <CardHeader>
                  <CardTitle>Monthly Performance</CardTitle>
                  <CardDescription>Quote volume and value trends</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {monthlyData.map((data, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-12 text-sm font-medium">{data.month}</div>
                          <div className="flex-1">
                            <div className="text-sm">{data.quotes} quotes</div>
                            <div className="text-xs text-gray-500">₹{data.value.toLocaleString()}</div>
                          </div>
                        </div>
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${(data.value / 1200000) * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <CardDescription>Frequently used features</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button className="w-full justify-start" onClick={() => router.push('/chat')}>
                    <FileText className="h-4 w-4 mr-2" />
                    Create New Quote
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <Download className="h-4 w-4 mr-2" />
                    Export All Quotes
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Generate Report
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <Users className="h-4 w-4 mr-2" />
                    Client Management
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="quotes" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Quotes</CardTitle>
                <CardDescription>Your latest quotation activity</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentQuotes.map((quote) => (
                    <div key={quote.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <FileText className="h-8 w-8 text-blue-600" />
                        <div>
                          <div className="font-medium">{quote.client}</div>
                          <div className="text-sm text-gray-500">{quote.date}</div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="font-medium">₹{quote.value.toLocaleString()}</div>
                          <Badge 
                            variant={
                              quote.status === 'Approved' ? 'default' : 
                              quote.status === 'Pending' ? 'secondary' : 'destructive'
                            }
                          >
                            {quote.status}
                          </Badge>
                        </div>
                        
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline">
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button size="sm" variant="outline">
                            <Edit3 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Quote Status Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span>Approved</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div className="bg-green-600 h-2 rounded-full" style={{ width: '68%' }} />
                        </div>
                        <span className="text-sm">68%</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Pending</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div className="bg-yellow-600 h-2 rounded-full" style={{ width: '22%' }} />
                        </div>
                        <span className="text-sm">22%</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Rejected</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div className="bg-red-600 h-2 rounded-full" style={{ width: '10%' }} />
                        </div>
                        <span className="text-sm">10%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Top Performing Categories</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>Web Development</span>
                      <span className="font-medium">₹850K</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Mobile Apps</span>
                      <span className="font-medium">₹620K</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>UI/UX Design</span>
                      <span className="font-medium">₹480K</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Consulting</span>
                      <span className="font-medium">₹320K</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="insights" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>AI-Powered Insights</CardTitle>
                <CardDescription>Recommendations to improve your quotation competitiveness</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-600">
                  <h4 className="font-medium text-blue-900">Pricing Optimization</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Your web development quotes are 15% higher than market average. Consider adjusting rates for better conversion.
                  </p>
                </div>
                
                <div className="p-4 bg-green-50 rounded-lg border-l-4 border-green-600">
                  <h4 className="font-medium text-green-900">Strong Performance</h4>
                  <p className="text-sm text-green-700 mt-1">
                    Your mobile app quotes have a 85% approval rate - excellent work! Consider expanding this service area.
                  </p>
                </div>
                
                <div className="p-4 bg-yellow-50 rounded-lg border-l-4 border-yellow-600">
                  <h4 className="font-medium text-yellow-900">Response Time</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    Quotes sent within 24 hours have 40% higher approval rates. Consider setting up automated responses.
                  </p>
                </div>
                
                <div className="p-4 bg-purple-50 rounded-lg border-l-4 border-purple-600">
                  <h4 className="font-medium text-purple-900">Seasonal Trends</h4>
                  <p className="text-sm text-purple-700 mt-1">
                    Q4 typically sees 30% more enterprise quotes. Prepare capacity and specialized offerings.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
