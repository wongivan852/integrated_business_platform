# tasks.py
# from celery import shared_task  # Temporarily disabled
from django.utils import timezone
from datetime import timedelta
from .models import Customer, Course, Enrollment, CommunicationLog
from .communication_services import CommunicationManager
import logging

logger = logging.getLogger(__name__)

# @shared_task  # Temporarily disabled
def send_course_reminders():
    """Send reminders for courses starting in 24 hours"""
    tomorrow = timezone.now() + timedelta(days=1)
    enrollments = Enrollment.objects.filter(
        course__start_date__date=tomorrow.date(),
        status__in=['registered', 'confirmed']
    )
    
    comm_manager = CommunicationManager()
    sent_count = 0
    
    for enrollment in enrollments:
        try:
            success, message = comm_manager.send_course_reminder(enrollment)
            if success:
                sent_count += 1
                logger.info(f"Reminder sent to {enrollment.customer.email}")
            else:
                logger.error(f"Failed to send reminder to {enrollment.customer.email}: {message}")
        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
    
    return f"Course reminders sent to {sent_count} customers"

# @shared_task  # Temporarily disabled
def send_weekly_newsletter():
    """Send weekly newsletter to subscribed customers"""
    customers = Customer.objects.filter(
        marketing_consent=True,
        status='active'
    )
    
    # Get upcoming courses and conferences
    upcoming_courses = Course.objects.filter(
        start_date__gte=timezone.now(),
        start_date__lte=timezone.now() + timedelta(days=30),
        is_active=True
    )[:5]
    
    # Create newsletter content
    subject = "Weekly Newsletter - Upcoming Courses & Events"
    content = f"""
    Dear Learning Community,
    
    Here's what's coming up this week:
    
    🎓 UPCOMING COURSES:
    """
    
    for course in upcoming_courses:
        content += f"• {course.title} - Starting {course.start_date.strftime('%B %d, %Y')}\n"
    
    content += """
    
    Visit our website for more details and registration.
    
    Best regards,
    Learning Institute Team
    """
    
    comm_manager = CommunicationManager()
    sent_count = 0
    
    for customer in customers:
        try:
            success, message = comm_manager.send_message(
                customer, 'email', subject, content
            )
            if success:
                sent_count += 1
        except Exception as e:
            logger.error(f"Error sending newsletter to {customer.email}: {str(e)}")
    
    return f"Newsletter sent to {sent_count} customers"

# @shared_task  # Temporarily disabled
def cleanup_old_communication_logs():
    """Clean up communication logs older than 6 months"""
    cutoff_date = timezone.now() - timedelta(days=180)
    deleted_count = CommunicationLog.objects.filter(
        sent_at__lt=cutoff_date
    ).delete()[0]
    
    return f"Deleted {deleted_count} old communication logs"

# @shared_task  # Temporarily disabled
def send_welcome_message_task(customer_id):
    """Background task to send welcome message to new customer"""
    try:
        customer = Customer.objects.get(id=customer_id)
        comm_manager = CommunicationManager()
        success, message = comm_manager.send_welcome_message(customer)
        
        if success:
            logger.info(f"Welcome message sent to {customer.email}")
            return f"Welcome message sent to {customer.email}"
        else:
            logger.error(f"Failed to send welcome message to {customer.email}: {message}")
            return f"Failed to send welcome message: {message}"
            
    except Customer.DoesNotExist:
        error_msg = f"Customer with ID {customer_id} not found"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error sending welcome message: {str(e)}"
        logger.error(error_msg)
        return error_msg
