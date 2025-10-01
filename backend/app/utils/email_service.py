import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Tuple
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Verify environment variables
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
if not EMAIL_PASSWORD or EMAIL_PASSWORD == "your_app_specific_password_here":
    logger.warning("EMAIL_PASSWORD not set or using default value. Emails will not be sent.")

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "vilaimathiai@gmail.com"
        self.sender_password = os.getenv("EMAIL_PASSWORD")
        
    async def send_feedback_email(self, feedback_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Send feedback email to the configured email address
        
        Args:
            feedback_data (dict): Dictionary containing feedback data with keys:
                - name: User's name
                - email: User's email
                - message: Feedback message
                - rating: Optional rating (1-5)
                
        Returns:
            Tuple[bool, str]: (success, message) indicating whether the email was sent successfully
        """
        if not self.sender_password or self.sender_password == "your_app_specific_password_here":
            logger.warning("Email not sent: EMAIL_PASSWORD not properly configured")
            return False, "Email service not configured properly"
            
        try:
            # Create message container
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.sender_email
            msg['Subject'] = f"New Feedback from {feedback_data.get('name', 'Anonymous')}"
            
            # Create email body with additional metadata
            page_url = feedback_data.get('page_url', 'Not provided')
            user_agent = feedback_data.get('user_agent', 'Not provided')
            
            body = f"""
            <h2>New Feedback Received</h2>
            <p><strong>Name:</strong> {feedback_data.get('name', 'Anonymous')}</p>
            <p><strong>Email:</strong> {feedback_data.get('email', 'Not provided')}</p>
            <p><strong>Rating:</strong> {feedback_data.get('rating', 'Not rated')}/5</p>
            <p><strong>Page URL:</strong> {page_url}</p>
            <p><strong>User Agent:</strong> {user_agent}</p>
            <p><strong>Timestamp:</strong> {feedback_data.get('timestamp', 'Not available')}</p>
            
            <h3>Message:</h3>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
                {feedback_data.get('message', 'No message provided')}
            </div>
            """
            
            # Attach body to email
            msg.attach(MIMEText(body, 'html'))
            
            # Create a secure SSL context
            context = ssl.create_default_context()
            
            # Try to log in to server and send email
            with smtplib.SMTP_SSL(self.smtp_server, 465, context=context) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info("Feedback email sent successfully")
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = "Failed to authenticate with email server. Please check your email credentials."
            logger.error(f"{error_msg} Error: {str(e)}")
            return False, error_msg
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# Create a singleton instance
email_service = EmailService()
