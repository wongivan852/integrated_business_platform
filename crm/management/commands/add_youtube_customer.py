from django.core.management.base import BaseCommand
from crm.models import Customer
import uuid

class Command(BaseCommand):
    help = 'Add a customer with YouTube data directly'

    def add_arguments(self, parser):
        parser.add_argument('youtube_handle', type=str, help='YouTube handle (with or without @)')
        parser.add_argument('--first-name', type=str, default='YouTube', help='First name')
        parser.add_argument('--last-name', type=str, default='User', help='Last name')
        parser.add_argument('--email', type=str, help='Email address (auto-generated if not provided)')

    def handle(self, *args, **options):
        youtube_handle = options['youtube_handle'].lstrip('@')
        first_name = options['first_name']
        last_name = options['last_name']
        email = options['email'] or f'youtube_{youtube_handle}@example.com'

        try:
            # Create customer
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email_primary=email,
                customer_type='individual',
                status='prospect',
                preferred_communication_method='email',
                youtube_handle=youtube_handle
            )
            
            # Validate and save
            customer.full_clean()
            customer.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully created customer:')
            )
            self.stdout.write(f'   Name: {customer.first_name} {customer.last_name}')
            self.stdout.write(f'   Email: {customer.email_primary}')
            self.stdout.write(f'   YouTube Handle: @{customer.youtube_handle}')
            self.stdout.write(f'   YouTube URL: {customer.youtube_channel_url}')
            self.stdout.write(f'   Customer ID: {customer.id}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create customer: {str(e)}')
            )