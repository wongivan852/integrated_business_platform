"""
Management command to create Employee profiles for users without one
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from leave_management.models import Employee

User = get_user_model()


class Command(BaseCommand):
    help = 'Create Employee profiles for users without one'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(employee__isnull=True)
        
        created_count = 0
        for user in users_without_profile:
            # Generate employee_id from username or email (max 20 chars)
            if user.username:
                employee_id = user.username[:20]
            elif user.email:
                employee_id = user.email.split('@')[0][:20]
            else:
                employee_id = f'EMP{user.id}'
            
            # Create Employee profile
            try:
                employee = Employee.objects.create(
                    user=user,
                    employee_id=employee_id,
                    department=getattr(user, 'department', 'General'),
                    position=getattr(user, 'position', 'Staff'),
                    company='Krystal Institute Ltd',
                    region='HK'
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created Employee profile for {user.username} (ID: {employee_id})')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to create profile for {user.username}: {str(e)}')
                )
        
        if created_count == 0:
            self.stdout.write(self.style.WARNING('No users without Employee profiles found'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Created {created_count} Employee profile(s)')
            )
