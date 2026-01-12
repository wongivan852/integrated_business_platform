# management/commands/bulk_update_customer_fields.py
"""
Bulk update customer_centre and service_subscribed fields for existing customers.
Can update based on country_region or from CSV file.
"""
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from crm.models import Customer


class Command(BaseCommand):
    help = 'Bulk update customer_centre and service_subscribed fields for existing customers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-country',
            action='store_true',
            help='Set customer_centre based on country_region field'
        )
        parser.add_argument(
            '--from-csv',
            type=str,
            help='Path to CSV file with email, customer_centre, service_subscribed columns'
        )
        parser.add_argument(
            '--default-centre',
            type=str,
            default='',
            help='Default customer_centre for customers without country_region'
        )
        parser.add_argument(
            '--default-service',
            type=str,
            default='',
            help='Default service_subscribed for all customers without one'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )
        parser.add_argument(
            '--only-empty',
            action='store_true',
            default=True,
            help='Only update customers with empty customer_centre/service_subscribed'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_empty = options['only_empty']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))

        # Statistics
        stats = {
            'total_customers': Customer.objects.count(),
            'empty_centre': Customer.objects.filter(customer_centre='').count(),
            'empty_service': Customer.objects.filter(service_subscribed='').count(),
            'updated_centre': 0,
            'updated_service': 0,
            'errors': 0,
        }

        self.stdout.write(f"\n=== Current Statistics ===")
        self.stdout.write(f"Total customers: {stats['total_customers']}")
        self.stdout.write(f"Customers with empty customer_centre: {stats['empty_centre']}")
        self.stdout.write(f"Customers with empty service_subscribed: {stats['empty_service']}")

        if options['from_country']:
            stats = self.update_from_country(stats, dry_run, only_empty, options['default_centre'])

        if options['from_csv']:
            stats = self.update_from_csv(options['from_csv'], stats, dry_run, only_empty)

        if options['default_service']:
            stats = self.set_default_service(options['default_service'], stats, dry_run, only_empty)

        # Final summary
        self.stdout.write(f"\n=== Update Summary ===")
        self.stdout.write(f"Customer centres updated: {stats['updated_centre']}")
        self.stdout.write(f"Services subscribed updated: {stats['updated_service']}")
        self.stdout.write(f"Errors: {stats['errors']}")

    def update_from_country(self, stats, dry_run, only_empty, default_centre):
        """Update customer_centre based on country_region field"""
        self.stdout.write(f"\n=== Updating customer_centre from country_region ===")

        # Mapping from country_region to customer_centre
        country_to_centre = {
            'CN': 'cn',
            'HK': 'hk',
            'TW': 'tw',
            'MO': 'hk',  # Macau -> Hong Kong centre
            'SG': 'sg',
            'MY': 'my',
            'TH': 'th',
            'VN': 'vn',
            'PH': 'ph',
            'ID': 'id',
            'KR': 'kr',
            'JP': 'jp',
            'IN': 'sg',  # India -> Singapore centre
            'AU': 'au',
            'NZ': 'nz',
            'GB': 'uk',
            'DE': 'eu',
            'FR': 'eu',
            'IT': 'eu',
            'ES': 'eu',
            'NL': 'eu',
            'BE': 'eu',
            'CH': 'eu',
            'AT': 'eu',
            'SE': 'eu',
            'NO': 'eu',
            'DK': 'eu',
            'FI': 'eu',
            'US': 'us',
            'CA': 'us',  # Canada -> US centre
            'MX': 'us',  # Mexico -> US centre
            'BR': 'other',
            'AR': 'other',
            'CL': 'other',
            'CO': 'other',
            'PE': 'other',
            'AE': 'other',
            'SA': 'other',
            'IL': 'other',
            'ZA': 'other',
            'EG': 'other',
            'KE': 'other',
            'NG': 'other',
            'RU': 'other',
            'TR': 'other',
        }

        # Get customers to update
        if only_empty:
            customers = Customer.objects.filter(customer_centre='')
        else:
            customers = Customer.objects.all()

        with transaction.atomic():
            for customer in customers:
                if customer.country_region:
                    new_centre = country_to_centre.get(customer.country_region, default_centre)
                    if new_centre and new_centre != customer.customer_centre:
                        if dry_run:
                            self.stdout.write(
                                f"  Would update {customer.email_primary}: "
                                f"country={customer.country_region} -> centre={new_centre}"
                            )
                        else:
                            customer.customer_centre = new_centre
                            customer.save(update_fields=['customer_centre'])
                        stats['updated_centre'] += 1
                elif default_centre:
                    if dry_run:
                        self.stdout.write(
                            f"  Would set default centre for {customer.email_primary}: {default_centre}"
                        )
                    else:
                        customer.customer_centre = default_centre
                        customer.save(update_fields=['customer_centre'])
                    stats['updated_centre'] += 1

        return stats

    def update_from_csv(self, csv_path, stats, dry_run, only_empty):
        """Update fields from CSV file with email, customer_centre, service_subscribed columns"""
        self.stdout.write(f"\n=== Updating from CSV: {csv_path} ===")

        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                with transaction.atomic():
                    for row in reader:
                        email = row.get('email', row.get('Email', row.get('email_primary', ''))).strip()
                        centre = row.get('customer_centre', row.get('Customer Centre', row.get('centre', row.get('region', '')))).strip().lower()
                        service = row.get('service_subscribed', row.get('Service Subscribed', row.get('service', ''))).strip().lower()

                        if not email:
                            continue

                        try:
                            customer = Customer.objects.get(email_primary=email)
                            updated = False

                            # Update centre
                            if centre and (not only_empty or not customer.customer_centre):
                                mapped_centre = self.map_centre(centre)
                                if mapped_centre:
                                    if dry_run:
                                        self.stdout.write(f"  Would update {email}: centre={mapped_centre}")
                                    else:
                                        customer.customer_centre = mapped_centre
                                        updated = True
                                    stats['updated_centre'] += 1

                            # Update service
                            if service and (not only_empty or not customer.service_subscribed):
                                mapped_service = self.map_service(service)
                                if mapped_service:
                                    if dry_run:
                                        self.stdout.write(f"  Would update {email}: service={mapped_service}")
                                    else:
                                        customer.service_subscribed = mapped_service
                                        updated = True
                                    stats['updated_service'] += 1

                            if updated and not dry_run:
                                customer.save()

                        except Customer.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f"  Customer not found: {email}"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  Error updating {email}: {e}"))
                            stats['errors'] += 1

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading CSV: {e}"))

        return stats

    def set_default_service(self, default_service, stats, dry_run, only_empty):
        """Set default service_subscribed for customers without one"""
        self.stdout.write(f"\n=== Setting default service: {default_service} ===")

        mapped_service = self.map_service(default_service)
        if not mapped_service:
            self.stdout.write(self.style.ERROR(f"Invalid service: {default_service}"))
            return stats

        if only_empty:
            customers = Customer.objects.filter(service_subscribed='')
        else:
            customers = Customer.objects.all()

        with transaction.atomic():
            for customer in customers:
                if dry_run:
                    self.stdout.write(f"  Would set service for {customer.email_primary}: {mapped_service}")
                else:
                    customer.service_subscribed = mapped_service
                    customer.save(update_fields=['service_subscribed'])
                stats['updated_service'] += 1

        return stats

    def map_centre(self, value):
        """Map various centre names to valid choices"""
        if not value:
            return ''
        mapping = {
            'hk': 'hk', 'hong kong': 'hk',
            'cn': 'cn', 'china': 'cn', 'china mainland': 'cn',
            'sg': 'sg', 'singapore': 'sg',
            'tw': 'tw', 'taiwan': 'tw',
            'my': 'my', 'malaysia': 'my',
            'th': 'th', 'thailand': 'th',
            'vn': 'vn', 'vietnam': 'vn',
            'id': 'id', 'indonesia': 'id',
            'ph': 'ph', 'philippines': 'ph',
            'jp': 'jp', 'japan': 'jp',
            'kr': 'kr', 'korea': 'kr',
            'au': 'au', 'australia': 'au',
            'nz': 'nz', 'new zealand': 'nz',
            'uk': 'uk', 'united kingdom': 'uk', 'gb': 'uk',
            'us': 'us', 'united states': 'us', 'usa': 'us',
            'eu': 'eu', 'europe': 'eu',
            'other': 'other',
        }
        return mapping.get(value.lower(), '')

    def map_service(self, value):
        """Map various service names to valid choices"""
        if not value:
            return ''
        mapping = {
            'blender_studio': 'blender_studio', 'blender studio': 'blender_studio', 'blender': 'blender_studio',
            'origin_cg': 'origin_cg', 'origin cg': 'origin_cg', 'origin': 'origin_cg',
            'krystal_institute': 'krystal_institute', 'krystal institute': 'krystal_institute', 'ki': 'krystal_institute',
            'krystal_technology': 'krystal_technology', 'krystal technology': 'krystal_technology', 'kt': 'krystal_technology',
            'cgge': 'cgge',
            'online_course': 'online_course', 'online course': 'online_course', 'online': 'online_course',
            'workshop': 'workshop',
            'mentorship': 'mentorship', 'mentorship program': 'mentorship',
            'corporate_training': 'corporate_training', 'corporate training': 'corporate_training', 'corporate': 'corporate_training',
            'consulting': 'consulting',
            'other': 'other',
        }
        return mapping.get(value.lower(), '')
