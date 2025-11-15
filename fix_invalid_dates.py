#!/usr/bin/env python
"""
Fix tasks with invalid date values in the database
"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_platform.settings')
django.setup()

from project_management.models import Task

def fix_invalid_dates():
    """Find and fix tasks with invalid start_date or end_date values"""

    print("=== Checking for tasks with invalid dates ===\n")

    fixed_count = 0
    total_tasks = Task.objects.count()

    print(f"Checking {total_tasks} tasks...\n")

    for task in Task.objects.all():
        needs_save = False

        # Check start_date
        if task.start_date is None:
            print(f"✗ Task {task.pk} ({task.task_code}): NULL start_date - setting to today")
            task.start_date = date.today()
            needs_save = True
        elif not isinstance(task.start_date, date):
            print(f"✗ Task {task.pk} ({task.task_code}): Invalid start_date type: {type(task.start_date)} - {task.start_date}")
            task.start_date = date.today()
            needs_save = True

        # Check end_date
        if task.end_date is not None and not isinstance(task.end_date, date):
            print(f"✗ Task {task.pk} ({task.task_code}): Invalid end_date type: {type(task.end_date)} - {task.end_date}")
            task.end_date = None
            needs_save = True

        # Check duration
        if task.duration is None or task.duration <= 0:
            print(f"✗ Task {task.pk} ({task.task_code}): Invalid duration: {task.duration} - setting to 1")
            task.duration = 1
            needs_save = True

        # Calculate end_date if missing
        if task.start_date and not task.end_date:
            from datetime import timedelta
            task.end_date = task.start_date + timedelta(days=task.duration - 1)
            print(f"ℹ Task {task.pk} ({task.task_code}): Calculated end_date from start_date + duration")
            needs_save = True

        if needs_save:
            task.save()
            fixed_count += 1

    print(f"\n=== Summary ===")
    print(f"Total tasks checked: {total_tasks}")
    print(f"Tasks fixed: {fixed_count}")

    if fixed_count > 0:
        print("\n✅ Database has been fixed!")
    else:
        print("\n✅ No issues found - database is clean!")

if __name__ == '__main__':
    fix_invalid_dates()
