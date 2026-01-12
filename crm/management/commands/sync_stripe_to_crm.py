# management/commands/sync_stripe_to_crm.py
"""
Sync Stripe customers to CRM customers.
Creates CRM customer records for Stripe customers that don't exist in CRM.
Links existing CRM customers to their Stripe accounts by email.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from crm.models import Customer
from stripe_integration.models import StripeCustomer, StripeSubscription


class Command(BaseCommand):
    help = 'Sync Stripe customers to CRM - create missing CRM records and link by email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create CRM customer records for Stripe customers that do not exist in CRM'
        )
        parser.add_argument(
            '--set-service-from-subscription',
            action='store_true',
            help='Set service_subscribed based on Stripe subscription plan name'
        )
        parser.add_argument(
            '--default-centre',
            type=str,
            default='hk',
            help='Default customer_centre for newly created customers (default: hk)'
        )
        parser.add_argument(
            '--default-service',
            type=str,
            default='',
            help='Default service_subscribed for newly created customers'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        create_missing = options['create_missing']
        set_service = options['set_service_from_subscription']
        default_centre = options['default_centre']
        default_service = options['default_service']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))

        # Statistics
        stats = {
            'stripe_customers': StripeCustomer.objects.count(),
            'crm_customers': Customer.objects.count(),
            'matched': 0,
            'created': 0,
            'updated_service': 0,
            'errors': 0,
        }

        self.stdout.write(f"\n=== Current Statistics ===")
        self.stdout.write(f"Stripe customers: {stats['stripe_customers']}")
        self.stdout.write(f"CRM customers: {stats['crm_customers']}")

        # Get all Stripe customers
        stripe_customers = StripeCustomer.objects.all()

        self.stdout.write(f"\n=== Processing Stripe Customers ===")

        with transaction.atomic():
            for stripe_cust in stripe_customers:
                email = stripe_cust.email.lower().strip() if stripe_cust.email else None
                if not email:
                    continue

                # Check if CRM customer exists with this email
                crm_customer = Customer.objects.filter(email_primary__iexact=email).first()

                if crm_customer:
                    stats['matched'] += 1
                    self.stdout.write(f"  Matched: {email}")

                    # Update service from subscription if requested
                    if set_service and not crm_customer.service_subscribed:
                        service = self.get_service_from_stripe(stripe_cust)
                        if service:
                            if dry_run:
                                self.stdout.write(f"    Would set service: {service}")
                            else:
                                crm_customer.service_subscribed = service
                                crm_customer.save(update_fields=['service_subscribed'])
                            stats['updated_service'] += 1

                elif create_missing:
                    # Create new CRM customer from Stripe data
                    self.stdout.write(f"  Creating: {email}")

                    # Parse name from Stripe
                    first_name, last_name = self.parse_name(stripe_cust.name)

                    # Get service from subscription
                    service = default_service
                    if set_service:
                        service = self.get_service_from_stripe(stripe_cust) or default_service

                    customer_data = {
                        'first_name': first_name or 'Unknown',
                        'last_name': last_name or 'Customer',
                        'email_primary': email,
                        'customer_type': 'individual',
                        'status': 'active',
                        'preferred_communication_method': 'email',
                        'customer_centre': default_centre,
                        'service_subscribed': service,
                    }

                    if dry_run:
                        self.stdout.write(f"    Would create: {customer_data}")
                    else:
                        try:
                            customer = Customer(**customer_data)
                            customer.full_clean()
                            customer.save()
                            stats['created'] += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"    Error creating: {e}"))
                            stats['errors'] += 1
                else:
                    self.stdout.write(f"  Not in CRM: {email} (use --create-missing to create)")

        # Final summary
        self.stdout.write(f"\n=== Sync Summary ===")
        self.stdout.write(f"Matched (existing in both): {stats['matched']}")
        self.stdout.write(f"Created in CRM: {stats['created']}")
        self.stdout.write(f"Services updated: {stats['updated_service']}")
        self.stdout.write(f"Errors: {stats['errors']}")

    def parse_name(self, full_name):
        """Parse full name into first and last name"""
        if not full_name:
            return None, None

        parts = full_name.strip().split()
        if len(parts) == 0:
            return None, None
        elif len(parts) == 1:
            return parts[0], None
        else:
            return parts[0], ' '.join(parts[1:])

    def get_service_from_stripe(self, stripe_customer):
        """Get service_subscribed based on Stripe subscription plan name"""
        # Get active subscriptions
        subscriptions = StripeSubscription.objects.filter(
            customer=stripe_customer,
            status='active'
        )

        for sub in subscriptions:
            plan_name = (sub.plan_name or '').lower()

            # Map plan names to service choices
            if 'blender' in plan_name:
                return 'blender_studio'
            elif 'origin' in plan_name:
                return 'origin_cg'
            elif 'institute' in plan_name or 'ki' in plan_name:
                return 'krystal_institute'
            elif 'technology' in plan_name or 'kt' in plan_name:
                return 'krystal_technology'
            elif 'cgge' in plan_name:
                return 'cgge'
            elif 'workshop' in plan_name:
                return 'workshop'
            elif 'mentor' in plan_name:
                return 'mentorship'
            elif 'corporate' in plan_name or 'training' in plan_name:
                return 'corporate_training'
            elif 'consult' in plan_name:
                return 'consulting'
            elif 'course' in plan_name or 'online' in plan_name:
                return 'online_course'

        return None
