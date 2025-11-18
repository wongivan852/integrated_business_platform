# email_service.py - Enhanced Email Service with Templates and Campaigns
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import Template, Context
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
from .models import (
    Customer, EmailTemplate, EmailCampaign, EmailLog, 
    EmailSubscription, CommunicationLog
)

logger = logging.getLogger('crm.communication')

class EmailTemplateService:
    """Service for managing email templates with variables"""
    
    def __init__(self):
        self.default_variables = {
            'first_name': 'Customer',
            'last_name': 'User',
            'full_name': 'Customer User',
            'email_primary': 'customer@example.com',
            'company_primary': 'Company Name',
            'institute_name': settings.INSTITUTE_NAME,
            'institute_email': settings.INSTITUTE_EMAIL,
            'institute_phone': settings.INSTITUTE_PHONE,
            'current_date': timezone.now().strftime('%Y-%m-%d'),
            'current_year': timezone.now().year,
        }
    
    def get_customer_variables(self, customer: Customer) -> Dict[str, Any]:
        """Extract template variables from customer object"""
        variables = {
            'first_name': customer.first_name or 'Customer',
            'last_name': customer.last_name or 'User',
            'full_name': customer.full_name or 'Customer User',
            'display_name': customer.display_name,
            'email_primary': customer.email_primary,
            'email_secondary': customer.email_secondary or '',
            'phone_primary': customer.phone_primary or '',
            'company_primary': customer.company_primary or '',
            'position_primary': customer.position_primary or '',
            'country_region': customer.get_country_region_display() or '',
            'preferred_name': customer.preferred_name or customer.first_name or 'Customer',
            'title': customer.title or '',
            'designation': customer.get_designation_display() or '',
        }
        
        # Add default variables
        variables.update(self.default_variables)
        
        return variables
    
    def render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Render template with variables using Django template engine"""
        try:
            # Replace double braces with Django template syntax if needed
            template_content = re.sub(r'\{\{(\w+)\}\}', r'{{ \1 }}', template_content)
            
            template = Template(template_content)
            context = Context(variables)
            return template.render(context)
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}")
            # Fallback to simple string replacement
            return self.simple_render(template_content, variables)
    
    def simple_render(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Simple template rendering with string replacement"""
        rendered = template_content
        for key, value in variables.items():
            rendered = rendered.replace(f'{{{key}}}', str(value))
            rendered = rendered.replace(f'{{{{{key}}}}}', str(value))  # Handle double braces
        return rendered
    
    def create_template(self, name: str, template_type: str, subject: str, 
                       content_text: str, content_html: str = '', 
                       created_by: str = '') -> EmailTemplate:
        """Create a new email template"""
        template = EmailTemplate.objects.create(
            name=name,
            template_type=template_type,
            subject=subject,
            content_text=content_text,
            content_html=content_html,
            created_by=created_by,
            status='active'
        )
        
        logger.info(f"Created email template: {template.name}")
        return template
    
    def get_template_by_type(self, template_type: str) -> Optional[EmailTemplate]:
        """Get the most recently updated active template by type"""
        return EmailTemplate.objects.filter(
            template_type=template_type,
            status='active'
        ).order_by('-updated_at').first()
    
    def validate_template_variables(self, template_content: str) -> List[str]:
        """Extract and validate template variables"""
        variables = re.findall(r'\{\{?(\w+)\}?\}', template_content)
        return list(set(variables))

