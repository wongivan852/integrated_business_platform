# communication_services.py
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.core.mail import send_mail
from .models import CommunicationLog
import logging
from django.core.exceptions import ValidationError
from django.conf import settings
from typing import Tuple, Optional
import time

# Get specific loggers
logger = logging.getLogger('crm.communication')
security_logger = logging.getLogger('crm.security')

class WhatsAppService:
    """
    WhatsApp Business API Integration
    Using Twilio WhatsApp API or Facebook WhatsApp Business API
    """
    
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    
    def send_message(self, to_number: str, message: str, customer=None) -> Tuple[bool, str]:
        """Send WhatsApp message with enhanced error handling"""
        
        # Validate inputs
        if not to_number or not message:
            error_msg = "Phone number and message are required"
            logger.error(error_msg, extra={'validation_error': True})
            return False, error_msg
        
        if len(message) > 4096:  # WhatsApp message limit
            error_msg = "Message too long (max 4096 characters)"
            logger.error(error_msg, extra={'validation_error': True})
            return False, error_msg
        
        # Validate API configuration
        if not all([self.api_url, self.access_token, self.phone_number_id]):
            error_msg = "WhatsApp API configuration incomplete"
            logger.error(error_msg, extra={'configuration_error': True})
            return False, error_msg
        
        start_time = time.time()
        
        try:
            # Format phone number (remove + and spaces)
            formatted_number = ''.join(filter(str.isdigit, to_number))
            
            if len(formatted_number) < 10:
                error_msg = f"Invalid phone number format: {to_number}"
                logger.error(error_msg, extra={'validation_error': True})
                return False, error_msg
            
            payload = {
                "messaging_product": "whatsapp",
                "to": formatted_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(
                f"Sending WhatsApp message to {formatted_number[:6]}***",
                extra={
                    'message_length': len(message),
                    'customer_id': str(customer.id) if customer else None,
                    'recipient_masked': f"{formatted_number[:6]}***"
                }
            )
            
            response = requests.post(
                f"{self.api_url}/{self.phone_number_id}/messages",
                json=payload,
                headers=headers,
                timeout=30  # Add timeout
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id')
                
                logger.info(
                    f"WhatsApp message sent successfully in {duration:.2f}s",
                    extra={
                        'success': True,
                        'duration': duration,
                        'message_id': message_id,
                        'customer_id': str(customer.id) if customer else None,
                    }
                )
                
                # Log communication
                if customer:
                    try:
                        CommunicationLog.objects.create(
                            customer=customer,
                            channel='whatsapp',
                            subject='WhatsApp Message',
                            content=message,
                            external_message_id=message_id,
                            is_outbound=True
                        )
                    except Exception as log_error:
                        logger.error(
                            f"Failed to log WhatsApp communication: {str(log_error)}",
                            extra={'log_error': True, 'customer_id': str(customer.id)}
                        )
                
                return True, message_id
            else:
                error_msg = f"WhatsApp API error (HTTP {response.status_code}): {response.text}"
                logger.error(
                    error_msg,
                    extra={
                        'api_error': True,
                        'status_code': response.status_code,
                        'duration': duration,
                        'customer_id': str(customer.id) if customer else None,
                    }
                )
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"WhatsApp API timeout after {time.time() - start_time:.2f}s"
            logger.error(error_msg, extra={'timeout_error': True})
            return False, error_msg
        
        except requests.exceptions.ConnectionError as e:
            error_msg = f"WhatsApp API connection error: {str(e)}"
            logger.error(error_msg, extra={'connection_error': True})
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Unexpected WhatsApp error: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    'unexpected_error': True,
                    'customer_id': str(customer.id) if customer else None,
                    'duration': time.time() - start_time
                },
                exc_info=True
            )
            return False, error_msg
    
    def send_template_message(self, to_number, template_name, parameters, customer=None):
        """Send WhatsApp template message"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "en"
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": param} for param in parameters]
                        }
                    ]
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_url}/{self.phone_number_id}/messages",
                json=payload,
                headers=headers
            )
            
            return response.status_code == 200, response.json()
            
        except Exception as e:
            logger.error(f"WhatsApp template send error: {str(e)}")
            return False, str(e)

class EmailService:
    """Email service for sending notifications and marketing emails"""
    
    def send_email(self, to_email: str, subject: str, content: str, customer=None, html_content: Optional[str] = None) -> Tuple[bool, str]:
        """Send email using Django's email backend with enhanced error handling"""
        
        # Validate inputs
        if not to_email or not subject or not content:
            error_msg = "Email, subject, and content are required"
            logger.error(error_msg, extra={'validation_error': True})
            return False, error_msg
        
        # Basic email validation
        if '@' not in to_email or '.' not in to_email.split('@')[1]:
            error_msg = f"Invalid email format: {to_email}"
            logger.error(error_msg, extra={'validation_error': True})
            return False, error_msg
        
        start_time = time.time()
        
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.core.mail import get_connection
            
            logger.info(
                f"Sending email to {to_email}",
                extra={
                    'recipient': to_email,
                    'subject': subject[:50] + '...' if len(subject) > 50 else subject,
                    'customer_id': str(customer.id) if customer else None,
                    'has_html': bool(html_content)
                }
            )
            
            # Use connection with timeout
            connection = get_connection()
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
                connection=connection
            )
            
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            
            result = msg.send()
            duration = time.time() - start_time
            
            if result > 0:
                logger.info(
                    f"Email sent successfully in {duration:.2f}s",
                    extra={
                        'success': True,
                        'duration': duration,
                        'recipient': to_email,
                        'customer_id': str(customer.id) if customer else None,
                    }
                )
                
                # Log communication
                if customer:
                    try:
                        CommunicationLog.objects.create(
                            customer=customer,
                            channel='email',
                            subject=subject,
                            content=content,
                            is_outbound=True
                        )
                    except Exception as log_error:
                        logger.error(
                            f"Failed to log email communication: {str(log_error)}",
                            extra={'log_error': True, 'customer_id': str(customer.id)}
                        )
                
                return True, "Email sent successfully"
            else:
                error_msg = "Email sending failed - no messages sent"
                logger.error(
                    error_msg,
                    extra={
                        'send_failure': True,
                        'duration': duration,
                        'customer_id': str(customer.id) if customer else None,
                    }
                )
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Email send error: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    'email_error': True,
                    'recipient': to_email,
                    'customer_id': str(customer.id) if customer else None,
                    'duration': time.time() - start_time
                },
                exc_info=True
            )
            return False, error_msg
    
    def send_bulk_email(self, customers, subject, content, html_content=None):
        """Send bulk emails to multiple customers"""
        results = []
        for customer in customers:
            if customer.email and customer.marketing_consent:
                success, message = self.send_email(
                    customer.email, 
                    subject, 
                    content, 
                    customer, 
                    html_content
                )
                results.append({
                    'customer_id': customer.id,
                    'email': customer.email,
                    'success': success,
                    'message': message
                })
        return results

