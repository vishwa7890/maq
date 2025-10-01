import { NextRequest } from 'next/server'
import { Server as SocketIOServer } from 'socket.io'
import { Server as HTTPServer } from 'http'

// Disable static generation for this route
export const dynamic = 'force-dynamic';
export const revalidate = 0;

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

// In-memory storage for demo purposes
// In production, you'd want to use a database like Redis
let visitorData: VisitorData = {
  totalVisitors: 1247,
  activeVisitors: 12,
  todayVisitors: 89,
  pageViews: 2341,
  averageSessionTime: '2:34',
  topPages: [
    { page: '/', views: 45 },
    { page: '/chat', views: 23 },
    { page: '/auth', views: 12 },
    { page: '/dashboard', views: 9 }
  ],
  recentVisitors: [
    {
      id: '1',
      timestamp: new Date().toISOString(),
      location: 'US',
      userAgent: 'Chrome/120.0.0.0',
      page: '/'
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 30000).toISOString(),
      location: 'IN',
      userAgent: 'Firefox/121.0',
      page: '/chat'
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 60000).toISOString(),
      location: 'GB',
      userAgent: 'Safari/17.0',
      page: '/auth'
    }
  ]
}

const activeConnections = new Set<string>()

// This is a hack to make Socket.IO work with Next.js API routes
let io: SocketIOServer | undefined

export async function GET(req: NextRequest) {
  if (!io) {
    // Create a mock HTTP server for Socket.IO
    const httpServer = new HTTPServer()
    io = new SocketIOServer(httpServer, {
      cors: {
        origin: "*",
        methods: ["GET", "POST"]
      },
      path: '/api/socket'
    })

    io.on('connection', (socket) => {
      console.log('Client connected:', socket.id)
      activeConnections.add(socket.id)
      
      // Update active visitors count
      visitorData.activeVisitors = activeConnections.size
      
      // Send current visitor data
      socket.emit('visitorUpdate', visitorData)
      
      // Broadcast new visitor to admin dashboard
      socket.broadcast.emit('newVisitor', {
        id: socket.id,
        timestamp: new Date().toISOString(),
        location: getRandomLocation(),
        userAgent: 'Unknown',
        page: '/'
      })

      // Handle visitor data requests
      socket.on('getVisitorData', () => {
        socket.emit('visitorUpdate', visitorData)
      })

      // Handle page view tracking
      socket.on('pageView', (data: { page: string; userAgent?: string }) => {
        visitorData.pageViews++
        
        // Update top pages
        const existingPage = visitorData.topPages.find(p => p.page === data.page)
        if (existingPage) {
          existingPage.views++
        } else {
          visitorData.topPages.push({ page: data.page, views: 1 })
        }
        
        // Sort top pages by views
        visitorData.topPages.sort((a, b) => b.views - a.views)
        visitorData.topPages = visitorData.topPages.slice(0, 10)
        
        // Add to recent visitors
        const newVisitor = {
          id: socket.id,
          timestamp: new Date().toISOString(),
          location: getRandomLocation(),
          userAgent: data.userAgent || 'Unknown',
          page: data.page
        }
        
        visitorData.recentVisitors.unshift(newVisitor)
        visitorData.recentVisitors = visitorData.recentVisitors.slice(0, 10)
        
        // Broadcast update
        io?.emit('visitorUpdate', visitorData)
      })

      socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id)
        activeConnections.delete(socket.id)
        visitorData.activeVisitors = activeConnections.size
        
        // Broadcast visitor left
        socket.broadcast.emit('visitorLeft', socket.id)
        socket.broadcast.emit('visitorUpdate', visitorData)
      })
    })

    // Simulate some visitor activity for demo
    setInterval(() => {
      if (Math.random() > 0.7) {
        const randomVisitor = {
          id: `demo-${Date.now()}`,
          timestamp: new Date().toISOString(),
          location: getRandomLocation(),
          userAgent: getRandomUserAgent(),
          page: getRandomPage()
        }
        
        visitorData.recentVisitors.unshift(randomVisitor)
        visitorData.recentVisitors = visitorData.recentVisitors.slice(0, 10)
        visitorData.todayVisitors++
        visitorData.totalVisitors++
        visitorData.pageViews++
        
        io?.emit('newVisitor', randomVisitor)
        io?.emit('visitorUpdate', visitorData)
      }
    }, 10000) // Every 10 seconds
  }

  return new Response('Socket.IO server initialized', { status: 200 })
}

function getRandomLocation(): string {
  const locations = ['US', 'IN', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'CN', 'BR']
  return locations[Math.floor(Math.random() * locations.length)]
}

function getRandomUserAgent(): string {
  const userAgents = [
    'Chrome/120.0.0.0',
    'Firefox/121.0',
    'Safari/17.0',
    'Edge/120.0.0.0',
    'Opera/105.0.0.0'
  ]
  return userAgents[Math.floor(Math.random() * userAgents.length)]
}

function getRandomPage(): string {
  const pages = ['/', '/chat', '/auth', '/dashboard', '/plans', '/settings']
  return pages[Math.floor(Math.random() * pages.length)]
}