"""
Add all staff members from staff_list.csv to Project Management app.
"""
import csv
from django.core.management.base import BaseCommand
from authentication.models import CompanyUser


class Command(BaseCommand):
    help = 'Add all staff members from staff_list.csv to Project Management app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='/home/user/Desktop/attendance-system/staff_list.csv',
            help='Path to staff_list.csv file'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']

        self.stdout.write(self.style.WARNING(f'\nReading staff list from: {csv_path}'))

        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                staff_emails = []
                for row in reader:
                    email = row.get('email', '').strip()
                    if email:
                        staff_emails.append(email)

                self.stdout.write(self.style.SUCCESS(f'Found {len(staff_emails)} staff members in CSV\n'))

                # Process each staff member
                updated_count = 0
                already_had_access = 0
                not_found_count = 0

                for email in staff_emails:
                    try:
                        user = CompanyUser.objects.get(email=email)

                        # Get current apps_access
                        apps_access = user.apps_access or []

                        # Check if project_management is already in the list
                        if 'project_management' in apps_access:
                            self.stdout.write(
                                self.style.WARNING(f'  ✓ {email}: Already has project_management access')
                            )
                            already_had_access += 1
                        else:
                            # Add project_management to apps_access
                            apps_access.append('project_management')
                            user.apps_access = apps_access
                            user.save(update_fields=['apps_access'])

                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ {email}: Added project_management access')
                            )
                            updated_count += 1

                    except CompanyUser.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ {email}: User not found in database')
                        )
                        not_found_count += 1

                # Summary
                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('Summary:'))
                self.stdout.write(self.style.SUCCESS(f'  Total staff in CSV: {len(staff_emails)}'))
                self.stdout.write(self.style.SUCCESS(f'  Updated with access: {updated_count}'))
                self.stdout.write(self.style.WARNING(f'  Already had access: {already_had_access}'))
                if not_found_count > 0:
                    self.stdout.write(self.style.ERROR(f'  Not found in database: {not_found_count}'))
                self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'\nError: Could not find file at {csv_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nError: {str(e)}')
            )
