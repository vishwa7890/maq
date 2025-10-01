/**
 * User-friendly error messages for common error scenarios
 */

type ErrorContext = {
  action?: string;
  feature?: string;
  details?: string;
};

/**
 * Converts technical errors into user-friendly messages
 */
export function getUserFriendlyError(error: unknown, context: ErrorContext = {}): string {
  const { action = 'process your request', feature = 'feature', details } = context;
  
  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }
  
  // Handle Error objects
  if (error instanceof Error) {
    const errorMessage = error.message.toLowerCase();
    
    // Common error patterns
    if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
      return `We're having trouble connecting to our servers. Please check your internet connection and try again.`;
    }
    
    if (errorMessage.includes('auth') || errorMessage.includes('unauthorized')) {
      return `Please sign in to access this ${feature}.`;
    }
    
    if (errorMessage.includes('timeout')) {
      return `This is taking longer than expected. Please wait a moment and try again.`;
    }
    
    if (errorMessage.includes('validation') || errorMessage.includes('invalid')) {
      return `The information you entered doesn't look right. Please check and try again.`;
    }
    
    if (errorMessage.includes('not found')) {
      return `We couldn't find what you're looking for. It may have been moved or deleted.`;
    }
    
    // Fallback with context
    return `We couldn't ${action}. ${details || 'Please try again later.'}`;
  }
  
  // Default fallback
  return `Something went wrong while trying to ${action}. Our team has been notified.`;
}

/**
 * Standard error response for API routes
 */
export function createErrorResponse(error: unknown, status: number = 500, context: ErrorContext = {}) {
  console.error('API Error:', error);
  
  return new Response(
    JSON.stringify({
      success: false,
      message: getUserFriendlyError(error, context),
      error: process.env.NODE_ENV === 'development' ? String(error) : undefined
    }),
    {
      status,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

/**
 * Handles common API errors with appropriate status codes
 */
export function handleApiError(error: unknown, context: ErrorContext = {}) {
  const errorMessage = String(error).toLowerCase();
  
  if (errorMessage.includes('not found')) {
    return createErrorResponse(error, 404, {
      ...context,
      action: context.action || 'find the requested resource'
    });
  }
  
  if (errorMessage.includes('unauthorized') || errorMessage.includes('forbidden')) {
    return createErrorResponse(error, 403, {
      ...context,
      action: context.action || 'access this resource'
    });
  }
  
  if (errorMessage.includes('validation')) {
    return createErrorResponse(error, 400, {
      ...context,
      action: context.action || 'validate your input'
    });
  }
  
  return createErrorResponse(error, 500, context);
}
