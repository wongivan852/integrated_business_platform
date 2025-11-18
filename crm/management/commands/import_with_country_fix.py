from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.exceptions import ValidationError
from crm.models import Customer
import csv
import os


class Command(BaseCommand):
    help = 'Import customers with proper country code mapping'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # Country mapping
        COUNTRY_MAPPING = {
            'hong kong sar': 'HK',
            'hong kong': 'HK', 
            'china': 'CN',
            'south korea': 'KR',
            'nigeria': 'NG',
            'united kingdom': 'GB',
            'uk': 'GB',
            'other (please specify in notes)': 'OTHER',
            'india': 'IN',
            'philippines': 'PH',
            'france': 'FR',
            'japan': 'JP',
            'thailand': 'TH',
            'malaysia': 'MY',
            'taiwan': 'TW',
            'united states': 'US',
            'usa': 'US',
            'peru': 'PE',
            'switzerland': 'CH',
            'italy': 'IT',
            'south africa': 'ZA',
            'netherlands': 'NL',
            'australia': 'AU',
            'canada': 'CA',
            'singapore': 'SG',
            'germany': 'DE',
            'brazil': 'BR',
            'mexico': 'MX',
        }

        def map_country(country_name):
            if not country_name or not country_name.strip():
                return ''
            country_key = country_name.strip().lower()
            mapped = COUNTRY_MAPPING.get(country_key, country_name.strip())
            # If it's already a code, return it
            if len(mapped) == 2 and mapped.isupper():
                return mapped
            return COUNTRY_MAPPING.get(country_key, '')

        def clean_field(value):
            if not value:
                return ''
            return str(value).strip()

        def clean_url_field(value):
            if not value or not value.strip():
                return ''
            url = str(value).strip()
            if url and not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return url

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return

        self.stdout.write('Starting customer import with country mapping...')
        
        success_count = 0
        error_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=1):
                try:
                    with transaction.atomic():
                        # Extract and clean data
                        first_name = clean_field(row.get('first_name', ''))
                        last_name = clean_field(row.get('last_name', ''))
                        email_primary = clean_field(row.get('email_primary', ''))
                        
                        # Map country
                        country_raw = clean_field(row.get('country_region', ''))
                        country_region = map_country(country_raw)
                        
                        # Create customer
                        customer = Customer(
                            first_name=first_name,
                            last_name=last_name,
                            email_primary=email_primary,
                            email_secondary=clean_field(row.get('email_secondary', '')),
                            phone_primary=clean_field(row.get('phone_primary', '')),
                            phone_secondary=clean_field(row.get('phone_secondary', '')),
                            company_primary=clean_field(row.get('company_name', '')),
                            position_primary=clean_field(row.get('job_title', '')),
                            profession=clean_field(row.get('industry', '')),
                            customer_type=clean_field(row.get('customer_type', 'corporate')),
                            status=clean_field(row.get('lead_status', 'prospect')),
                            source=clean_field(row.get('source', 'import')),
                            country_region=country_region,
                            address_primary=clean_field(row.get('address_line1', '')),
                            address_secondary=clean_field(row.get('address_line2', '')),
                            city=clean_field(row.get('city', '')),
                            state_province=clean_field(row.get('state_province', '')),
                            postal_code=clean_field(row.get('postal_code', '')),
                            company_website=clean_url_field(row.get('website', '')),
                            internal_notes=clean_field(row.get('notes', '')),
                            youtube_handle=clean_field(row.get('youtube_handle', '')),
                            instagram_handle=clean_field(row.get('instagram_handle', '')),
                            twitter_handle=clean_field(row.get('twitter_handle', '')),
                            facebook_profile=clean_url_field(row.get('facebook_page', '')),
                            linkedin_profile=clean_url_field(row.get('linkedin_profile', '')),
                        )
                        
                        customer.full_clean()
                        customer.save()
                        
                        success_count += 1
                        if success_count % 100 == 0:
                            self.stdout.write(f'Imported {success_count} customers...')
                            
                except ValidationError as e:
                    error_count += 1
                    if error_count <= 5:
                        self.stdout.write(self.style.WARNING(f'Row {row_num} validation error: {e}'))
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:
                        self.stdout.write(self.style.ERROR(f'Row {row_num} error: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Import completed!'))
        self.stdout.write(f'Successfully imported: {success_count}')
        self.stdout.write(f'Errors: {error_count}')
        self.stdout.write(f'Total processed: {success_count + error_count}')