class EmailCampaignService:
    """Service for managing email campaigns"""
    
    def __init__(self):
        self.template_service = EmailTemplateService()
    
    def get_campaign_recipients(self, campaign: EmailCampaign) -> List[Customer]:
        """Get recipients based on campaign target audience"""
        base_query = Customer.objects.filter(email_primary__isnull=False)
        
        # Apply audience filters
        if campaign.target_audience == 'all_customers':
            recipients = base_query.all()
        elif campaign.target_audience == 'active_customers':
            recipients = base_query.filter(status='active')
        elif campaign.target_audience == 'prospects':
            recipients = base_query.filter(status='prospect')
        elif campaign.target_audience == 'students':
            recipients = base_query.filter(customer_type='student')
        elif campaign.target_audience == 'corporate_clients':
            recipients = base_query.filter(customer_type='corporate')
        elif campaign.target_audience == 'newsletter_subscribers':
            # Get customers who are subscribed to newsletter
            subscribed_customers = EmailSubscription.objects.filter(
                subscription_type='newsletter',
                is_subscribed=True
            ).values_list('customer_id', flat=True)
            recipients = base_query.filter(id__in=subscribed_customers)
        elif campaign.target_audience == 'marketing_consent':
            recipients = base_query.filter(marketing_consent=True)
        elif campaign.target_audience == 'custom_filter':
            # Apply custom filter if provided
            if campaign.custom_filter:
                try:
                    filter_dict = json.loads(campaign.custom_filter) if isinstance(campaign.custom_filter, str) else campaign.custom_filter
                    recipients = base_query.filter(**filter_dict)
                except Exception as e:
                    logger.error(f"Custom filter error: {str(e)}")
                    recipients = base_query.none()
            else:
                recipients = base_query.none()
        else:
            recipients = base_query.none()
        
        return list(recipients)
    
    def create_campaign(self, name: str, description: str, template: EmailTemplate,
                       target_audience: str, custom_filter: Dict = None,
                       scheduled_at: datetime = None, created_by: str = '') -> EmailCampaign:
        """Create a new email campaign"""
        campaign = EmailCampaign.objects.create(
            name=name,
            description=description,
            template=template,
            subject=template.subject,
            content_text=template.content_text,
            content_html=template.content_html,
            target_audience=target_audience,
            custom_filter=custom_filter,
            scheduled_at=scheduled_at,
            created_by=created_by
        )
        
        # Calculate recipient count
        recipients = self.get_campaign_recipients(campaign)
        campaign.total_recipients = len(recipients)
        campaign.save()
        
        logger.info(f"Created email campaign: {campaign.name} with {campaign.total_recipients} recipients")
        return campaign
    
    def schedule_campaign(self, campaign: EmailCampaign, scheduled_at: datetime) -> bool:
        """Schedule a campaign for later sending"""
        try:
            campaign.scheduled_at = scheduled_at
            campaign.status = 'scheduled'
            campaign.save()
            
            logger.info(f"Scheduled campaign {campaign.name} for {scheduled_at}")
            return True
        except Exception as e:
            logger.error(f"Error scheduling campaign: {str(e)}")
            return False

