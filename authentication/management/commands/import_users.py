"""
Django management command to import users from CSV file
"""

import csv
import sys
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from authentication.models import CompanyUser


class Command(BaseCommand):
    help = 'Import users from CSV file into the system'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file with user data'
        )
        parser.add_argument(
            '--default-password',
            type=str,
            default='Welcome123!',
            help='Default password for imported users (default: Welcome123!)'
        )
        parser.add_argument(
            '--default-region',
            type=str,
            default='HK',
            help='Default region for imported users (default: HK)'
        )
        parser.add_argument(
            '--default-department',
            type=str,
            default='General',
            help='Default department for imported users (default: General)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode without actually creating users'
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
        default_region = options['default_region']
        default_department = options['default_department']
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']
        yes_flag = options['yes']

        self.stdout.write(self.style.NOTICE(f'Reading CSV file: {csv_file}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY-RUN mode - no changes will be made'))

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Verify required columns
                required_columns = ['primary_email', 'first_name', 'last_name']
                if not all(col in reader.fieldnames for col in required_columns):
                    raise CommandError(
                        f'CSV file must have columns: {", ".join(required_columns)}\n'
                        f'Found columns: {", ".join(reader.fieldnames)}'
                    )

                users_to_create = []
                skipped_count = 0
                error_count = 0

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    email = row.get('primary_email', '').strip().lower()
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    company = row.get('company_primary', '').strip()

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

                    # Always use default department (company names are too long for 20 char limit)
                    department = default_department

                    # Generate employee_id (use email prefix or sequential number)
                    employee_id = f'EMP{row_num:04d}'

                    # Prepare user data
                    user_data = {
                        'email': email,
                        'username': email,  # Use email as username
                        'first_name': first_name,
                        'last_name': last_name,
                        'employee_id': employee_id,
                        'region': default_region,
                        'department': department,
                        'is_active': True,
                        'is_staff': False,
                        'is_superuser': False,
                        'password_change_required': True,  # Force password change on first login
                    }

                    users_to_create.append((user_data, default_password))

                    if len(users_to_create) % 50 == 0:
                        self.stdout.write(f'Processed {len(users_to_create)} valid users...')

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

                if dry_run:
                    self.stdout.write(self.style.SUCCESS('DRY-RUN completed successfully!'))
                    self.stdout.write('Run without --dry-run to actually import users.')
                    return

                # Confirm before proceeding
                if not dry_run and not yes_flag:
                    confirm = input(f'\nProceed with importing {len(users_to_create)} users? [y/N]: ')
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

                            if created_count % 50 == 0:
                                self.stdout.write(f'Created {created_count} users...')

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
