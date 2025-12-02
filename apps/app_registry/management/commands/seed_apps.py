"""
Management command to seed initial application configurations.

Usage:
    python manage.py seed_apps
    python manage.py seed_apps --clear  # Clear existing apps first
"""

from django.core.management.base import BaseCommand
from apps.app_registry.models import ApplicationConfig, Department


class Command(BaseCommand):
    help = 'Seed initial application configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing apps before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing apps...')
            ApplicationConfig.objects.all().delete()
            Department.objects.all().delete()

        self.stdout.write('Seeding application configurations...')

        # Define applications
        apps = [
            {
                'code': 'dashboard',
                'name': 'Dashboard',
                'description': 'Main dashboard and app portal',
                'icon': 'fas fa-home',
                'color': '#6c757d',
                'category': 'system',
                'url_path': '/dashboard/',
                'status': 'production',
                'requires_permission': False,
                'permission_key': '',
                'display_order': 0,
            },
            {
                'code': 'expense_claims',
                'name': 'Expense Claims',
                'description': 'Submit and manage expense claims',
                'icon': 'fas fa-receipt',
                'color': '#dc3545',
                'category': 'finance',
                'url_path': '/expense-claims/',
                'status': 'production',
                'requires_permission': True,
                'permission_key': 'expense_system',
                'display_order': 10,
            },
            {
                'code': 'leave_management',
                'name': 'Leave Management',
                'description': 'Apply for leave and manage leave requests',
                'icon': 'fas fa-calendar-alt',
                'color': '#28a745',
                'category': 'hr',
                'url_path': '/leave/',
                'status': 'production',
                'requires_permission': True,
                'permission_key': 'leave_system',
                'display_order': 20,
            },
            {
                'code': 'asset_management',
                'name': 'Asset Management',
                'description': 'Track and manage company assets',
                'icon': 'fas fa-boxes',
                'color': '#fd7e14',
                'category': 'operations',
                'url_path': '/assets/',
                'status': 'production',
                'requires_permission': True,
                'permission_key': 'asset_management',
                'display_order': 30,
            },
            {
                'code': 'crm',
                'name': 'CRM',
                'description': 'Customer Relationship Management',
                'icon': 'fas fa-users',
                'color': '#6f42c1',
                'category': 'sales',
                'url_path': '/crm/',
                'status': 'production',
                'requires_permission': True,
                'permission_key': 'crm_system',
                'display_order': 40,
            },
            {
                'code': 'quotations',
                'name': 'Quotations',
                'description': 'Create and manage cost quotations',
                'icon': 'fas fa-calculator',
                'color': '#007bff',
                'category': 'sales',
                'url_path': '/quotations/',
                'status': 'uat',
                'requires_permission': True,
                'permission_key': 'quotation_system',
                'display_order': 50,
            },
            {
                'code': 'event_management',
                'name': 'Event Management',
                'description': 'Manage events, visits, and installations',
                'icon': 'fas fa-calendar-check',
                'color': '#17a2b8',
                'category': 'operations',
                'url_path': '/event-management/',
                'status': 'production',
                'requires_permission': True,
                'permission_key': 'event_management',
                'display_order': 60,
            },
            {
                'code': 'project_management',
                'name': 'Project Management',
                'description': 'Manage projects with Gantt charts and Kanban boards',
                'icon': 'fas fa-project-diagram',
                'color': '#20c997',
                'category': 'operations',
                'url_path': '/project-management/',
                'status': 'developing',
                'requires_permission': True,
                'permission_key': 'project_management',
                'display_order': 70,
            },
            {
                'code': 'attendance',
                'name': 'Attendance',
                'description': 'Staff daily attendance tracking',
                'icon': 'fas fa-clock',
                'color': '#6610f2',
                'category': 'hr',
                'url_path': '/attendance/',
                'status': 'production',
                'requires_permission': True,
                'permission_key': 'attendance_system',
                'display_order': 80,
            },
            {
                'code': 'qr_attendance',
                'name': 'QR Attendance',
                'description': 'QR code-based event attendance',
                'icon': 'fas fa-qrcode',
                'color': '#e83e8c',
                'category': 'operations',
                'url_path': '/qr-attendance/',
                'status': 'production',
                'requires_permission': True,
                'permission_key': 'qr_attendance',
                'display_order': 90,
            },
            {
                'code': 'stripe_integration',
                'name': 'Stripe Dashboard',
                'description': 'Payment processing and financial reports',
                'icon': 'fab fa-stripe-s',
                'color': '#635bff',
                'category': 'finance',
                'url_path': '/stripe/',
                'status': 'uat',
                'requires_permission': True,
                'permission_key': 'stripe_dashboard',
                'display_order': 100,
            },
            {
                'code': 'admin_panel',
                'name': 'Admin Panel',
                'description': 'User and app management',
                'icon': 'fas fa-cog',
                'color': '#343a40',
                'category': 'admin',
                'url_path': '/admin-panel/',
                'status': 'production',
                'requires_permission': True,
                'permission_key': 'admin_panel',
                'display_order': 200,
            },
        ]

        created_count = 0
        updated_count = 0

        for app_data in apps:
            app, created = ApplicationConfig.objects.update_or_create(
                code=app_data['code'],
                defaults=app_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  Created: {app.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  Updated: {app.name}')
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Done! Created {created_count} apps, updated {updated_count} apps.'
            )
        )

        # Create default departments
        self.stdout.write('')
        self.stdout.write('Seeding departments...')

        departments = [
            {'code': 'HR', 'name': 'Human Resources'},
            {'code': 'Finance', 'name': 'Finance'},
            {'code': 'IT', 'name': 'Information Technology'},
            {'code': 'Operations', 'name': 'Operations'},
            {'code': 'Sales', 'name': 'Sales'},
            {'code': 'Management', 'name': 'Management'},
            {'code': 'Admin', 'name': 'Administration'},
        ]

        for dept_data in departments:
            dept, created = Department.objects.update_or_create(
                code=dept_data['code'],
                defaults={'name': dept_data['name']}
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  Created department: {dept.name}')
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
