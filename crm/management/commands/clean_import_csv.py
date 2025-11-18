# management/commands/clean_import_csv.py
import csv
import os
import re
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from crm.models import Customer
from django.db import transaction

class Command(BaseCommand):
    help = 'Import customers from CSV with data cleaning and validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to CSV file to import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        
        if not os.path.exists(file_path):
            raise CommandError(f'File does not exist: {file_path}')
        
        self.stdout.write(f'Starting clean import from: {file_path}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        self.import_customers_clean(file_path, dry_run)

    def import_customers_clean(self, file_path, dry_run):
        """Import customers with data cleaning and better error handling"""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Clean and validate the row data
                    cleaned_data = self.clean_row_data(row)
                    
                    if not cleaned_data:
                        skipped_count += 1
                        if dry_run:
                            self.stdout.write(f'Row {row_num}: Would skip (insufficient data)')
                        continue
                    
                    # Check for existing customer
                    existing_customer = self.check_existing_customer(cleaned_data)
                    
                    if existing_customer:
                        skipped_count += 1
                        if dry_run:
                            self.stdout.write(f'Row {row_num}: Would skip existing customer: {cleaned_data["first_name"]} {cleaned_data["last_name"]}')
                        continue
                    
                    if dry_run:
                        self.stdout.write(f'Row {row_num}: Would create {cleaned_data["first_name"]} {cleaned_data["last_name"]} - {cleaned_data["email_primary"]}')
                    else:
                        # Create the customer
                        try:
                            customer = Customer(**cleaned_data)
                            customer.full_clean()  # Validate
                            customer.save()
                            
                            imported_count += 1
                            if imported_count <= 10 or imported_count % 50 == 0:  # Show first 10 and every 50th
                                self.stdout.write(f'Row {row_num}: Created {customer.first_name} {customer.last_name} - {customer.email_primary}')
                        except Exception as save_error:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'Row {row_num}: Error saving - {str(save_error)}')
                            )
                            continue
                    
                    if not dry_run:
                        imported_count += 1
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Row {row_num}: Error processing - {str(e)}')
                    )
                    continue
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Clean import complete: {imported_count} imported, '
                f'{skipped_count} skipped, {error_count} errors'
            )
        )

    def clean_row_data(self, row):
        """Clean and validate row data before creating customer"""
        # Get basic fields
        company = (row.get('company_primary', '') or row.get('company', '')).strip()
        email = (row.get('primary_email', '') or row.get('email', '')).strip()
        first_name_raw = (row.get('first_name', '') or row.get('first', '')).strip()
        last_name_raw = (row.get('last_name', '') or row.get('last', '')).strip()
        referral_source = row.get('referral_source', 'csv_import').strip()
        
        # Clean email data - handle multi-email entries
        email = self.clean_email(email)
        
        # Basic validation
        if not email:
            return None  # Skip rows without valid email
        
        if not (first_name_raw or last_name_raw):
            return None  # Skip rows without name data
        
        # Clean name data - handle cases where full name is in first_name field
        first_name, last_name = self.clean_names(first_name_raw, last_name_raw)
        
        if not first_name:
            first_name = "Unknown"
        if not last_name:
            last_name = "Contact"
        
        # Determine customer type based on data patterns
        customer_type = self.determine_customer_type(row, company, first_name, last_name)
        
        # Build clean customer data
        cleaned_data = {
            'first_name': first_name[:50],  # Ensure field length limits
            'last_name': last_name[:50],
            'email_primary': email.lower(),
            'company_primary': company[:100] if company else f"{first_name} {last_name} Company",
            'customer_type': customer_type,
            'status': 'prospect',
            'preferred_communication_method': 'email',
            'referral_source': referral_source if referral_source else 'csv_import',
        }
        
        # Add YouTube-specific data if detected
        if customer_type == 'youtuber':
            youtube_handle = self.extract_youtube_handle(row, company, first_name, last_name)
            if youtube_handle:
                cleaned_data['youtube_handle'] = youtube_handle
                cleaned_data['youtube_channel_url'] = f"https://youtube.com/@{youtube_handle}"
                cleaned_data['position_primary'] = 'Content Creator'
                cleaned_data['interests'] = 'Content Creation, Video Production'
        
        return cleaned_data

    def clean_names(self, first_name_raw, last_name_raw):
        """Clean and split name data properly"""
        # Handle case where full name is in first_name field
        if first_name_raw and (' ' in first_name_raw) and (not last_name_raw or last_name_raw in first_name_raw):
            # Split the first name
            name_parts = first_name_raw.strip().split()
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else last_name_raw
        else:
            first_name = first_name_raw
            last_name = last_name_raw
        
        # Clean individual names
        first_name = re.sub(r'[^a-zA-Z\s\'-]', '', first_name).strip() if first_name else ""
        last_name = re.sub(r'[^a-zA-Z\s\'-]', '', last_name).strip() if last_name else ""
        
        # Handle cases where names are duplicated
        if first_name and last_name and first_name.lower() in last_name.lower():
            # Remove duplicate names
            if last_name.lower().startswith(first_name.lower()):
                last_name = last_name[len(first_name):].strip()
            elif last_name.lower().endswith(first_name.lower()):
                last_name = last_name[:-len(first_name)].strip()
        
        return first_name, last_name

    def determine_customer_type(self, row, company, first_name, last_name):
        """Determine customer type based on available data"""
        # Check for YouTube/content creator indicators
        youtube_indicators = [
            'channel', 'tv', 'media', 'studio', 'productions', 'creative',
            'content', 'digital', 'video', 'creator', 'vlog', 'youtuber'
        ]
        
        if company:
            company_lower = company.lower()
            if any(indicator in company_lower for indicator in youtube_indicators):
                return 'youtuber'
        
        # Default to individual customer
        return 'individual'

    def clean_email(self, email_raw):
        """Clean and validate email, handling multi-email entries"""
        if not email_raw:
            return None
        
        # Handle multiple emails - take the first valid one
        emails = re.split(r'[\s,;]+', email_raw.strip())
        
        for email in emails:
            email = email.strip()
            if email and '@' in email and len(email) >= 5:
                # Basic email validation
                if re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                    return email
        
        return None

    def extract_youtube_handle(self, row, company, first_name, last_name):
        """Extract or generate YouTube handle for content creators"""
        # Try to use company name as handle if it looks like one
        if company and not ' ' in company and len(company) > 3:
            handle = re.sub(r'[^a-zA-Z0-9_]', '', company)
            if len(handle) > 2:
                return handle
        
        # Generate from names
        handle = f"{first_name}{last_name}".replace(' ', '')
        handle = re.sub(r'[^a-zA-Z0-9_]', '', handle)
        return handle if len(handle) > 2 else None

    def check_existing_customer(self, customer_data):
        """Check if customer already exists"""
        # Check by email first
        if customer_data.get('email_primary'):
            existing = Customer.objects.filter(
                email_primary=customer_data['email_primary']
            ).first()
            if existing:
                return existing
        
        # Check by name combination
        existing = Customer.objects.filter(
            first_name__iexact=customer_data['first_name'],
            last_name__iexact=customer_data['last_name']
        ).first()
        
        return existing
