from django.core.management.base import BaseCommand
from crm.models import Customer

class Command(BaseCommand):
    help = 'Add a YouTuber with only @handle required'

    def add_arguments(self, parser):
        parser.add_argument('youtube_handle', type=str, help='YouTube handle (with or without @)')

    def handle(self, *args, **options):
        youtube_handle = options['youtube_handle'].lstrip('@')

        try:
            # Create YouTuber customer with minimal data
            customer = Customer(
                customer_type='youtuber',
                youtube_handle=youtube_handle
            )
            
            # The clean() method will auto-generate all required fields
            customer.full_clean()
            customer.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ YouTuber created successfully!')
            )
            self.stdout.write(f'   Generated Name: {customer.first_name} {customer.last_name}')
            if customer.email_primary:
                self.stdout.write(f'   Email: {customer.email_primary}')
            else:
                self.stdout.write(f'   Email: Not provided (optional)')
            self.stdout.write(f'   YouTube Handle: @{customer.youtube_handle}')
            self.stdout.write(f'   YouTube URL: {customer.youtube_channel_url}')
            self.stdout.write(f'   Customer Type: {customer.get_customer_type_display()}')
            self.stdout.write(f'   Status: {customer.get_status_display()}')
            self.stdout.write(f'   Customer ID: {customer.id}')
            
        except Exception as e:
            error_msg = str(e)
            if 'already used by' in error_msg:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Duplicate YouTube handle: {error_msg}')
                )
                # Show existing customer info
                try:
                    existing = Customer.objects.get(youtube_handle__iexact=youtube_handle)
                    self.stdout.write(f'   Existing customer: {existing.first_name} {existing.last_name}')
                    if existing.email_primary:
                        self.stdout.write(f'   Email: {existing.email_primary}')
                    self.stdout.write(f'   Created: {existing.created_at.strftime("%Y-%m-%d %H:%M")}')
                    self.stdout.write(f'   Customer ID: {existing.id}')
                except:
                    pass
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create YouTuber: {error_msg}')
                )