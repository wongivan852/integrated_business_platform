# management/commands/import_youtube_creators.py
import csv
import os
import re
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from crm.models import Customer
from django.db import transaction

class Command(BaseCommand):
    help = 'Import YouTube creators from CSV - handles entries with only names and YouTube handles'

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
        
        self.stdout.write(f'Starting YouTube creator import from: {file_path}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        self.import_youtube_creators(file_path, dry_run)

    def import_youtube_creators(self, file_path, dry_run):
        """Import YouTube creators from CSV, detecting various formats"""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Look for potential YouTube creator indicators
                    youtube_indicators = self.detect_youtube_creator(row)
                    
                    if not youtube_indicators:
                        continue  # Skip non-YouTube entries
                    
                    # Extract YouTube handle/channel name
                    youtube_handle = self.extract_youtube_handle(row, youtube_indicators)
                    
                    if not youtube_handle:
                        continue
                    
                    # Build customer data
                    customer_data = self.build_youtube_customer_data(row, youtube_handle)
                    
                    # Check if customer already exists
                    existing_customer = self.check_existing_customer(customer_data)
                    
                    if existing_customer:
                        if dry_run:
                            self.stdout.write(f'Row {row_num}: Would skip existing customer @{youtube_handle}')
                        skipped_count += 1
                        continue
                    
                    if dry_run:
                        self.stdout.write(f'Row {row_num}: Would create YouTube creator @{youtube_handle} - {customer_data["first_name"]} {customer_data["last_name"]}')
                    else:
                        # Create the customer
                        try:
                            with transaction.atomic():
                                customer = Customer(**customer_data)
                                customer.full_clean()  # Validate
                                customer.save()
                                
                                self.stdout.write(f'Row {row_num}: Created YouTube creator @{customer.youtube_handle} - {customer.first_name} {customer.last_name}')
                        except Exception as save_error:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'Row {row_num}: Error saving - {str(save_error)}')
                            )
                            continue
                    
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
                f'YouTube creator import complete: {imported_count} imported, '
                f'{skipped_count} skipped, {error_count} errors'
            )
        )

    def detect_youtube_creator(self, row):
        """Detect if this row represents a YouTube creator"""
        indicators = []
        
        # Check company field for YouTube channel-like names
        company = (row.get('company_primary', '') or row.get('company', '')).strip()
        if company:
            # Look for channel-like patterns
            if any(keyword in company.lower() for keyword in [
                'channel', 'tv', 'media', 'studio', 'productions', 'creative',
                'content', 'digital', 'video', 'creator', 'vlog'
            ]):
                indicators.append(('company_channel', company))
            
            # Look for @handle patterns
            if company.startswith('@') or re.match(r'^[a-zA-Z0-9_.-]+$', company):
                if len(company) > 3 and not '@' in company[1:]:  # Not an email
                    indicators.append(('handle_pattern', company))
        
        # Check for missing email but has name (common for YouTube entries)
        email = (row.get('primary_email', '') or row.get('email', '')).strip()
        first_name = (row.get('first_name', '') or row.get('first', '')).strip()
        last_name = (row.get('last_name', '') or row.get('last', '')).strip()
        
        if (not email or len(email) < 5) and (first_name or last_name):
            indicators.append(('no_email_has_name', True))
        
        # Check if company name looks like a YouTube handle
        if company and not '.' in company and not ' ' in company and len(company) > 3:
            indicators.append(('possible_handle', company))
        
        return indicators

    def extract_youtube_handle(self, row, indicators):
        """Extract YouTube handle from the row"""
        # Try different sources for the handle
        for indicator_type, value in indicators:
            if indicator_type in ['handle_pattern', 'possible_handle']:
                handle = str(value).strip().lstrip('@')
                if len(handle) > 2 and handle.replace('_', '').replace('-', '').isalnum():
                    return handle
            
            elif indicator_type == 'company_channel':
                # Convert company name to handle format
                handle = re.sub(r'[^a-zA-Z0-9_]', '', str(value).replace(' ', ''))
                if len(handle) > 3:
                    return handle
        
        # Fallback: try to construct from name
        first_name = (row.get('first_name', '') or row.get('first', '')).strip()
        last_name = (row.get('last_name', '') or row.get('last', '')).strip()
        
        if first_name or last_name:
            handle = f"{first_name}{last_name}".replace(' ', '')
            if len(handle) > 2:
                return handle
        
        return None

    def build_youtube_customer_data(self, row, youtube_handle):
        """Build customer data for YouTube creator"""
        first_name = (row.get('first_name', '') or row.get('first', '')).strip()
        last_name = (row.get('last_name', '') or row.get('last', '')).strip()
        email = (row.get('primary_email', '') or row.get('email', '')).strip()
        company = (row.get('company_primary', '') or row.get('company', '')).strip()
        
        # If no proper names, generate from handle
        if not first_name and not last_name:
            # Try to split CamelCase or underscore handle
            name_parts = re.findall(r'[A-Z][a-z]*|[a-z]+', youtube_handle)
            if name_parts:
                first_name = name_parts[0]
                if len(name_parts) > 1:
                    last_name = ' '.join(name_parts[1:])
                else:
                    last_name = 'Creator'
            else:
                first_name = youtube_handle.title()
                last_name = 'Creator'
        elif not first_name:
            first_name = youtube_handle.title()
        elif not last_name:
            last_name = 'Creator'
        
        # Generate YouTube URL
        youtube_url = f"https://youtube.com/@{youtube_handle}"
        
        customer_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email_primary': email if email and len(email) > 5 else None,
            'customer_type': 'youtuber',
            'status': 'prospect',
            'youtube_handle': youtube_handle,
            'youtube_channel_url': youtube_url,
            'company_primary': company if company and company != youtube_handle else f"{first_name} {last_name} Channel",
            'position_primary': 'Content Creator',
            'preferred_communication_method': 'email' if email else 'whatsapp',
            'referral_source': row.get('referral_source', 'csv_import'),
            'interests': 'Content Creation, Video Production',
        }
        
        return customer_data

    def check_existing_customer(self, customer_data):
        """Check if customer already exists"""
        # Check by YouTube handle first
        if customer_data.get('youtube_handle'):
            existing = Customer.objects.filter(
                youtube_handle__iexact=customer_data['youtube_handle']
            ).first()
            if existing:
                return existing
        
        # Check by email if available
        if customer_data.get('email_primary'):
            existing = Customer.objects.filter(
                email_primary=customer_data['email_primary']
            ).first()
            if existing:
                return existing
        
        # Check by name combination
        existing = Customer.objects.filter(
            first_name__iexact=customer_data['first_name'],
            last_name__iexact=customer_data['last_name'],
            customer_type='youtuber'
        ).first()
        
        return existing
