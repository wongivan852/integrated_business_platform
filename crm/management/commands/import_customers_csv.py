# management/commands/import_customers_csv.py
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from crm.models import Customer
from django.db import transaction
import uuid

class Command(BaseCommand):
    help = 'Import customers from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to CSV file to import'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['full', 'simple'],
            default='full',
            help='CSV format: full (comprehensive) or simple (basic)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        csv_format = options['format']
        dry_run = options['dry_run']
        
        if not os.path.exists(file_path):
            raise CommandError(f'File does not exist: {file_path}')
        
        self.stdout.write(f'Starting import from: {file_path}')
        self.stdout.write(f'Format: {csv_format}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        if csv_format == 'full':
            self.import_full_format(file_path, dry_run)
        else:
            self.import_simple_format(file_path, dry_run)

    def import_full_format(self, file_path, dry_run):
        """Import from comprehensive CSV export format"""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Map CSV fields to model fields
                        customer_data = {
                            'first_name': row.get('First Name', '').strip(),
                            'middle_name': row.get('Middle Name', '').strip(),
                            'last_name': row.get('Last Name', '').strip(),
                            'preferred_name': row.get('Preferred Name', '').strip(),
                            'other_names': row.get('Other Names', '').strip(),
                            'email_primary': row.get('Primary Email', '').strip(),
                            'email_secondary': row.get('Secondary Email', '').strip(),
                            'phone_primary': row.get('Primary Phone', '').strip(),
                            'phone_primary_country_code': row.get('Primary Phone Country Code', '').strip(),
                            'phone_secondary': row.get('Secondary Phone', '').strip(),
                            'phone_secondary_country_code': row.get('Secondary Phone Country Code', '').strip(),
                            'whatsapp_number': row.get('WhatsApp Number', '').strip(),
                            'whatsapp_country_code': row.get('WhatsApp Country Code', '').strip(),
                            'fax': row.get('Fax', '').strip(),
                            'fax_country_code': row.get('Fax Country Code', '').strip(),
                            'wechat_id': row.get('WeChat ID', '').strip(),
                            'company_primary': row.get('Primary Company', '').strip(),
                            'position_primary': row.get('Primary Position', '').strip(),
                            'company_secondary': row.get('Secondary Company', '').strip(),
                            'position_secondary': row.get('Secondary Position', '').strip(),
                            'company_website': row.get('Company Website', '').strip(),
                            'address_primary': row.get('Primary Address', '').strip(),
                            'address_secondary': row.get('Secondary Address', '').strip(),
                            'country_region': self.map_country_code(row.get('Country/Region', '').strip()),
                            'linkedin_profile': row.get('LinkedIn Profile', '').strip(),
                            'facebook_profile': row.get('Facebook Profile', '').strip(),
                            'twitter_handle': row.get('Twitter Handle', '').strip(),
                            'instagram_handle': row.get('Instagram Handle', '').strip(),
                            'customer_type': self.map_customer_type(row.get('Customer Type', 'individual').strip()),
                            'status': self.map_status(row.get('Status', 'prospect').strip()),
                            'preferred_learning_format': row.get('Preferred Learning Format', '').strip(),
                            'preferred_communication_method': self.map_communication_method(row.get('Preferred Communication Method', 'email').strip()),
                            'interests': row.get('Interests', '').strip(),
                        }
                        
                        # Clean empty strings to None for optional fields
                        for key, value in customer_data.items():
                            if value == '':
                                customer_data[key] = None
                        
                        # Check if customer already exists by email or ID
                        existing_customer = None
                        if customer_data['email_primary']:
                            existing_customer = Customer.objects.filter(
                                email_primary=customer_data['email_primary']
                            ).first()
                        
                        # Try to get by ID if provided and no email match
                        if not existing_customer and row.get('ID'):
                            try:
                                existing_customer = Customer.objects.filter(
                                    id=row['ID']
                                ).first()
                            except:
                                pass
                        
                        if existing_customer:
                            if dry_run:
                                self.stdout.write(f'Row {row_num}: Would skip existing customer {customer_data["email_primary"]}')
                            skipped_count += 1
                            continue
                        
                        if dry_run:
                            self.stdout.write(f'Row {row_num}: Would create customer {customer_data["first_name"]} {customer_data["last_name"]} ({customer_data["email_primary"]})')
                        else:
                            # Create the customer
                            customer = Customer(**customer_data)
                            customer.full_clean()  # Validate
                            customer.save()
                            
                            self.stdout.write(f'Row {row_num}: Created customer {customer.first_name} {customer.last_name} ({customer.email_primary})')
                        
                        imported_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Error - {str(e)}')
                        )
                        # Continue with next row
                        continue
                
                if dry_run:
                    # Don't commit in dry run mode
                    transaction.set_rollback(True)
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete: {imported_count} imported, '
                f'{skipped_count} skipped, {error_count} errors'
            )
        )

    def import_simple_format(self, file_path, dry_run):
        """Import from simple CSV format (master_eDM_list)"""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Parse name
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    
                    # If last_name is duplicated in the "last_name" field, clean it
                    if last_name and first_name and last_name in first_name:
                        # Extract just the first name part
                        parts = first_name.split()
                        if len(parts) > 1:
                            first_name = parts[0]
                    
                    # Handle missing names
                    if not first_name and not last_name:
                        self.stdout.write(f'Row {row_num}: Skipping - no name provided')
                        skipped_count += 1
                        continue
                    
                    # If only one name provided, put it in first_name
                    if not first_name:
                        first_name = last_name
                        last_name = ''
                    
                    customer_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'email_primary': row.get('primary_email', '').strip(),
                        'company_primary': row.get('company_primary', '').strip(),
                        'customer_type': 'corporate',  # Default based on data
                        'status': 'prospect',  # Default status
                        'preferred_communication_method': 'email',
                        'referral_source': row.get('referral_source', '').strip(),
                    }
                    
                    # Clean empty strings
                    for key, value in customer_data.items():
                        if value == '':
                            customer_data[key] = None
                    
                    # Skip if no email
                    if not customer_data['email_primary']:
                        self.stdout.write(f'Row {row_num}: Skipping - no email address')
                        skipped_count += 1
                        continue
                    
                    # Check if customer already exists
                    existing_customer = Customer.objects.filter(
                        email_primary=customer_data['email_primary']
                    ).first()
                    
                    if existing_customer:
                        if dry_run:
                            self.stdout.write(f'Row {row_num}: Would skip existing customer {customer_data["email_primary"]}')
                        skipped_count += 1
                        continue
                    
                    if dry_run:
                        self.stdout.write(f'Row {row_num}: Would create customer {customer_data["first_name"]} {customer_data["last_name"]} ({customer_data["email_primary"]})')
                    else:
                        # Create the customer (each in its own transaction)
                        try:
                            with transaction.atomic():
                                customer = Customer(**customer_data)
                                customer.full_clean()  # Validate
                                customer.save()
                                
                                self.stdout.write(f'Row {row_num}: Created customer {customer.first_name} {customer.last_name} ({customer.email_primary})')
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
                f'Import complete: {imported_count} imported, '
                f'{skipped_count} skipped, {error_count} errors'
            )
        )

    def map_customer_type(self, csv_value):
        """Map CSV customer type to model choices"""
        mapping = {
            'corporare client': 'corporate',  # Note: typo in original data
            'corporate client': 'corporate',
            'individual learner': 'individual',
            'student': 'student',
            'instructor': 'instructor',
            'youtuber': 'youtuber',
        }
        return mapping.get(csv_value.lower(), 'individual')

    def map_status(self, csv_value):
        """Map CSV status to model choices"""
        mapping = {
            'prospect': 'prospect',
            'active': 'active',
            'inactive': 'inactive',
            'alumni': 'alumni',
        }
        return mapping.get(csv_value.lower(), 'prospect')

    def map_communication_method(self, csv_value):
        """Map CSV communication method to model choices"""
        mapping = {
            'email': 'email',
            'phone': 'phone',
            'whatsapp': 'whatsapp',
            'wechat': 'wechat',
            'sms': 'sms',
        }
        return mapping.get(csv_value.lower(), 'email')

    def map_country_code(self, csv_value):
        """Map country names to ISO codes"""
        # Basic mapping - can be expanded
        mapping = {
            'china': 'CN',
            'united states': 'US',
            'usa': 'US',
            'uk': 'GB',
            'united kingdom': 'GB',
            'canada': 'CA',
            'australia': 'AU',
            'singapore': 'SG',
            'hong kong': 'HK',
            'malaysia': 'MY',
            'thailand': 'TH',
        }
        return mapping.get(csv_value.lower(), '')
