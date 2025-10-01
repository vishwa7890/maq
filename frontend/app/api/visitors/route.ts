import { NextRequest } from 'next/server';
import { handleApiError } from '@/lib/error-handler';

// Disable static generation for this route
export const dynamic = 'force-dynamic';
export const revalidate = 0;

// In-memory storage for demo purposes
// In production, you'd want to use a database
let visitorStats = {
  totalVisitors: 1247,
  todayVisitors: 89,
  pageViews: 2341,
  uniqueVisitors: new Set<string>(),
  dailyVisitors: new Set<string>(),
  lastReset: new Date().toDateString()
}

export async function GET(request: NextRequest) {
  try {
    // Reset daily counters if it's a new day
    const today = new Date().toDateString()
    if (visitorStats.lastReset !== today) {
      visitorStats.dailyVisitors.clear()
      visitorStats.todayVisitors = 0
      visitorStats.lastReset = today
    }

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          totalVisitors: visitorStats.totalVisitors,
          todayVisitors: visitorStats.todayVisitors,
          pageViews: visitorStats.pageViews,
          uniqueVisitors: visitorStats.uniqueVisitors.size
        }
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return handleApiError(error, {
      action: 'retrieve visitor statistics',
      feature: 'visitor counter',
      details: 'This won\'t affect your experience.'
    });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { visitorId, page, userAgent } = body
    
    // Get client IP for unique visitor tracking
    const forwarded = request.headers.get('x-forwarded-for')
    const ip = forwarded ? forwarded.split(',')[0] : request.headers.get('x-real-ip') || 'unknown'
    
    const uniqueId = visitorId || `${ip}-${userAgent}`
    
    // Reset daily counters if it's a new day
    const today = new Date().toDateString()
    if (visitorStats.lastReset !== today) {
      visitorStats.dailyVisitors.clear()
      visitorStats.todayVisitors = 0
      visitorStats.lastReset = today
    }
    
    // Track unique visitors
    if (!visitorStats.uniqueVisitors.has(uniqueId)) {
      visitorStats.uniqueVisitors.add(uniqueId)
      visitorStats.totalVisitors++
    }
    
    // Track daily visitors
    if (!visitorStats.dailyVisitors.has(uniqueId)) {
      visitorStats.dailyVisitors.add(uniqueId)
      visitorStats.todayVisitors++
    }
    
    // Increment page views
    visitorStats.pageViews++
    
    return new Response(
      JSON.stringify({
        success: true,
        data: {
          totalVisitors: visitorStats.totalVisitors,
          todayVisitors: visitorStats.todayVisitors,
          pageViews: visitorStats.pageViews
        }
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return handleApiError(error, {
      action: 'update visitor statistics',
      feature: 'visitor counter',
      details: 'This won\'t affect your experience.'
    });
  }
}