class EnhancedEmailService:
    """Enhanced email service with template and campaign support"""
    
    def __init__(self):
        self.template_service = EmailTemplateService()
        self.campaign_service = EmailCampaignService()
    
    def send_template_email(self, customer: Customer, template: EmailTemplate,
                           additional_variables: Dict = None) -> Tuple[bool, str]:
        """Send email using a template with customer personalization"""
        try:
            # Get customer variables
            variables = self.template_service.get_customer_variables(customer)
            
            # Add any additional variables
            if additional_variables:
                variables.update(additional_variables)
            
            # Render template content
            subject = self.template_service.render_template(template.subject, variables)
            content_text = self.template_service.render_template(template.content_text, variables)
            content_html = self.template_service.render_template(template.content_html, variables) if template.content_html else None
            
            # Send email
            success, message = self.send_email(
                customer=customer,
                subject=subject,
                content_text=content_text,
                content_html=content_html,
                template=template
            )
            
            if success:
                # Update template usage
                template.increment_usage()
            
            return success, message
            
        except Exception as e:
            error_msg = f"Template email error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def send_email(self, customer: Customer, subject: str, content_text: str,
                   content_html: str = None, template: EmailTemplate = None,
                   campaign: EmailCampaign = None) -> Tuple[bool, str]:
        """Send individual email with full logging and tracking"""
        
        # Create email log entry
        email_log = EmailLog.objects.create(
            customer=customer,
            campaign=campaign,
            template=template,
            recipient_email=customer.email_primary,
            subject=subject,
            content_text=content_text,
            content_html=content_html or '',
            status='queued'
        )
        
        try:
            # Check if customer has unsubscribed from this type of email
            if campaign and not self.check_subscription_status(customer, 'marketing'):
                email_log.update_status('failed', 'Customer unsubscribed from marketing emails')
                return False, "Customer unsubscribed"
            
            # Update status to sending
            email_log.update_status('sending')
            
            # Send email using Django's email backend
            connection = get_connection()
            msg = EmailMultiAlternatives(
                subject=subject,
                body=content_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[customer.email_primary],
                connection=connection
            )
            
            if content_html:
                msg.attach_alternative(content_html, "text/html")
            
            # Add tracking headers
            msg.extra_headers['X-Email-Log-ID'] = str(email_log.id)
            if campaign:
                msg.extra_headers['X-Campaign-ID'] = str(campaign.id)
            
            result = msg.send()
            
            if result > 0:
                email_log.update_status('sent')
                
                # Update campaign metrics
                if campaign:
                    campaign.emails_sent += 1
                    campaign.save()
                
                # Log communication
                CommunicationLog.objects.create(
                    customer=customer,
                    channel='email',
                    subject=subject,
                    content=content_text,
                    external_message_id=str(email_log.id),
                    is_outbound=True
                )
                
                logger.info(f"Email sent successfully to {customer.email_primary}")
                return True, "Email sent successfully"
            else:
                email_log.update_status('failed', 'Email send failed - no messages sent')
                return False, "Email send failed"
                
        except Exception as e:
            error_msg = f"Email send error: {str(e)}"
            email_log.update_status('failed', error_msg)
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def send_campaign(self, campaign: EmailCampaign) -> Dict[str, Any]:
        """Send email campaign to all recipients"""
        results = {
            'total_recipients': 0,
            'emails_sent': 0,
            'emails_failed': 0,
            'errors': []
        }
        
        try:
            # Update campaign status
            campaign.status = 'sending'
            campaign.save()
            
            # Get recipients
            recipients = self.campaign_service.get_campaign_recipients(campaign)
            results['total_recipients'] = len(recipients)
            
            logger.info(f"Starting campaign {campaign.name} to {len(recipients)} recipients")
            
            # Send emails with transaction handling
            with transaction.atomic():
                for customer in recipients:
                    try:
                        success, message = self.send_email(
                            customer=customer,
                            subject=campaign.subject,
                            content_text=campaign.content_text,
                            content_html=campaign.content_html,
                            template=campaign.template,
                            campaign=campaign
                        )
                        
                        if success:
                            results['emails_sent'] += 1
                        else:
                            results['emails_failed'] += 1
                            results['errors'].append(f"{customer.email_primary}: {message}")
                            
                    except Exception as e:
                        results['emails_failed'] += 1
                        error_msg = f"{customer.email_primary}: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(f"Campaign email error: {error_msg}")
            
            # Update campaign status and metrics
            campaign.status = 'sent'
            campaign.sent_at = timezone.now()
            campaign.emails_sent = results['emails_sent']
            campaign.emails_failed = results['emails_failed']
            campaign.save()
            
            logger.info(f"Campaign {campaign.name} completed: {results['emails_sent']} sent, {results['emails_failed']} failed")
            
        except Exception as e:
            campaign.status = 'failed'
            campaign.save()
            error_msg = f"Campaign send error: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg, exc_info=True)
        
        return results
    
    def check_subscription_status(self, customer: Customer, subscription_type: str) -> bool:
        """Check if customer is subscribed to a specific type of email"""
        try:
            subscription = EmailSubscription.objects.get(
                customer=customer,
                subscription_type=subscription_type
            )
            return subscription.is_subscribed
        except EmailSubscription.DoesNotExist:
            # If no subscription record exists, check customer preferences
            if subscription_type == 'marketing':
                return customer.marketing_consent
            elif subscription_type == 'newsletter':
                return customer.newsletter_subscription
            else:
                return True  # Default to subscribed for system notifications
    
    def unsubscribe_customer(self, customer: Customer, subscription_type: str, reason: str = '') -> bool:
        """Unsubscribe customer from specific email type"""
        try:
            subscription, created = EmailSubscription.objects.get_or_create(
                customer=customer,
                subscription_type=subscription_type,
                defaults={'is_subscribed': True}
            )
            
            if subscription.is_subscribed:
                subscription.unsubscribe(reason)
                logger.info(f"Unsubscribed {customer.email_primary} from {subscription_type}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Unsubscribe error: {str(e)}")
            return False
    
    def get_email_analytics(self, campaign: EmailCampaign = None, 
                           days: int = 30) -> Dict[str, Any]:
        """Get email analytics for campaigns or overall performance"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        query = EmailLog.objects.filter(queued_at__gte=start_date)
        if campaign:
            query = query.filter(campaign=campaign)
        
        stats = query.aggregate(
            total_queued=Count('id'),
            total_sent=Count('id', filter=Q(status__in=['sent', 'delivered', 'opened', 'clicked'])),
            total_delivered=Count('id', filter=Q(status__in=['delivered', 'opened', 'clicked'])),
            total_opened=Count('id', filter=Q(status__in=['opened', 'clicked'])),
            total_clicked=Count('id', filter=Q(status='clicked')),
            total_bounced=Count('id', filter=Q(status='bounced')),
            total_failed=Count('id', filter=Q(status='failed'))
        )
        
        # Calculate rates
        sent = stats['total_sent'] or 0
        delivered = stats['total_delivered'] or 0
        
        analytics = {
            'period_days': days,
            'total_emails': stats['total_queued'],
            'sent': sent,
            'delivered': delivered,
            'opened': stats['total_opened'],
            'clicked': stats['total_clicked'],
            'bounced': stats['total_bounced'],
            'failed': stats['total_failed'],
            'delivery_rate': round((delivered / sent * 100), 2) if sent > 0 else 0,
            'open_rate': round((stats['total_opened'] / delivered * 100), 2) if delivered > 0 else 0,
            'click_rate': round((stats['total_clicked'] / delivered * 100), 2) if delivered > 0 else 0,
            'bounce_rate': round((stats['total_bounced'] / sent * 100), 2) if sent > 0 else 0,
        }
        
        return analytics

# Convenience functions for common email operations
def send_welcome_email(customer: Customer) -> Tuple[bool, str]:
    """Send welcome email to new customer"""
    service = EnhancedEmailService()
    template = service.template_service.get_template_by_type('welcome')
    
    if template:
        return service.send_template_email(customer, template)
    else:
        # Fallback to simple email
        subject = f"Welcome to {settings.INSTITUTE_NAME}!"
        content = f"""
