"""
Management command to populate customer_centre and service_subscribed fields
for existing customers based on their country_region and source data.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from crm.models import Customer


class Command(BaseCommand):
    help = 'Populate customer_centre and service_subscribed fields for existing customers'

    # Mapping from country_region to customer_centre
    COUNTRY_TO_CENTRE = {
        # Asia Pacific
        'HK': 'hk', 'Hong Kong': 'hk', 'Hong Kong SAR': 'hk',
        'CN': 'cn', 'China': 'cn', 'Mainland China': 'cn', 'PRC': 'cn',
        'SG': 'sg', 'Singapore': 'sg',
        'TW': 'tw', 'Taiwan': 'tw', 'Taiwan, Province of China': 'tw',
        'MY': 'my', 'Malaysia': 'my',
        'TH': 'th', 'Thailand': 'th',
        'VN': 'vn', 'Vietnam': 'vn', 'Viet Nam': 'vn',
        'ID': 'id', 'Indonesia': 'id',
        'PH': 'ph', 'Philippines': 'ph',
        'JP': 'jp', 'Japan': 'jp',
        'KR': 'kr', 'Korea': 'kr', 'South Korea': 'kr', 'Korea, Republic of': 'kr',
        'AU': 'au', 'Australia': 'au',
        'NZ': 'nz', 'New Zealand': 'nz',
        # Europe
        'UK': 'uk', 'United Kingdom': 'uk', 'GB': 'uk', 'Great Britain': 'uk', 'England': 'uk',
        'DE': 'eu', 'Germany': 'eu',
        'FR': 'eu', 'France': 'eu',
        'IT': 'eu', 'Italy': 'eu',
        'ES': 'eu', 'Spain': 'eu',
        'NL': 'eu', 'Netherlands': 'eu',
        'BE': 'eu', 'Belgium': 'eu',
        'AT': 'eu', 'Austria': 'eu',
        'CH': 'eu', 'Switzerland': 'eu',
        'SE': 'eu', 'Sweden': 'eu',
        'NO': 'eu', 'Norway': 'eu',
        'DK': 'eu', 'Denmark': 'eu',
        'FI': 'eu', 'Finland': 'eu',
        'PL': 'eu', 'Poland': 'eu',
        'PT': 'eu', 'Portugal': 'eu',
        'IE': 'eu', 'Ireland': 'eu',
        # Americas
        'US': 'us', 'United States': 'us', 'USA': 'us', 'United States of America': 'us',
        'CA': 'us', 'Canada': 'us',  # Map to US centre for North America
    }

    # Mapping from source to service_subscribed
    SOURCE_TO_SERVICE = {
        'youtube': 'cgge',
        'youtube_import': 'cgge',
        'instagram': 'cgge',
        'facebook': 'cgge',
        'social_media': 'cgge',
        'google_search': 'online_course',
        'google_ads': 'online_course',
        'website': 'krystal_institute',
        'stripe_import': 'online_course',  # Stripe customers likely purchased online
        'conference': 'workshop',
        'referral': 'mentorship',
        'word_of_mouth': 'mentorship',
        'email_marketing': 'online_course',
        'csv_import': 'krystal_institute',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing values (default: only populate empty fields)',
        )
        parser.add_argument(
            '--centre-only',
            action='store_true',
            help='Only populate customer_centre field',
        )
        parser.add_argument(
            '--service-only',
            action='store_true',
            help='Only populate service_subscribed field',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        centre_only = options['centre_only']
        service_only = options['service_only']

        self.stdout.write(self.style.NOTICE('Starting customer centre/service population...'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get customers to update
        customers = Customer.objects.all()
        total = customers.count()

        self.stdout.write(f'Total customers: {total}')

        centre_updated = 0
        service_updated = 0
        skipped = 0

        with transaction.atomic():
            for customer in customers:
                changes_made = False

                # Update customer_centre based on country_region
                if not service_only:
                    if force or not customer.customer_centre:
                        country = customer.country_region
                        if country:
                            # Try exact match first
                            centre = self.COUNTRY_TO_CENTRE.get(country)

                            # Try case-insensitive match
                            if not centre:
                                for key, value in self.COUNTRY_TO_CENTRE.items():
                                    if key.lower() == country.lower():
                                        centre = value
                                        break

                            if centre:
                                if customer.customer_centre != centre:
                                    if not dry_run:
                                        customer.customer_centre = centre
                                    centre_updated += 1
                                    changes_made = True
                                    self.stdout.write(
                                        f'  {customer.email_primary}: country={country} -> centre={centre}'
                                    )

                # Update service_subscribed based on source
                if not centre_only:
                    if force or not customer.service_subscribed:
                        source = customer.source
                        if source:
                            service = self.SOURCE_TO_SERVICE.get(source)
                            if service:
                                if customer.service_subscribed != service:
                                    if not dry_run:
                                        customer.service_subscribed = service
                                    service_updated += 1
                                    changes_made = True
                                    self.stdout.write(
                                        f'  {customer.email_primary}: source={source} -> service={service}'
                                    )

                if changes_made and not dry_run:
                    customer.save(update_fields=['customer_centre', 'service_subscribed'])
                elif not changes_made:
                    skipped += 1

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Total customers processed: {total}')
        self.stdout.write(f'Customer centres updated: {centre_updated}')
        self.stdout.write(f'Services subscribed updated: {service_updated}')
        self.stdout.write(f'Skipped (no changes needed): {skipped}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No actual changes were made'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))
        else:
            self.stdout.write(self.style.SUCCESS('\nChanges have been saved to database'))

        # Show current stats
        self.stdout.write('')
        self.stdout.write('Current field population stats:')
        with_centre = Customer.objects.exclude(customer_centre='').exclude(customer_centre__isnull=True).count()
        with_service = Customer.objects.exclude(service_subscribed='').exclude(service_subscribed__isnull=True).count()
        self.stdout.write(f'  Customers with customer_centre: {with_centre}/{total}')
        self.stdout.write(f'  Customers with service_subscribed: {with_service}/{total}')
