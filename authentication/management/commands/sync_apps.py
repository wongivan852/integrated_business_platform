"""
Sync application configurations to the dashboard.

Usage:
    python manage.py sync_apps
"""

from django.core.management.base import BaseCommand
from authentication.models import ApplicationConfig


class Command(BaseCommand):
    help = 'Sync application configurations for dashboard display'

    def handle(self, *args, **options):
        self.stdout.write('Syncing application configurations...\n')

        # Define all platform applications
        apps = [
            {
                'name': 'expense_claims',
                'display_name': 'Expense Claims',
                'description': 'Submit and manage expense claims',
                'url': '/expense-claims/',
                'icon': 'fas fa-receipt',
                'color': '#dc3545',
                'order': 10,
            },
            {
                'name': 'leave_management',
                'display_name': 'Leave Management',
                'description': 'Apply for leave and manage leave requests',
                'url': '/leave/',
                'icon': 'fas fa-calendar-alt',
                'color': '#28a745',
                'order': 20,
            },
            {
                'name': 'crm',
                'display_name': 'CRM System',
                'description': 'Customer Relationship Management - manage customers, courses, and communications',
                'url': '/crm/',
                'icon': 'fas fa-users-cog',
                'color': '#6f42c1',
                'order': 30,
            },
            {
                'name': 'asset_management',
                'display_name': 'Asset Management',
                'description': 'Track and manage company assets',
                'url': '/assets/',
                'icon': 'fas fa-boxes',
                'color': '#fd7e14',
                'order': 40,
            },
            {
                'name': 'project_management',
                'display_name': 'Project Management',
                'description': 'Manage projects with Gantt charts and Kanban boards',
                'url': '/project-management/',
                'icon': 'fas fa-project-diagram',
                'color': '#20c997',
                'order': 50,
            },
            {
                'name': 'event_management',
                'display_name': 'Event Management',
                'description': 'Manage events, visits, and installations',
                'url': '/event-management/',
                'icon': 'fas fa-calendar-check',
                'color': '#17a2b8',
                'order': 60,
            },
            {
                'name': 'quotations',
                'display_name': 'Quotations',
                'description': 'Create and manage cost quotations',
                'url': '/quotations/',
                'icon': 'fas fa-calculator',
                'color': '#007bff',
                'order': 70,
            },
            {
                'name': 'attendance',
                'display_name': 'Staff Attendance',
                'description': 'Staff daily attendance tracking',
                'url': '/attendance/',
                'icon': 'fas fa-clock',
                'color': '#6610f2',
                'order': 80,
            },
            {
                'name': 'qr_attendance',
                'display_name': 'QR Attendance',
                'description': 'QR code-based event attendance',
                'url': '/qr-attendance/',
                'icon': 'fas fa-qrcode',
                'color': '#e83e8c',
                'order': 90,
            },
        ]

        created = 0
        updated = 0

        for app_data in apps:
            app, was_created = ApplicationConfig.objects.update_or_create(
                name=app_data['name'],
                defaults={
                    'display_name': app_data['display_name'],
                    'description': app_data['description'],
                    'url': app_data['url'],
                    'icon': app_data['icon'],
                    'color': app_data['color'],
                    'order': app_data['order'],
                    'is_active': True,
                    'requires_sso': True,
                }
            )

            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {app.display_name}'))
            else:
                updated += 1
                self.stdout.write(f'  Updated: {app.display_name}')

        self.stdout.write(f'\nCreated: {created}, Updated: {updated}')
        self.stdout.write(self.style.SUCCESS('Sync complete!'))