class WeChatService:
    """
    WeChat API Integration
    Using WeChat Work API for business communications
    """
    
    def __init__(self):
        self.corp_id = settings.WECHAT_CORP_ID
        self.corp_secret = settings.WECHAT_CORP_SECRET
        self.agent_id = settings.WECHAT_AGENT_ID
        self.access_token = None
    
    def get_access_token(self):
        """Get WeChat access token"""
        try:
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                'corpid': self.corp_id,
                'corpsecret': self.corp_secret
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('errcode') == 0:
                self.access_token = data.get('access_token')
                return True
            else:
                logger.error(f"WeChat token error: {data}")
                return False
                
        except Exception as e:
            logger.error(f"WeChat token request error: {str(e)}")
            return False
    
    def send_message(self, to_user, message, customer=None):
        """Send WeChat message"""
        try:
            if not self.access_token:
                if not self.get_access_token():
                    return False, "Failed to get access token"
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
            
            payload = {
                "touser": to_user,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": message
                }
            }
            
            response = requests.post(url, json=payload)
            data = response.json()
            
            if data.get('errcode') == 0:
                # Log communication
                if customer:
                    CommunicationLog.objects.create(
                        customer=customer,
                        channel='wechat',
                        subject='WeChat Message',
                        content=message,
                        external_message_id=data.get('msgid'),
                        is_outbound=True
                    )
                return True, "Message sent successfully"
            else:
                logger.error(f"WeChat send error: {data}")
                return False, data.get('errmsg', 'Unknown error')
                
        except Exception as e:
            logger.error(f"WeChat send error: {str(e)}")
            return False, str(e)

