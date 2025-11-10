"""
Management command to create default leave types
"""
from django.core.management.base import BaseCommand
from leave_management.models import LeaveType


class Command(BaseCommand):
    help = 'Create default leave types for the leave management system'

    def handle(self, *args, **options):
        leave_types_data = [
            {
                'name': 'Annual Leave',
                'description': 'Paid vacation days for employees',
                'max_days_per_year': 14,
                'requires_approval': True,
            },
            {
                'name': 'Sick Leave',
                'description': 'Leave for illness or medical appointments',
                'max_days_per_year': 10,
                'requires_approval': True,
            },
            {
                'name': 'Emergency Leave',
                'description': 'Leave for unexpected emergencies',
                'max_days_per_year': 3,
                'requires_approval': True,
            },
            {
                'name': 'Maternity Leave',
                'description': 'Maternity leave for expecting mothers',
                'max_days_per_year': 90,
                'requires_approval': True,
            },
            {
                'name': 'Paternity Leave',
                'description': 'Paternity leave for new fathers',
                'max_days_per_year': 5,
                'requires_approval': True,
            },
            {
                'name': 'Compassionate Leave',
                'description': 'Leave for family emergencies or bereavement',
                'max_days_per_year': 5,
                'requires_approval': True,
            },
            {
                'name': 'Marriage Leave',
                'description': 'Leave for getting married',
                'max_days_per_year': 3,
                'requires_approval': True,
            },
            {
                'name': 'Unpaid Leave',
                'description': 'Leave without pay',
                'max_days_per_year': 30,
                'requires_approval': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in leave_types_data:
            leave_type, created = LeaveType.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {leave_type.name} ({leave_type.max_days_per_year} days/year)')
                )
            else:
                # Update existing leave type
                for key, value in data.items():
                    setattr(leave_type, key, value)
                leave_type.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {leave_type.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Created {created_count} leave type(s), Updated {updated_count} leave type(s)')
        )
        
        total = LeaveType.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'✓ Total leave types in system: {total}')
        )
