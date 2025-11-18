# management/commands/send_email_campaign.py
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from crm.models import EmailCampaign
from crm.email_service import EnhancedEmailService
import logging

logger = logging.getLogger('crm.communication')

class Command(BaseCommand):
    help = 'Send email campaigns (scheduled or manual)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--campaign-id',
            type=str,
            help='Send specific campaign by ID',
        )
        parser.add_argument(
            '--send-scheduled',
            action='store_true',
            help='Send all scheduled campaigns that are due',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )
    
    def handle(self, *args, **options):
        email_service = EnhancedEmailService()
        
        if options['campaign_id']:
            # Send specific campaign
            try:
                campaign = EmailCampaign.objects.get(id=options['campaign_id'])
                self.send_campaign(email_service, campaign, options['dry_run'])
            except EmailCampaign.DoesNotExist:
                raise CommandError(f'Campaign with ID {options["campaign_id"]} does not exist')
        
        elif options['send_scheduled']:
            # Send scheduled campaigns
            scheduled_campaigns = EmailCampaign.objects.filter(
                status='scheduled',
                scheduled_at__lte=timezone.now()
            )
            
            if not scheduled_campaigns.exists():
                self.stdout.write(self.style.SUCCESS('No scheduled campaigns to send'))
                return
            
            for campaign in scheduled_campaigns:
                self.send_campaign(email_service, campaign, options['dry_run'])
        
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --campaign-id or --send-scheduled')
            )
    
    def send_campaign(self, email_service, campaign, dry_run=False):
        """Send a single campaign"""
        recipients = email_service.campaign_service.get_campaign_recipients(campaign)
        
        self.stdout.write(
            f'Campaign: {campaign.name} ({len(recipients)} recipients)'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would send to {len(recipients)} recipients')
            )
            for recipient in recipients[:5]:  # Show first 5
                self.stdout.write(f'  - {recipient.email_primary}')
            if len(recipients) > 5:
                self.stdout.write(f'  ... and {len(recipients) - 5} more')
            return
        
        # Actually send the campaign
        results = email_service.send_campaign(campaign)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Campaign sent: {results["emails_sent"]} successful, '
                f'{results["emails_failed"]} failed'
            )
        )
        
        if results['errors']:
            self.stdout.write(self.style.ERROR('Errors:'))
            for error in results['errors'][:10]:  # Show first 10 errors
                self.stdout.write(f'  - {error}')