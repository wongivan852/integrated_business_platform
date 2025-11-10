"""
Management command to initialize leave balances for all employees
"""
from django.core.management.base import BaseCommand
from leave_management.models import Employee, LeaveType, LeaveBalance
from django.utils import timezone


class Command(BaseCommand):
    help = 'Initialize leave balances for all employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Year for leave balances (default: current year)'
        )

    def handle(self, *args, **options):
        year = options['year']
        employees = Employee.objects.all()
        leave_types = LeaveType.objects.all()
        
        if not leave_types.exists():
            self.stdout.write(
                self.style.ERROR('No leave types found! Run "python manage.py create_leave_types" first.')
            )
            return
        
        if not employees.exists():
            self.stdout.write(
                self.style.ERROR('No employees found! Run "python manage.py create_employee_profiles" first.')
            )
            return
        
        created_count = 0
        skipped_count = 0
        
        for employee in employees:
            for leave_type in leave_types:
                balance, created = LeaveBalance.objects.get_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    defaults={
                        'opening_balance': 0.00,
                        'carried_forward': 0.00,
                        'current_year_entitlement': leave_type.max_days_per_year,
                        'taken': 0.00,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {employee.user.username}: {leave_type.name} = {leave_type.max_days_per_year} days'
                        )
                    )
                else:
                    skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Created {created_count} leave balance(s) for {employees.count()} employee(s)'
            )
        )
        
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'↻ Skipped {skipped_count} existing balance(s)')
            )
