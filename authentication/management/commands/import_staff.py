"""
Django management command to import staff from staff_list.csv
"""

import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from authentication.models import CompanyUser


class Command(BaseCommand):
    help = 'Import staff from staff_list.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file with staff data'
        )
        parser.add_argument(
            '--default-password',
            type=str,
            default='Welcome123!',
            help='Default password for imported staff (default: Welcome123!)'
        )
        parser.add_argument(
            '--default-department',
            type=str,
            default='General',
            help='Default department for staff (default: General)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip users that already exist (by email)'
        )
        parser.add_argument(
            '--yes', '-y',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        default_password = options['default_password']
        default_department = options['default_department']
        skip_existing = options['skip_existing']
        yes_flag = options['yes']

        self.stdout.write(self.style.NOTICE(f'Reading CSV file: {csv_file}'))

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Verify required columns
                required_columns = ['email', 'first_name', 'last_name', 'username', 'region']
                if not all(col in reader.fieldnames for col in required_columns):
                    raise CommandError(
                        f'CSV file must have columns: {", ".join(required_columns)}\n'
                        f'Found columns: {", ".join(reader.fieldnames)}'
                    )

                users_to_create = []
                skipped_count = 0
                error_count = 0

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    # Clean data (remove newlines from emails)
                    email = row.get('email', '').strip().replace('\n', '').replace('\r', '').lower()
                    username = row.get('username', '').strip()
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    region = row.get('region', 'HK').strip().upper()
                    is_staff_str = row.get('is_staff', 'FALSE').strip().upper()
                    is_staff = is_staff_str in ['TRUE', '1', 'YES', 'Y']

                    # Validate data
                    if not email:
                        self.stdout.write(
                            self.style.WARNING(f'Row {row_num}: Skipping - no email address')
                        )
                        skipped_count += 1
                        continue

                    if not first_name and not last_name:
                        self.stdout.write(
                            self.style.WARNING(f'Row {row_num}: Skipping - no name provided for {email}')
                        )
                        skipped_count += 1
                        continue

                    # Check if user already exists
                    if CompanyUser.objects.filter(email=email).exists():
                        if skip_existing:
                            self.stdout.write(
                                self.style.WARNING(f'Row {row_num}: Skipping existing user: {email}')
                            )
                            skipped_count += 1
                            continue
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'Row {row_num}: User already exists: {email}')
                            )
                            error_count += 1
                            continue

                    # Generate employee_id from username or email
                    employee_id = username.upper() if username else email.split('@')[0].upper()
                    # Limit to 20 chars
                    if len(employee_id) > 20:
                        employee_id = employee_id[:20]

                    # Prepare user data
                    user_data = {
                        'email': email,
                        'username': email,  # Use email as username for uniqueness
                        'first_name': first_name,
                        'last_name': last_name,
                        'employee_id': employee_id,
                        'region': region if region in ['HK', 'CN', 'TW', 'JP', 'SG'] else 'HK',
                        'department': default_department,
                        'is_active': True,
                        'is_staff': is_staff,
                        'is_superuser': False,
                        'password_change_required': True,  # Force password change on first login
                    }

                    users_to_create.append((user_data, default_password))

                # Summary before import
                self.stdout.write(self.style.NOTICE('\n' + '='*60))
                self.stdout.write(self.style.NOTICE('Import Summary:'))
                self.stdout.write(f'  Valid users to import: {len(users_to_create)}')
                self.stdout.write(f'  Skipped: {skipped_count}')
                self.stdout.write(f'  Errors: {error_count}')
                self.stdout.write(self.style.NOTICE('='*60 + '\n'))

                if not users_to_create:
                    self.stdout.write(self.style.WARNING('No users to import!'))
                    return

                # Confirm before proceeding
                if not yes_flag:
                    confirm = input(f'\nProceed with importing {len(users_to_create)} staff? [y/N]: ')
                    if confirm.lower() != 'y':
                        self.stdout.write(self.style.WARNING('Import cancelled by user'))
                        return

                # Import users (each in its own transaction to avoid rollback issues)
                self.stdout.write(self.style.NOTICE('Starting import...'))
                created_count = 0
                failed_count = 0

                for user_data, password in users_to_create:
                    try:
                        with transaction.atomic():
                            user = CompanyUser.objects.create_user(
                                password=password,
                                **user_data
                            )
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created: {user.email} ({user.first_name} {user.last_name})')
                            )

                    except Exception as e:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'Error creating user {user_data["email"]}: {str(e)}')
                        )

                # Final summary
                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('Import Complete!'))
                self.stdout.write(self.style.SUCCESS(f'Successfully created: {created_count} users'))
                if failed_count > 0:
                    self.stdout.write(self.style.WARNING(f'Failed to create: {failed_count} users'))
                self.stdout.write(self.style.SUCCESS(f'Default password: {default_password}'))
                self.stdout.write(self.style.SUCCESS('='*60))

                self.stdout.write(self.style.NOTICE(
                    '\nNote: All imported users have been set with the default password.'
                ))
                self.stdout.write(self.style.NOTICE(
                    'Users should change their passwords on first login.'
                ))

        except FileNotFoundError:
            raise CommandError(f'CSV file not found: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error importing users: {str(e)}')
