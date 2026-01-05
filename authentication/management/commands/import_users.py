"""
Import users from JSON export files into the database.

Usage:
    python manage.py import_users                    # Import from active_users_26.json
    python manage.py import_users --file=custom.json # Import from custom file
    python manage.py import_users --dry-run          # Preview without importing
"""

import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings


class Command(BaseCommand):
    help = 'Import users from JSON export file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='active_users_26.json',
            help='JSON file to import (default: active_users_26.json)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview import without making changes'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing users instead of skipping'
        )
        parser.add_argument(
            '--default-password',
            type=str,
            default='Krystal@2025',
            help='Default password for new users'
        )

    def handle(self, *args, **options):
        User = get_user_model()

        file_path = options['file']
        dry_run = options['dry_run']
        update_existing = options['update']
        default_password = options['default_password']

        # Find the file
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        # Load JSON
        with open(file_path, 'r') as f:
            users_data = json.load(f)

        self.stdout.write(f'\nImporting users from: {file_path}')
        self.stdout.write(f'Total users in file: {len(users_data)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN MODE ===\n'))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for user_data in users_data:
            username = user_data.get('username')
            email = user_data.get('email', username)

            # Check if user exists
            existing_user = User.objects.filter(username=username).first()

            if existing_user:
                if update_existing:
                    if not dry_run:
                        existing_user.email = email
                        existing_user.first_name = user_data.get('first_name', '')
                        existing_user.last_name = user_data.get('last_name', '')
                        existing_user.is_active = user_data.get('is_active', True)
                        existing_user.is_staff = user_data.get('is_staff', False)

                        if hasattr(existing_user, 'employee_id'):
                            existing_user.employee_id = user_data.get('employee_id', '')
                        if hasattr(existing_user, 'region'):
                            existing_user.region = user_data.get('region', 'HK')
                        if hasattr(existing_user, 'department'):
                            existing_user.department = user_data.get('department', '')

                        existing_user.save()

                    self.stdout.write(f'  Updated: {username}')
                    updated_count += 1
                else:
                    self.stdout.write(f'  Skipped (exists): {username}')
                    skipped_count += 1
            else:
                if not dry_run:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=default_password,
                        first_name=user_data.get('first_name', ''),
                        last_name=user_data.get('last_name', ''),
                        is_active=user_data.get('is_active', True),
                        is_staff=user_data.get('is_staff', False),
                        is_superuser=user_data.get('is_superuser', False),
                    )

                    if hasattr(user, 'employee_id'):
                        user.employee_id = user_data.get('employee_id', '')
                    if hasattr(user, 'region'):
                        user.region = user_data.get('region', 'HK')
                    if hasattr(user, 'department'):
                        user.department = user_data.get('department', '')

                    user.save()

                self.stdout.write(self.style.SUCCESS(f'  Created: {username}'))
                created_count += 1

        self.stdout.write('\n' + '=' * 40)
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write('=' * 40)

        if dry_run:
            self.stdout.write(self.style.WARNING('\nThis was a dry run. No changes were made.'))
            self.stdout.write('Run without --dry-run to actually import users.')
        else:
            self.stdout.write(self.style.SUCCESS('\nImport complete!'))
            if created_count > 0:
                self.stdout.write(f'\nDefault password for new users: {default_password}')
                self.stdout.write('Users should change their password on first login.')
