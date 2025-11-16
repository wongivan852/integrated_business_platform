#!/usr/bin/env python3
"""
Script to remove timeline marker tasks from the database
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/home/user/Desktop/integrated_business_platform')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_platform.settings')
django.setup()

from project_management.models import Task

def cleanup_timeline_markers():
    """Remove all timeline marker tasks from the database"""

    # Find and delete tasks with timeline marker patterns
    patterns = [
        r'^W\d+$',  # W1, W2, W3, etc.
        r'^Start 2025$',
        r'^End 2025$',
        r'^timeline_',
        r'^TIMELINE_MARKER',
    ]

    total_deleted = 0

    for pattern in patterns:
        tasks = Task.objects.filter(title__iregex=pattern)
        count = tasks.count()
        if count > 0:
            print(f"Found {count} tasks matching pattern '{pattern}':")
            for task in tasks[:5]:  # Show first 5
                print(f"  - ID: {task.pk}, Title: '{task.title}', Project: {task.project.name if task.project else 'None'}")
            if count > 5:
                print(f"  ... and {count - 5} more")

            # Delete them
            tasks.delete()
            print(f"Deleted {count} tasks matching '{pattern}'")
            total_deleted += count

    # Also check for empty title tasks that might be boundary tasks
    empty_tasks = Task.objects.filter(title='')
    empty_count = empty_tasks.count()
    if empty_count > 0:
        print(f"Found {empty_count} tasks with empty titles")
        empty_tasks.delete()
        total_deleted += empty_count

    # Check for tasks with IDs 999998 or 999999
    boundary_ids = [999998, 999999]
    for task_id in boundary_ids:
        try:
            task = Task.objects.get(pk=task_id)
            print(f"Found boundary task with ID {task_id}: '{task.title}'")
            task.delete()
            total_deleted += 1
        except Task.DoesNotExist:
            pass

    print(f"\nTotal tasks deleted: {total_deleted}")

    # Show remaining task count
    remaining = Task.objects.count()
    print(f"Remaining tasks in database: {remaining}")

    return total_deleted

if __name__ == "__main__":
    print("=== Cleaning up timeline marker tasks ===")
    deleted = cleanup_timeline_markers()
    if deleted > 0:
        print("\n✓ Cleanup complete!")
    else:
        print("\n✓ No timeline marker tasks found - database is clean!")