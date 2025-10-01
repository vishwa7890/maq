'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Users, Eye, Clock, Globe, TrendingUp, Activity, RotateCcw, AlertTriangle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import io from 'socket.io-client'

interface VisitorData {
  totalVisitors: number
  activeVisitors: number
  todayVisitors: number
  pageViews: number
  averageSessionTime: string
  topPages: Array<{ page: string; views: number }>
  recentVisitors: Array<{
    id: string
    timestamp: string
    location: string
    userAgent: string
    page: string
  }>
}

export default function AdminDashboard() {
  const [visitorData, setVisitorData] = useState<VisitorData>({
    totalVisitors: 0,
    activeVisitors: 0,
    todayVisitors: 0,
    pageViews: 0,
    averageSessionTime: '0:00',
    topPages: [],
    recentVisitors: []
  })
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [mounted, setMounted] = useState(false)
  const [socket, setSocket] = useState<any>(null)
  const [isResetting, setIsResetting] = useState(false)
  const [showResetConfirm, setShowResetConfirm] = useState(false)

  useEffect(() => {
    setMounted(true)
    setLastUpdate(new Date())
    
    // Initialize socket connection
    const socketInstance = io(process.env.NEXT_PUBLIC_SOCKET_URL || window.location.origin)
    setSocket(socketInstance)

    socketInstance.on('connect', () => {
      setIsConnected(true)
      console.log('Connected to socket server')
    })

    socketInstance.on('disconnect', () => {
      setIsConnected(false)
      console.log('Disconnected from socket server')
    })

    // Listen for visitor updates
    socketInstance.on('visitorUpdate', (data: VisitorData) => {
      setVisitorData(data)
      setLastUpdate(new Date())
    })

    // Listen for new visitor events
    socketInstance.on('newVisitor', (visitor: any) => {
      setVisitorData(prev => ({
        ...prev,
        activeVisitors: prev.activeVisitors + 1,
        todayVisitors: prev.todayVisitors + 1,
        recentVisitors: [visitor, ...prev.recentVisitors.slice(0, 9)]
      }))
      setLastUpdate(new Date())
    })

    // Listen for visitor left events
    socketInstance.on('visitorLeft', () => {
      setVisitorData(prev => ({
        ...prev,
        activeVisitors: Math.max(0, prev.activeVisitors - 1)
      }))
      setLastUpdate(new Date())
    })

    // Listen for reset confirmation
    socketInstance.on('statsReset', () => {
      setIsResetting(false)
      setShowResetConfirm(false)
      setLastUpdate(new Date())
    })

    // Request initial data
    socketInstance.emit('getVisitorData')

    // Cleanup on unmount
    return () => {
      socketInstance.disconnect()
    }
  }, [])

  const formatTime = (timestamp: string) => {
    if (!mounted) return '--:--:--'
    return new Date(timestamp).toLocaleTimeString()
  }

  const getLocationFlag = (location: string) => {
    const flags: { [key: string]: string } = {
      'US': '🇺🇸',
      'IN': '🇮🇳',
      'GB': '🇬🇧',
      'CA': '🇨🇦',
      'AU': '🇦🇺',
      'DE': '🇩🇪',
      'FR': '🇫🇷',
      'JP': '🇯🇵',
      'CN': '🇨🇳',
      'BR': '🇧🇷'
    }
    return flags[location] || '🌍'
  }

  const handleResetStats = () => {
    if (!socket || !isConnected) return
    
    setIsResetting(true)
    socket.emit('resetStats')
    
    // Reset local state immediately for better UX
    setVisitorData({
      totalVisitors: 0,
      activeVisitors: 0,
      todayVisitors: 0,
      pageViews: 0,
      averageSessionTime: '0:00',
      topPages: [],
      recentVisitors: []
    })
    
    setTimeout(() => {
      setIsResetting(false)
      setShowResetConfirm(false)
    }, 2000)
  }

  const handleResetClick = () => {
    setShowResetConfirm(true)
  }

  const handleCancelReset = () => {
    setShowResetConfirm(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Admin Dashboard
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                Real-time visitor analytics and monitoring
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Badge 
                variant={isConnected ? "default" : "destructive"}
                className="flex items-center gap-2"
              >
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                {isConnected ? 'Connected' : 'Disconnected'}
              </Badge>
              <div className="text-sm text-slate-500">
                Last update: {mounted && lastUpdate ? lastUpdate.toLocaleTimeString() : '--:--:--'}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleResetClick}
                disabled={!isConnected || isResetting}
                className="flex items-center gap-2 border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300"
              >
                <RotateCcw className={`h-4 w-4 ${isResetting ? 'animate-spin' : ''}`} />
                {isResetting ? 'Resetting...' : 'Reset Stats'}
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="relative overflow-hidden border-0 shadow-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">Active Visitors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-3xl font-bold">{visitorData.activeVisitors}</div>
                  <Activity className="h-8 w-8 opacity-80" />
                </div>
                <div className="absolute -right-4 -bottom-4 opacity-20">
                  <Users className="h-16 w-16" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="relative overflow-hidden border-0 shadow-lg bg-gradient-to-br from-green-500 to-green-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">Today's Visitors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-3xl font-bold">{visitorData.todayVisitors}</div>
                  <TrendingUp className="h-8 w-8 opacity-80" />
                </div>
                <div className="absolute -right-4 -bottom-4 opacity-20">
                  <Eye className="h-16 w-16" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="relative overflow-hidden border-0 shadow-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">Total Visitors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-3xl font-bold">{visitorData.totalVisitors}</div>
                  <Globe className="h-8 w-8 opacity-80" />
                </div>
                <div className="absolute -right-4 -bottom-4 opacity-20">
                  <Users className="h-16 w-16" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="relative overflow-hidden border-0 shadow-lg bg-gradient-to-br from-orange-500 to-orange-600 text-white">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium opacity-90">Page Views</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-3xl font-bold">{visitorData.pageViews}</div>
                  <Clock className="h-8 w-8 opacity-80" />
                </div>
                <div className="absolute -right-4 -bottom-4 opacity-20">
                  <Eye className="h-16 w-16" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Real-time Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Visitors */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-600" />
                  Recent Visitors
                </CardTitle>
                <CardDescription>
                  Live visitor activity on your website
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  <AnimatePresence>
                    {visitorData.recentVisitors.map((visitor, index) => (
                      <motion.div
                        key={visitor.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="text-2xl">
                            {getLocationFlag(visitor.location)}
                          </div>
                          <div>
                            <div className="font-medium text-sm">
                              {visitor.location || 'Unknown'}
                            </div>
                            <div className="text-xs text-slate-500">
                              {visitor.page}
                            </div>
                          </div>
                        </div>
                        <div className="text-xs text-slate-500">
                          {formatTime(visitor.timestamp)}
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  {visitorData.recentVisitors.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      No recent visitors
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Top Pages */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
          >
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  Popular Pages
                </CardTitle>
                <CardDescription>
                  Most visited pages today
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {visitorData.topPages.map((page, index) => (
                    <div
                      key={page.page}
                      className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-medium text-sm">
                            {page.page}
                          </div>
                        </div>
                      </div>
                      <Badge variant="secondary">
                        {page.views} views
                      </Badge>
                    </div>
                  ))}
                  {visitorData.topPages.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      No page data available
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Session Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="mt-6"
        >
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-orange-600" />
                Session Analytics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {visitorData.averageSessionTime}
                  </div>
                  <div className="text-sm text-slate-500">Average Session Time</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {visitorData.pageViews > 0 ? (visitorData.pageViews / Math.max(visitorData.todayVisitors, 1)).toFixed(1) : '0'}
                  </div>
                  <div className="text-sm text-slate-500">Pages per Session</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {visitorData.activeVisitors > 0 ? ((visitorData.activeVisitors / visitorData.totalVisitors) * 100).toFixed(1) : '0'}%
                  </div>
                  <div className="text-sm text-slate-500">Active Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Reset Confirmation Modal */}
        <AnimatePresence>
          {showResetConfirm && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={handleCancelReset}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Reset Statistics
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      This action cannot be undone
                    </p>
                  </div>
                </div>
                
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  Are you sure you want to reset all visitor statistics? This will clear:
                </p>
                
                <ul className="text-sm text-gray-500 dark:text-gray-400 mb-6 space-y-1">
                  <li>• Total visitors count</li>
                  <li>• Today's visitors</li>
                  <li>• Page views</li>
                  <li>• Recent visitors list</li>
                  <li>• Popular pages data</li>
                </ul>
                
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={handleCancelReset}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleResetStats}
                    disabled={isResetting}
                    className="flex-1 flex items-center gap-2"
                  >
                    <RotateCcw className={`h-4 w-4 ${isResetting ? 'animate-spin' : ''}`} />
                    {isResetting ? 'Resetting...' : 'Reset All'}
                  </Button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}