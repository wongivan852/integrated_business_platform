"""
Create sample expense claims for testing.

This command creates 2 sample expense claims based on the original
FastAPI version's seed data, adapted for Django models.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from expense_claims.models import (
    Company, ExpenseCategory, Currency, ExpenseClaim, ExpenseItem, ExchangeRate
)
from authentication.models import CompanyUser


class Command(BaseCommand):
    help = 'Create sample expense claims for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing sample claims before creating new ones',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating sample expense claims...'))

        if options['clear']:
            self.clear_sample_claims()

        try:
            # Get or create sample users
            ivan = self.get_or_create_ivan_wong()
            ktl_employee = self.get_or_create_ktl_employee()

            # Get required data
            kil_company = Company.objects.filter(code='KI').first()
            ktl_company = Company.objects.filter(code='KT').first()

            if not kil_company or not ktl_company:
                self.stdout.write(self.style.ERROR(
                    '❌ Companies not found. Please run: python manage.py setup_krystal_companies'
                ))
                return

            # Get categories
            transport_cat = ExpenseCategory.objects.filter(code='transportation').first()
            keynote_cat = ExpenseCategory.objects.filter(code='keynote_speech').first()
            business_cat = ExpenseCategory.objects.filter(code='business_negotiation').first()

            if not all([transport_cat, keynote_cat]):
                self.stdout.write(self.style.ERROR(
                    '❌ Categories not found. Please run: python manage.py setup_expense_categories'
                ))
                return

            # Get currencies
            hkd_currency = Currency.objects.filter(code='HKD').first()
            cny_currency = Currency.objects.filter(code='CNY').first()

            if not all([hkd_currency, cny_currency]):
                self.stdout.write(self.style.ERROR(
                    '❌ Currencies not found. Please check currency setup.'
                ))
                return

            # Get or create exchange rates
            hkd_rate = self.get_or_create_exchange_rate(hkd_currency, Decimal('1.00'))
            cny_rate = self.get_or_create_exchange_rate(cny_currency, Decimal('1.08'))

            # Create Sample Claim 1: IAICC Event for Ivan Wong
            if ivan and kil_company:
                claim1 = self.create_iaicc_claim(
                    ivan, kil_company, transport_cat, keynote_cat,
                    hkd_currency, cny_currency, hkd_rate, cny_rate
                )
                if claim1:
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Created Claim 1: {claim1.claim_number} - IAICC Event (Ivan Wong)'
                    ))

            # Create Sample Claim 2: Business Trip for KTL Employee
            if ktl_employee and ktl_company and business_cat:
                claim2 = self.create_business_trip_claim(
                    ktl_employee, ktl_company, business_cat or transport_cat,
                    hkd_currency, hkd_rate
                )
                if claim2:
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Created Claim 2: {claim2.claim_number} - Business Trip (KTL Employee)'
                    ))

            self.stdout.write(self.style.SUCCESS('\n🎉 Sample claims created successfully!'))
            self.stdout.write(self.style.SUCCESS(
                '\nYou can view them at: http://localhost:8003/expense-claims/'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating sample claims: {e}'))
            import traceback
            traceback.print_exc()

    def clear_sample_claims(self):
        """Clear existing sample claims."""
        # Delete claims created by sample users
        sample_emails = [
            'ivan.wong@krystal.institute',
            'tech.employee@krystal.institute'
        ]

        for email in sample_emails:
            try:
                user = CompanyUser.objects.get(email=email)
                claims = ExpenseClaim.objects.filter(claimant=user)
                count = claims.count()
                claims.delete()
                if count > 0:
                    self.stdout.write(self.style.WARNING(
                        f'🗑️  Deleted {count} existing claims for {email}'
                    ))
            except CompanyUser.DoesNotExist:
                pass

    def get_or_create_ivan_wong(self):
        """Get or create Ivan Wong user."""
        try:
            ivan = CompanyUser.objects.get(email='ivan.wong@krystal.institute')
            self.stdout.write(f'📋 Found existing user: Ivan Wong')
            return ivan
        except CompanyUser.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                '⚠️  Ivan Wong not found. Using existing user or skipping...'
            ))
            # Try to find any user from KI company
            kil_company = Company.objects.filter(code='KI').first()
            if kil_company:
                # Try to find any user
                any_user = CompanyUser.objects.first()
                if any_user:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  Using {any_user.email} instead of Ivan Wong'
                    ))
                    return any_user
            return None

    def get_or_create_ktl_employee(self):
        """Get or create KTL employee user."""
        try:
            # Try to find any user
            users = CompanyUser.objects.exclude(email='ivan.wong@krystal.institute')
            if users.exists():
                user = users.first()
                self.stdout.write(f'📋 Found existing user for KTL: {user.email}')
                return user
            else:
                self.stdout.write(self.style.WARNING(
                    '⚠️  No additional users found for KTL claim'
                ))
                return None
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Error finding KTL employee: {e}'))
            return None

    def get_or_create_exchange_rate(self, currency, rate):
        """Get or create exchange rate for currency."""
        try:
            # Try to get today's rate
            exchange_rate = ExchangeRate.objects.filter(
                currency=currency,
                effective_date__date=timezone.now().date()
            ).first()

            if not exchange_rate:
                # Create new rate
                exchange_rate = ExchangeRate.objects.create(
                    currency=currency,
                    rate_to_base=rate,
                    effective_date=timezone.now(),
                    source='sample_data'
                )
                self.stdout.write(f'📈 Created exchange rate: 1 {currency.code} = {rate} HKD')

            return exchange_rate.rate_to_base

        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'⚠️  Error with exchange rate for {currency.code}: {e}, using default'
            ))
            return rate

    def create_iaicc_claim(self, ivan, company, transport_cat, keynote_cat,
                           hkd_currency, cny_currency, hkd_rate, cny_rate):
        """Create IAICC event expense claim for Ivan Wong."""
        try:
            # Create the expense claim
            claim = ExpenseClaim.objects.create(
                claimant=ivan,
                company=company,
                event_name='IAICC AI Conference 2024',
                period_from=timezone.now().date() - timedelta(days=7),
                period_to=timezone.now().date() - timedelta(days=1),
                status='draft'
            )

            # Add Expense 1: Taxi from SZ Bay Port to CUHKSRI
            ExpenseItem.objects.create(
                expense_claim=claim,
                item_number=1,
                expense_date=timezone.now().date() - timedelta(days=5),
                description='Taxi from SZ Bay Port to CUHKSRI',
                description_chinese='从深圳湾口岸到中大(深圳)的士费',
                category=transport_cat,
                original_amount=Decimal('85.00'),
                currency=cny_currency,
                exchange_rate=cny_rate,
                amount_hkd=Decimal('85.00') * cny_rate,
                has_receipt=True,
                location='Shenzhen to CUHK',
                participants='Total 2 persons included Jeff and Ivan',
                notes='Transportation to AI conference venue'
            )

            # Add Expense 2: Keynote speaker honorarium
            ExpenseItem.objects.create(
                expense_claim=claim,
                item_number=2,
                expense_date=timezone.now().date() - timedelta(days=3),
                description='Keynote speaker honorarium',
                description_chinese='主题演讲嘉宾费',
                category=keynote_cat,
                original_amount=Decimal('5000.00'),
                currency=hkd_currency,
                exchange_rate=hkd_rate,
                amount_hkd=Decimal('5000.00'),
                has_receipt=True,
                notes='Payment for keynote speech at IAICC conference'
            )

            # Update claim totals
            claim.update_totals()

            return claim

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating IAICC claim: {e}'))
            import traceback
            traceback.print_exc()
            return None

    def create_business_trip_claim(self, employee, company, category,
                                    hkd_currency, hkd_rate):
        """Create business trip expense claim."""
        try:
            # Create the expense claim
            claim = ExpenseClaim.objects.create(
                claimant=employee,
                company=company,
                event_name='Business Development Trip',
                period_from=timezone.now().date() - timedelta(days=14),
                period_to=timezone.now().date() - timedelta(days=10),
                status='draft'
            )

            # Add Expense: Business lunch with client
            ExpenseItem.objects.create(
                expense_claim=claim,
                item_number=1,
                expense_date=timezone.now().date() - timedelta(days=12),
                description='Business lunch with client',
                description_chinese='与客户商务午餐',
                category=category,
                original_amount=Decimal('350.00'),
                currency=hkd_currency,
                exchange_rate=hkd_rate,
                amount_hkd=Decimal('350.00'),
                has_receipt=True,
                notes='Client relationship building'
            )

            # Update claim totals
            claim.update_totals()

            return claim

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating business trip claim: {e}'))
            import traceback
            traceback.print_exc()
            return None
