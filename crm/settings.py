# settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'crm',  # Your CRM app
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'crm_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'crm_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'crm_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@learninginstitute.com')

# WhatsApp Configuration (Facebook Business API)
WHATSAPP_API_URL = "https://graph.facebook.com/v17.0"
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.environ.get('WHATSAPP_WEBHOOK_VERIFY_TOKEN')

# WeChat Configuration
WECHAT_CORP_ID = os.environ.get('WECHAT_CORP_ID')
WECHAT_CORP_SECRET = os.environ.get('WECHAT_CORP_SECRET')
WECHAT_AGENT_ID = os.environ.get('WECHAT_AGENT_ID')

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# webhooks.py
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import hmac
import hashlib
from .models import Customer, CommunicationLog
from .communication_services import CommunicationManager
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """WhatsApp webhook handler"""
    
    if request.method == "GET":
        # Webhook verification
        verify_token = request.GET.get('hub.verify_token')
        if verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            return HttpResponse(request.GET.get('hub.challenge'))
        return HttpResponse('Verification failed', status=403)
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            
            # Process incoming messages
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    
                    # Handle incoming messages
                    if 'messages' in value:
                        for message in value['messages']:
                            phone_number = message['from']
                            message_text = message.get('text', {}).get('body', '')
                            message_id = message['id']
                            
                            # Find customer by phone number
                            try:
                                customer = Customer.objects.filter(
                                    whatsapp_number__icontains=phone_number[-10:]
                                ).first()
                                
                                if customer:
                                    # Log incoming message
                                    CommunicationLog.objects.create(
                                        customer=customer,
                                        channel='whatsapp',
                                        subject='Incoming WhatsApp Message',
                                        content=message_text,
                                        external_message_id=message_id,
                                        is_outbound=False
                                    )
                                    
                                    # Auto-respond based on message content
                                    handle_whatsapp_message(customer, message_text)
                                
                            except Exception as e:
                                logger.error(f"Error processing WhatsApp message: {e}")
                    
                    # Handle message status updates
                    if 'statuses' in value:
                        for status in value['statuses']:
                            message_id = status['id']
                            status_type = status['status']
                            
                            # Update communication log with delivery status
                            try:
                                comm_log = CommunicationLog.objects.get(
                                    external_message_id=message_id
                                )
                                # You can add a status field to track delivery
                                logger.info(f"Message {message_id} status: {status_type}")
                            except CommunicationLog.DoesNotExist:
                                pass
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {e}")
            return JsonResponse({'error': str(e)}, status=500)

def handle_whatsapp_message(customer, message_text):
    """Handle incoming WhatsApp message and provide auto-responses"""
    message_lower = message_text.lower()
    comm_manager = CommunicationManager()
    
    if any(keyword in message_lower for keyword in ['courses', 'class', 'learn']):
        response = f"""
        Hi {customer.first_name}! 
        
        Here are our available courses:
        • Online Programming Bootcamp
        • Data Science Workshop
        • Digital Marketing Course
        
        Reply with the course name for more details, or visit our website.
        """
        comm_manager.whatsapp.send_message(customer.whatsapp_number, response, customer)
    
    elif any(keyword in message_lower for keyword in ['conference', 'event', 'seminar']):
        response = f"""
        Hi {customer.first_name}!
        
        We have exciting conferences coming up:
        • Tech Innovation Summit 2025
        • Education Leadership Conference
        
        Would you like more information about any of these events?
        """
        comm_manager.whatsapp.send_message(customer.whatsapp_number, response, customer)
    
    elif any(keyword in message_lower for keyword in ['help', 'support', 'contact']):
        response = f"""
        Hi {customer.first_name}!
        
        I'm here to help! You can:
        • Ask about our courses
        • Get conference information
        • Speak with our support team at support@learninginstitute.com
        
        What would you like to know?
        """
        comm_manager.whatsapp.send_message(customer.whatsapp_number, response, customer)

@csrf_exempt
@require_http_methods(["POST"])
def email_webhook(request):
    """Email webhook handler for incoming emails (using services like SendGrid, Mailgun)"""
    try:
        data = json.loads(request.body)
        
        # Example for SendGrid inbound parse
        from_email = data.get('from')
        subject = data.get('subject', '')
        content = data.get('text', '')
        
        # Find customer by email
        try:
            customer = Customer.objects.get(email=from_email)
            
            # Log incoming email
            CommunicationLog.objects.create(
                customer=customer,
                channel='email',
                subject=subject,
                content=content,
                is_outbound=False
            )
            
            # Auto-respond if needed
            handle_email_message(customer, subject, content)
            
        except Customer.DoesNotExist:
            logger.info(f"Received email from unknown customer: {from_email}")
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Email webhook error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def handle_email_message(customer, subject, content):
    """Handle incoming email and provide auto-responses"""
    subject_lower = subject.lower()
    content_lower = content.lower()
    
    if any(keyword in subject_lower or keyword in content_lower 
           for keyword in ['course', 'enrollment', 'register']):
        # Auto-respond with course information
        pass  # Implement auto-response logic
    
    elif any(keyword in subject_lower or keyword in content_lower 
             for keyword in ['conference', 'event']):
        # Auto-respond with conference information
        pass  # Implement auto-response logic

# management/commands/send_daily_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models import Enrollment
from crm.communication_services import CommunicationManager

class Command(BaseCommand):
    help = 'Send daily course reminders'
    
    def handle(self, *args, **options):
        tomorrow = timezone.now() + timedelta(days=1)
        enrollments = Enrollment.objects.filter(
            course__start_date__date=tomorrow.date(),
            status__in=['registered', 'confirmed']
        )
        
        comm_manager = CommunicationManager()
        sent_count = 0
        
        for enrollment in enrollments:
            success, message = comm_manager.send_course_reminder(enrollment)
            if success:
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Reminder sent to {enrollment.customer.email}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send reminder to {enrollment.customer.email}: {message}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Sent {sent_count} course reminders')
        )