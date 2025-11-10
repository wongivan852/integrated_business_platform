"""
Management command to set up Leave Management System in ApplicationConfig
"""
from django.core.management.base import BaseCommand
from authentication.models import ApplicationConfig


class Command(BaseCommand):
    help = 'Setup Leave Management System application configuration'

    def handle(self, *args, **options):
        leave_app, created = ApplicationConfig.objects.get_or_create(
            name='leave_system',
            defaults={
                'display_name': 'Leave Management System',
                'url': '/leave/',
                'icon': 'fa-calendar-alt',
                'color': 'success',
                'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'description': 'Manage employee leave requests, approvals, and leave balances',
                'is_active': True,
            }
        )
        
        if not created:
            # Update existing configuration
            leave_app.display_name = 'Leave Management System'
            leave_app.url = '/leave/'
            leave_app.icon = 'fa-calendar-alt'
            leave_app.color = 'success'
            leave_app.gradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            leave_app.description = 'Manage employee leave requests, approvals, and leave balances'
            leave_app.is_active = True
            leave_app.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated Leave Management System configuration'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Created Leave Management System configuration'))
        
        self.stdout.write(self.style.SUCCESS(f'  URL: {leave_app.url}'))
        self.stdout.write(self.style.SUCCESS(f'  Display Name: {leave_app.display_name}'))
        self.stdout.write(self.style.SUCCESS(f'  Active: {leave_app.is_active}'))
