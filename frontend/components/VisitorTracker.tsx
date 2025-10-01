'use client'

import { useEffect, useRef } from 'react'
import io, { Socket } from 'socket.io-client'

interface VisitorTrackerProps {
  page?: string
}

export default function VisitorTracker({ page = '/' }: VisitorTrackerProps) {
  const socketRef = useRef<Socket | null>(null)
  const hasTracked = useRef(false)

  useEffect(() => {
    // Only track once per page load
    if (hasTracked.current) return

    const trackVisitor = async () => {
      try {
        // Generate a unique visitor ID
        const visitorId = localStorage.getItem('visitorId') || 
          `visitor-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        
        if (!localStorage.getItem('visitorId')) {
          localStorage.setItem('visitorId', visitorId)
        }

        // Track via API
        await fetch('/api/visitors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            visitorId,
            page,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
          }),
        })

        // Initialize socket connection for real-time tracking
        if (!socketRef.current) {
          socketRef.current = io(process.env.NEXT_PUBLIC_SOCKET_URL || window.location.origin)

          socketRef.current.on('connect', () => {
            console.log('Connected to visitor tracking')
            
            // Send page view event
            socketRef.current?.emit('pageView', {
              page,
              userAgent: navigator.userAgent,
              visitorId
            })
          })

          socketRef.current.on('disconnect', () => {
            console.log('Disconnected from visitor tracking')
          })
        }

        hasTracked.current = true
      } catch (error) {
        console.error('Error tracking visitor:', error)
      }
    }

    // Track visitor after a short delay to ensure page is loaded
    const timer = setTimeout(trackVisitor, 1000)

    return () => {
      clearTimeout(timer)
      if (socketRef.current) {
        socketRef.current.disconnect()
        socketRef.current = null
      }
    }
  }, [page])

  // This component doesn't render anything visible
  return null
}