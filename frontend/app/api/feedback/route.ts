import { handleApiError } from '@/lib/error-handler';

// Disable static generation for this route
export const dynamic = 'force-dynamic';
export const revalidate = 0;

// This is the URL of your backend API
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    
    // Add additional metadata
    const feedbackData = {
      ...body,
      page_url: request.headers.get('referer') || 'unknown',
      user_agent: request.headers.get('user-agent') || 'unknown'
    }

    // Forward the feedback to our backend
    const response = await fetch(`${BACKEND_URL}/api/feedback/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedbackData),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to submit feedback')
    }

    const data = await response.json()
    return new Response(
      JSON.stringify({
        success: true,
        message: 'Thank you for your feedback! We appreciate your input.',
        data
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    )
    
  } catch (error) {
    return handleApiError(error, {
      action: 'submit your feedback',
      feature: 'feedback form',
      details: 'Please try again in a few moments.'
    });
  }
}
