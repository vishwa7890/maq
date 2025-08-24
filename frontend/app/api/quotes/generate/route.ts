import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Forward the request to the backend quote generation endpoint
    const response = await fetch(`${API_BASE}/api/quotes/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
      },
      credentials: 'include',
      body: JSON.stringify(body),
    })

    const data = await response.json()
    
    // Return the response with the same status code
    return NextResponse.json(data, { status: response.status })

  } catch (error) {
    console.error('Quote generation error:', error)
    
    // Fallback to mock behavior if backend is unavailable
    try {
      const { prompt, userRole, quotesUsed } = await request.json()
      
      if (userRole === 'normal' && quotesUsed >= 5) {
        return NextResponse.json(
          { 
            error: 'Quote limit reached',
            message: 'You\'ve reached your monthly limit of 5 quotes. Upgrade to Premium for unlimited quotes.',
            upgrade_required: true,
            current_plan: 'normal',
            quotes_used: quotesUsed,
            quotes_limit: 5
          },
          { status: 429 }
        )
      }

      const generateQuoteItems = (p: string) => {
        const items: any[] = []
        const t = p.toLowerCase()
        if (t.includes('web') || t.includes('website')) {
          items.push(
            { description: 'Web Development', quantity: 1, rate: 2500, amount: 2500 },
            { description: 'Responsive Design', quantity: 1, rate: 800, amount: 800 },
            { description: 'Testing & QA', quantity: 1, rate: 500, amount: 500 }
          )
        } else if (t.includes('mobile') || t.includes('app')) {
          items.push(
            { description: 'Mobile App Development', quantity: 1, rate: 4000, amount: 4000 },
            { description: 'UI/UX Design', quantity: 1, rate: 1200, amount: 1200 },
            { description: 'App Store Deployment', quantity: 1, rate: 300, amount: 300 }
          )
        } else if (t.includes('design')) {
          items.push(
            { description: 'UI/UX Design', quantity: 1, rate: 1500, amount: 1500 },
            { description: 'Branding & Logo', quantity: 1, rate: 800, amount: 800 },
            { description: 'Design System', quantity: 1, rate: 1000, amount: 1000 }
          )
        } else {
          items.push(
            { description: 'Initial consultation', quantity: 1, rate: 150, amount: 150 },
            { description: 'Project development', quantity: 20, rate: 100, amount: 2000 },
            { description: 'Testing and deployment', quantity: 5, rate: 120, amount: 600 }
          )
        }
        return items
      }

      const items = generateQuoteItems(prompt)
      const subtotal = items.reduce((sum, item) => sum + item.amount, 0)
      const tax = Math.round(subtotal * 0.1) // 10% tax
      const total = subtotal + tax
      
      const quote = {
        id: `quote_${Date.now()}`,
        title: `Quote for: ${prompt.substring(0, 50)}...`,
        items,
        subtotal,
        tax,
        total,
        terms: 'Payment due within 30 days',
        has_watermark: userRole === 'normal',
        can_edit: userRole === 'premium',
        created_at: new Date().toISOString()
      }

      return NextResponse.json({
        success: true,
        message: 'Quote generated successfully',
        quote,
        user_info: {
          role: userRole,
          quotes_used: quotesUsed + 1,
          quotes_remaining: userRole === 'normal' ? 5 - (quotesUsed + 1) : 'unlimited'
        }
      })
    } catch {
      return NextResponse.json({ error: 'Failed to generate quote' }, { status: 500 })
    }
  }
}