Dear {customer.first_name or 'Customer'},

Welcome to our learning community! We're excited to have you join us.

You can explore our courses and upcoming conferences through our platform.

If you have any questions, feel free to reach out to us.

Best regards,
{settings.INSTITUTE_NAME} Team
        """
        return service.send_email(customer, subject, content)

def send_course_reminder(customer: Customer, course, **kwargs) -> Tuple[bool, str]:
    """Send course reminder email"""
    service = EnhancedEmailService()
    template = service.template_service.get_template_by_type('course_reminder')
    
    additional_variables = {
        'course_title': course.title,
        'course_start_date': course.start_date.strftime('%Y-%m-%d %H:%M'),
        'course_duration': course.duration_hours,
        **kwargs
    }
    
    if template:
        return service.send_template_email(customer, template, additional_variables)
    else:
        # Fallback to simple email
        subject = f"Reminder: {course.title} starts soon!"
        content = f"""
Dear {customer.first_name or 'Customer'},

This is a reminder that your course "{course.title}" is starting soon.

Start Date: {course.start_date.strftime('%Y-%m-%d %H:%M')}
Duration: {course.duration_hours} hours

Please ensure you're prepared for the session.

Best regards,
{settings.INSTITUTE_NAME} Team
        """
        return service.send_email(customer, subject, content)