'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Users, Eye, TrendingUp, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import io, { Socket } from 'socket.io-client'

interface VisitorStats {
  totalVisitors: number
  activeVisitors: number
  todayVisitors: number
  pageViews: number
}

export default function VisitorCounter() {
  const [stats, setStats] = useState<VisitorStats>({
    totalVisitors: 0,
    activeVisitors: 0,
    todayVisitors: 0,
    pageViews: 0
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [socket, setSocket] = useState<Socket | null>(null)

  useEffect(() => {
    // Fetch initial stats
    const fetchStats = async () => {
      try {
        setError(null);
        const response = await fetch('/api/visitors');
        const result = await response.json();
        
        if (!response.ok) {
          throw new Error(result.message || 'Failed to load visitor data');
        }
        
        if (result.success && result.data) {
          setStats(prev => ({
            ...prev,
            totalVisitors: result.data.totalVisitors || 0,
            todayVisitors: result.data.todayVisitors || 0,
            pageViews: result.data.pageViews || 0,
            activeVisitors: result.data.uniqueVisitors || 0
          }));
        }
      } catch (error) {
        console.error('Error fetching visitor stats:', error);
        setError(
          error instanceof Error 
            ? error.message 
            : 'We\'re having trouble loading visitor statistics. Please refresh the page to try again.'
        );
      } finally {
        setIsLoading(false);
      }
    }

    fetchStats()

    // Initialize socket for real-time updates
    let socketInstance: Socket;
    
    try {
      socketInstance = io(process.env.NEXT_PUBLIC_SOCKET_URL || window.location.origin, {
        reconnectionAttempts: 3,
        reconnectionDelay: 1000,
        timeout: 5000
      });

      socketInstance.on('connect', () => {
        console.log('Connected to visitor counter socket');
      });

      socketInstance.on('visitorUpdate', (data: VisitorStats) => {
        setStats(prev => ({
          ...prev,
          ...data
        }));
      });

      socketInstance.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
        setError('Connection to live updates lost. Some features may be limited.');
      });

      socketInstance.on('error', (error) => {
        console.error('Socket error:', error);
        setError('There was an issue with live updates. The visitor count may not be current.');
      });

      setSocket(socketInstance);
    } catch (error) {
      console.error('Failed to initialize socket:', error);
      setError('Live updates are currently unavailable. The visitor count may not be current.');
    }

    return () => {
      if (socket) {
        socket.off('connect');
        socket.off('visitorUpdate');
        socket.off('connect_error');
        socket.off('error');
        socket.disconnect();
      }
    }
  }, [])

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4">
              <div className="h-4 bg-gray-200 rounded mb-2"></div>
              <div className="h-8 bg-gray-200 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  const statItems = [
    {
      label: 'Active Now',
      value: stats.activeVisitors,
      icon: Activity,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      pulse: true
    },
    {
      label: 'Today',
      value: stats.todayVisitors,
      icon: TrendingUp,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      label: 'Total Visitors',
      value: stats.totalVisitors,
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      label: 'Page Views',
      value: stats.pageViews,
      icon: Eye,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ]

  return (
    <div className="w-full">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
          Live Visitor Statistics
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Real-time website analytics
        </p>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AnimatePresence>
          {statItems.map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow duration-300">
                <CardContent className={`p-4 ${item.bgColor} dark:bg-gray-800`}>
                  <div className="flex items-center justify-between mb-2">
                    <item.icon className={`h-5 w-5 ${item.color}`} />
                    {item.pulse && (
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></div>
                        <Badge variant="secondary" className="text-xs">
                          Live
                        </Badge>
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-1">
                    <motion.div
                      key={item.value}
                      initial={{ scale: 1.2 }}
                      animate={{ scale: 1 }}
                      className={`text-2xl font-bold ${item.color}`}
                    >
                      {item.value.toLocaleString()}
                    </motion.div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                      {item.label}
                    </div>
                  </div>
                  
                  {/* Decorative background element */}
                  <div className={`absolute -right-2 -bottom-2 opacity-10 ${item.color}`}>
                    <item.icon className="h-12 w-12" />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      
      {/* Connection status */}
      <div className="flex justify-center mt-4">
        <Badge 
          variant={socket?.connected ? "default" : "secondary"}
          className="text-xs"
        >
          <div className={`w-2 h-2 rounded-full mr-2 ${
            socket?.connected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
          }`} />
          {socket?.connected ? 'Live Updates Active' : 'Connecting...'}
        </Badge>
      </div>
    </div>
  )
}