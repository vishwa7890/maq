import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import email service using absolute import
from app.utils.email_service import email_service

# Set up logging
logger = logging.getLogger(__name__)


router = APIRouter()

class Feedback(BaseModel):
    name: str
    email: str
    message: str
    rating: Optional[int] = None
    page_url: Optional[str] = None
    user_agent: Optional[str] = None

@router.post("/submit")
async def submit_feedback(
    feedback: Feedback,
    request: Request,
    user_agent: str = Header(None, alias="User-Agent")
):
    """
    Submit feedback and send it via email
    """
    try:
        # Convert feedback to dict for email
        feedback_dict = feedback.dict()
        
        # Add metadata
        feedback_dict.update({
            "timestamp": datetime.utcnow().isoformat(),
            "page_url": str(request.url),
            "user_agent": user_agent
        })
        
        # Log the feedback for debugging
        logger.info(f"Processing feedback from {feedback_dict.get('email', 'unknown')}")
        
        # Send email
        success, message = await email_service.send_feedback_email(feedback_dict)
        
        if not success:
            logger.error(f"Failed to send feedback email: {message}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": message,
                    "message": "We received your feedback but encountered an issue sending the notification."
                }
            )
            
        logger.info("Feedback processed successfully")
        return {
            "success": True,
            "message": "Thank you for your feedback! We'll get back to you soon."
        }
        
    except Exception as e:
        error_msg = f"Unexpected error processing feedback: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "An unexpected error occurred",
                "message": "We're sorry, but we encountered an error while processing your feedback. Please try again later."
            }
        )

# Add this to your main FastAPI app's router
# from .feedback import router as feedback_router
# app.include_router(feedback_router, prefix="/api/feedback", tags=["feedback"])
