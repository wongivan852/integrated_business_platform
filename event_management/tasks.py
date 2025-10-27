"""
Celery Tasks for Event Management System

This module contains background tasks for:
- Automated reminder sending (email, SMS, WeChat)
- Daily event digests
- Overdue event checks
- Notification delivery tracking
"""
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
import logging

from .models import Event, EventReminder

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_reminder_email(self, reminder_id):
    """
    Send a reminder email to recipients

    Args:
        reminder_id: ID of the EventReminder instance

    Returns:
        dict: Status of email sending
    """
    try:
        reminder = EventReminder.objects.select_related('event', 'created_by').prefetch_related('recipients').get(id=reminder_id)

        # Get all recipient emails
        recipient_emails = [user.email for user in reminder.recipients.all() if user.email]

        if not recipient_emails:
            logger.warning(f"No valid email addresses for reminder {reminder_id}")
            reminder.email_error = "No valid email addresses found"
            reminder.save()
            return {'status': 'error', 'message': 'No valid email addresses'}

        # Prepare email content
        subject = f"[Event Reminder] {reminder.title}"

        # Create HTML email
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #0d6efd; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .event-details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ background-color: #6c757d; color: white; padding: 10px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{reminder.title}</h2>
            </div>
            <div class="content">
                <p>{reminder.message}</p>

                <div class="event-details">
                    <h3>Event Information</h3>
                    <p><strong>Event Number:</strong> {reminder.event.event_number}</p>
                    <p><strong>Customer:</strong> {reminder.event.customer_company}</p>
                    <p><strong>Contact Person:</strong> {reminder.event.contact_person}</p>
                    <p><strong>Start Date:</strong> {reminder.event.planned_start_date.strftime('%B %d, %Y')}</p>
                    <p><strong>End Date:</strong> {reminder.event.planned_end_date.strftime('%B %d, %Y')}</p>
                    <p><strong>Location:</strong> {reminder.event.delivery_address}</p>
                </div>

                <p>Please ensure you are prepared for this event. If you have any questions, contact your supervisor.</p>
            </div>
            <div class="footer">
                <p>This is an automated reminder from Krystal Business Platform</p>
                <p>Do not reply to this email</p>
            </div>
        </body>
        </html>
        """

        plain_content = strip_tags(html_content)

        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_emails,
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        # Update reminder status
        reminder.email_sent = True
        reminder.email_error = ""
        if not reminder.sent:
            reminder.sent = True
            reminder.sent_at = timezone.now()
        reminder.save()

        logger.info(f"Reminder email sent successfully: {reminder_id} to {len(recipient_emails)} recipients")
        return {'status': 'success', 'recipients': len(recipient_emails)}

    except EventReminder.DoesNotExist:
        logger.error(f"Reminder {reminder_id} not found")
        return {'status': 'error', 'message': 'Reminder not found'}

    except Exception as e:
        logger.error(f"Error sending reminder email {reminder_id}: {str(e)}")
        try:
            reminder = EventReminder.objects.get(id=reminder_id)
            reminder.email_error = str(e)
            reminder.save()
        except:
            pass

        # Retry the task
        raise self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes


@shared_task
def send_reminder_sms(reminder_id):
    """
    Send a reminder via SMS

    This is a placeholder for future SMS integration.
    Requires SMS provider setup (Twilio, Aliyun, etc.)
    """
    try:
        reminder = EventReminder.objects.get(id=reminder_id)

        # TODO: Implement SMS sending logic based on SMS_PROVIDER setting
        # For now, just log and mark as not sent
        logger.info(f"SMS reminder {reminder_id}: SMS provider not configured")
        reminder.sms_error = "SMS provider not configured"
        reminder.save()

        return {'status': 'pending', 'message': 'SMS provider not configured'}

    except Exception as e:
        logger.error(f"Error in SMS reminder {reminder_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_reminder_wechat(reminder_id):
    """
    Send a reminder via WeChat

    This is a placeholder for future WeChat integration.
    Requires WeChat Official Account API setup.
    """
    try:
        reminder = EventReminder.objects.get(id=reminder_id)

        # TODO: Implement WeChat sending logic
        # For now, just log and mark as not sent
        logger.info(f"WeChat reminder {reminder_id}: WeChat API not configured")
        reminder.wechat_error = "WeChat API not configured"
        reminder.save()

        return {'status': 'pending', 'message': 'WeChat API not configured'}

    except Exception as e:
        logger.error(f"Error in WeChat reminder {reminder_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def check_and_send_reminders():
    """
    Periodic task to check for reminders that need to be sent

    Runs every 5 minutes to check for pending reminders.
    """
    now = timezone.now()

    # Find reminders that should be sent now
    pending_reminders = EventReminder.objects.filter(
        sent=False,
        send_datetime__lte=now
    ).select_related('event')

    sent_count = 0

    for reminder in pending_reminders:
        logger.info(f"Processing reminder {reminder.id} for event {reminder.event.event_number}")

        # Send via configured channels
        if reminder.send_email and settings.EVENT_REMINDER_ENABLE_EMAIL:
            send_reminder_email.delay(reminder.id)
            sent_count += 1

        if reminder.send_sms and settings.EVENT_REMINDER_ENABLE_SMS:
            send_reminder_sms.delay(reminder.id)
            sent_count += 1

        if reminder.send_wechat and settings.EVENT_REMINDER_ENABLE_WECHAT:
            send_reminder_wechat.delay(reminder.id)
            sent_count += 1

    logger.info(f"Processed {len(pending_reminders)} reminders, sent {sent_count} notifications")
    return {'processed': len(pending_reminders), 'sent': sent_count}


@shared_task
def send_daily_event_digest():
    """
    Send daily digest of upcoming events to all staff

    Runs at 8 AM every day to notify staff of events happening today and this week.
    """
    today = timezone.now().date()
    week_from_now = today + timedelta(days=7)

    # Get events happening today
    events_today = Event.objects.filter(
        planned_start_date=today,
        status__in=['confirmed', 'in_progress']
    ).select_related('sales_responsible')

    # Get events happening this week
    events_this_week = Event.objects.filter(
        planned_start_date__gte=today,
        planned_start_date__lte=week_from_now,
        status__in=['planned', 'confirmed']
    ).exclude(id__in=events_today).select_related('sales_responsible')

    if not events_today and not events_this_week:
        logger.info("No events for daily digest")
        return {'status': 'success', 'message': 'No events to report'}

    # Prepare digest email
    subject = f"Daily Event Digest - {today.strftime('%B %d, %Y')}"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background-color: #0d6efd; color: white; padding: 20px; }}
            .section {{ margin: 20px 0; }}
            .event-item {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Daily Event Digest</h2>
            <p>{today.strftime('%B %d, %Y')}</p>
        </div>

        <div class="section">
            <h3>Events Today ({events_today.count()})</h3>
            {''.join([f'<div class="event-item"><strong>{event.event_number}</strong> - {event.customer_company}<br>Contact: {event.contact_person}<br>Responsible: {event.sales_responsible.get_full_name() if event.sales_responsible else "Unassigned"}</div>' for event in events_today])}
        </div>

        <div class="section">
            <h3>Events This Week ({events_this_week.count()})</h3>
            {''.join([f'<div class="event-item"><strong>{event.event_number}</strong> - {event.customer_company}<br>Start: {event.planned_start_date.strftime("%b %d")}<br>Responsible: {event.sales_responsible.get_full_name() if event.sales_responsible else "Unassigned"}</div>' for event in events_this_week])}
        </div>
    </body>
    </html>
    """

    plain_content = strip_tags(html_content)

    # Send to admin email
    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Daily digest sent: {events_today.count()} today, {events_this_week.count()} this week")
        return {'status': 'success', 'today': events_today.count(), 'week': events_this_week.count()}
    except Exception as e:
        logger.error(f"Error sending daily digest: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def check_overdue_events():
    """
    Check for events that are overdue and send alerts

    Runs every hour to check for events that should have been completed
    but are still marked as in_progress.
    """
    today = timezone.now().date()

    # Find events that are overdue
    overdue_events = Event.objects.filter(
        planned_end_date__lt=today,
        status='in_progress'
    ).select_related('sales_responsible')

    if not overdue_events:
        logger.info("No overdue events found")
        return {'status': 'success', 'overdue': 0}

    # Send alert email
    subject = f"Alert: {overdue_events.count()} Overdue Events"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background-color: #dc3545; color: white; padding: 20px; }}
            .event-item {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #dc3545; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>⚠️ Overdue Events Alert</h2>
        </div>

        <p>The following events are past their planned end date but still marked as "In Progress":</p>

        {''.join([f'<div class="event-item"><strong>{event.event_number}</strong> - {event.customer_company}<br>Planned End: {event.planned_end_date.strftime("%B %d, %Y")} ({(today - event.planned_end_date).days} days overdue)<br>Responsible: {event.sales_responsible.get_full_name() if event.sales_responsible else "Unassigned"}</div>' for event in overdue_events])}

        <p>Please review these events and update their status accordingly.</p>
    </body>
    </html>
    """

    plain_content = strip_tags(html_content)

    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Overdue events alert sent: {overdue_events.count()} events")
        return {'status': 'success', 'overdue': overdue_events.count()}
    except Exception as e:
        logger.error(f"Error sending overdue alert: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def auto_create_event_reminders(event_id):
    """
    Automatically create standard reminders for a new event

    Args:
        event_id: ID of the Event instance

    Creates reminders at standard intervals (7 days, 3 days, 1 day before event)
    """
    try:
        event = Event.objects.get(id=event_id)

        # Standard reminder templates
        reminder_templates = [
            {
                'days_before': 7,
                'type': 'checklist',
                'title': '1 Week Reminder: Pre-Event Checklist',
                'message': f'The event "{event.event_number}" for {event.customer_company} is scheduled in 1 week. Please review and complete the pre-event checklist.'
            },
            {
                'days_before': 3,
                'type': 'equipment',
                'title': '3 Days Reminder: Equipment Preparation',
                'message': f'The event "{event.event_number}" is in 3 days. Please verify all equipment is ready and checked out.'
            },
            {
                'days_before': 1,
                'type': 'safety',
                'title': '1 Day Reminder: Safety & Final Check',
                'message': f'The event "{event.event_number}" is tomorrow. Review safety protocols and conduct final preparations.'
            },
        ]

        created_count = 0

        for template in reminder_templates:
            send_datetime = timezone.make_aware(
                timezone.datetime.combine(
                    event.planned_start_date - timedelta(days=template['days_before']),
                    timezone.datetime.min.time()
                ).replace(hour=9)  # 9 AM
            )

            # Only create if send_datetime is in the future
            if send_datetime > timezone.now():
                reminder = EventReminder.objects.create(
                    event=event,
                    reminder_type=template['type'],
                    title=template['title'],
                    message=template['message'],
                    send_datetime=send_datetime,
                    send_email=True,
                    send_sms=False,
                    send_wechat=False,
                    created_by=event.sales_responsible
                )

                # Add recipients (assigned staff and sales responsible)
                if event.sales_responsible:
                    reminder.recipients.add(event.sales_responsible)

                reminder.recipients.add(*event.assigned_staff.all())

                created_count += 1
                logger.info(f"Created reminder for event {event.event_number}: {template['title']}")

        return {'status': 'success', 'created': created_count}

    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return {'status': 'error', 'message': 'Event not found'}
    except Exception as e:
        logger.error(f"Error creating reminders for event {event_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}
