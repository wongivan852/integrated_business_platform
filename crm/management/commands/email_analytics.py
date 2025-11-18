# management/commands/email_analytics.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from crm.models import EmailCampaign, EmailLog
from crm.email_service import EnhancedEmailService
from datetime import timedelta

class Command(BaseCommand):
    help = 'Display email analytics and campaign performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)',
        )
        parser.add_argument(
            '--campaign-id',
            type=str,
            help='Analyze specific campaign',
        )
        parser.add_argument(
            '--export-csv',
            type=str,
            help='Export analytics to CSV file',
        )
    
    def handle(self, *args, **options):
        email_service = EnhancedEmailService()
        days = options['days']
        
        if options['campaign_id']:
            # Analyze specific campaign
            try:
                campaign = EmailCampaign.objects.get(id=options['campaign_id'])
                analytics = email_service.get_email_analytics(campaign=campaign, days=days)
                self.display_campaign_analytics(campaign, analytics)
            except EmailCampaign.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Campaign with ID {options["campaign_id"]} does not exist')
                )
        else:
            # Overall analytics
            analytics = email_service.get_email_analytics(days=days)
            self.display_overall_analytics(analytics, days)
        
        if options['export_csv']:
            self.export_to_csv(options['export_csv'], analytics)
    
    def display_overall_analytics(self, analytics, days):
        """Display overall email analytics"""
        self.stdout.write(
            self.style.SUCCESS(f'\n=== Email Analytics (Last {days} days) ===')
        )
        
        self.stdout.write(f'Total Emails: {analytics["total_emails"]}')
        self.stdout.write(f'Sent: {analytics["sent"]}')
        self.stdout.write(f'Delivered: {analytics["delivered"]}')
        self.stdout.write(f'Opened: {analytics["opened"]}')
        self.stdout.write(f'Clicked: {analytics["clicked"]}')
        self.stdout.write(f'Bounced: {analytics["bounced"]}')
        self.stdout.write(f'Failed: {analytics["failed"]}')
        
        self.stdout.write('\n=== Performance Rates ===')
        self.stdout.write(f'Delivery Rate: {analytics["delivery_rate"]}%')
        self.stdout.write(f'Open Rate: {analytics["open_rate"]}%')
        self.stdout.write(f'Click Rate: {analytics["click_rate"]}%')
        self.stdout.write(f'Bounce Rate: {analytics["bounce_rate"]}%')
        
        # Recent campaigns
        recent_campaigns = EmailCampaign.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=days)
        ).order_by('-created_at')[:5]
        
        if recent_campaigns:
            self.stdout.write('\n=== Recent Campaigns ===')
            for campaign in recent_campaigns:
                self.stdout.write(
                    f'{campaign.name}: {campaign.emails_sent} sent, '
                    f'{campaign.open_rate}% open rate'
                )
    
    def display_campaign_analytics(self, campaign, analytics):
        """Display analytics for specific campaign"""
        self.stdout.write(
            self.style.SUCCESS(f'\n=== Campaign Analytics: {campaign.name} ===')
        )
        
        self.stdout.write(f'Campaign Status: {campaign.get_status_display()}')
        self.stdout.write(f'Target Audience: {campaign.get_target_audience_display()}')
        self.stdout.write(f'Created: {campaign.created_at.strftime("%Y-%m-%d %H:%M")}')
        
        if campaign.sent_at:
            self.stdout.write(f'Sent: {campaign.sent_at.strftime("%Y-%m-%d %H:%M")}')
        
        self.stdout.write('\n=== Campaign Metrics ===')
        self.stdout.write(f'Total Recipients: {campaign.total_recipients}')
        self.stdout.write(f'Emails Sent: {campaign.emails_sent}')
        self.stdout.write(f'Emails Delivered: {campaign.emails_delivered}')
        self.stdout.write(f'Emails Opened: {campaign.emails_opened}')
        self.stdout.write(f'Emails Clicked: {campaign.emails_clicked}')
        self.stdout.write(f'Emails Bounced: {campaign.emails_bounced}')
        self.stdout.write(f'Emails Failed: {campaign.emails_failed}')
        
        self.stdout.write('\n=== Performance Rates ===')
        self.stdout.write(f'Open Rate: {campaign.open_rate}%')
        self.stdout.write(f'Click Rate: {campaign.click_rate}%')
        self.stdout.write(f'Bounce Rate: {campaign.bounce_rate}%')
    
    def export_to_csv(self, filename, analytics):
        """Export analytics to CSV file"""
        import csv
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Metric', 'Value'])
                
                for key, value in analytics.items():
                    writer.writerow([key.replace('_', ' ').title(), value])
            
            self.stdout.write(
                self.style.SUCCESS(f'Analytics exported to {filename}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Export failed: {str(e)}')
            )