class CommunicationManager:
    """Unified communication manager"""
    
    def __init__(self):
        self.whatsapp = WhatsAppService()
        self.email = EmailService()
        self.wechat = WeChatService()
    
    def send_message(self, customer, channel: str, subject: str, content: str) -> Tuple[bool, str]:
        """Send message via specified channel with enhanced error handling"""
        
        if not customer:
            error_msg = "Customer is required"
            logger.error(error_msg, extra={'validation_error': True})
            return False, error_msg
        
        start_time = time.time()
        
        logger.info(
            f"Attempting to send {channel} message to customer",
            extra={
                'customer_id': str(customer.id),
                'channel': channel,
                'subject': subject[:50] + '...' if len(subject) > 50 else subject,
            }
        )
        
        try:
            if channel == 'email':
                if not customer.email_primary:
                    error_msg = f"No primary email address for customer {customer.id}"
                    logger.warning(error_msg, extra={'missing_contact': True, 'customer_id': str(customer.id)})
                    return False, error_msg
                
                return self.email.send_email(customer.email_primary, subject, content, customer)
            
            elif channel == 'whatsapp':
                if not customer.whatsapp_number:
                    error_msg = f"No WhatsApp number for customer {customer.id}"
                    logger.warning(error_msg, extra={'missing_contact': True, 'customer_id': str(customer.id)})
                    return False, error_msg
                
                return self.whatsapp.send_message(customer.whatsapp_number, content, customer)
            
            elif channel == 'wechat':
                if not customer.wechat_id:
                    error_msg = f"No WeChat ID for customer {customer.id}"
                    logger.warning(error_msg, extra={'missing_contact': True, 'customer_id': str(customer.id)})
                    return False, error_msg
                
                return self.wechat.send_message(customer.wechat_id, content, customer)
            
            else:
                error_msg = f"Unsupported communication channel: {channel}"
                logger.error(
                    error_msg,
                    extra={
                        'unsupported_channel': True,
                        'channel': channel,
                        'customer_id': str(customer.id)
                    }
                )
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Communication error for {channel}: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    'communication_error': True,
                    'channel': channel,
                    'customer_id': str(customer.id),
                    'duration': time.time() - start_time
                },
                exc_info=True
            )
            return False, error_msg
    
    def send_course_reminder(self, enrollment):
        """Send course reminder to enrolled customer"""
        customer = enrollment.customer
        course = enrollment.course
        
        subject = f"Reminder: {course.title} starts soon!"
        content = f"""
        Dear {customer.first_name},
        
        This is a reminder that your course "{course.title}" is starting soon.
        
        Start Date: {course.start_date.strftime('%Y-%m-%d %H:%M')}
        Duration: {course.duration_hours} hours
        
        Please ensure you're prepared for the session.
        
        Best regards,
        Learning Institute Team
        """
        
        return self.send_message(
            customer, 
            customer.preferred_communication_method, 
            subject, 
            content
        )
    
    def send_welcome_message(self, customer):
        """Send welcome message to new customer"""
        subject = "Welcome to Our Learning Institute!"
        content = f"""
        Dear {customer.first_name},
        
        Welcome to our learning community! We're excited to have you join us.
        
        You can explore our courses and upcoming conferences through our platform.
        
        If you have any questions, feel free to reach out to us.
        
        Best regards,
        Learning Institute Team
        """
        
        return self.send_message(
            customer, 
            customer.preferred_communication_method, 
            subject, 
            content
        )
